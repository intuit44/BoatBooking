import asyncio
import json
import logging
import subprocess
from datetime import datetime
import os
import requests
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    asyncio.run(promover_correcciones_pendientes())


def _load_pending_fixes() -> list[dict]:
    path = Path("scripts/pending_fixes.json")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON inválido en pending_fixes.json: {e}")
        _enviar_alerta_slack(
            {"id": "sistema", "target": "pending_fixes.json"},
            motivo=f"Archivo corrupto: {e}"
        )
        return []
    except Exception as e:
        logging.error(f"❌ Error leyendo pending_fixes.json: {e}")
        return []


def _save_fixes(fixes: list[dict]):
    """Guarda la lista de correcciones actualizada."""
    with open('scripts/pending_fixes.json', 'w', encoding='utf-8') as f:
        json.dump(fixes, f, indent=4)


def _log_semantic_event(event: dict):
    """Registra un evento semántico usando memory_service."""
    try:
        from services.memory_service import memory_service
        if memory_service:
            event_type = event.pop('tipo', 'semantic')
            memory_service.log_event(event_type, event)
        else:
            # Fallback a archivo local si memory_service no está disponible
            with open('scripts/semantic_log.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
    except ImportError:
        # Fallback a archivo local si no se puede importar memory_service
        try:
            with open('scripts/semantic_log.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logging.error(f"Error al registrar evento semántico: {e}")
    except Exception as e:
        logging.error(f"Error al registrar evento semántico: {e}")


def _evaluate_auto_promotion(fix: dict) -> dict:
    """Evalúa si una corrección puede ser promovida automáticamente."""
    # Lógica de evaluación (ejemplo simple)
    if fix.get("prioridad", 0) >= 8 and fix.get("validado_por_test", False):
        return {"promocionable": True}
    return {"promocionable": False, "razon": "Prioridad baja o no validado por tests"}


def _execute_fix(fix: dict) -> dict:
    """Ejecuta una corrección aprobada con logging, validación y trazabilidad."""
    resultado = {
        "id_correccion": fix.get("id"),
        "timestamp": datetime.now().isoformat(),
        "ejecutado": False,
        "validado": False,
        "errores": []
    }

    try:
        logging.info(f"Ejecutando fix {fix.get('id')} en {fix.get('target')}")
        target_path = Path("/home/site/wwwroot") / fix.get("target", "")

        # 1. Validar existencia del target
        if not target_path.exists():
            error_msg = f"Target {fix.get('target')} no encontrado"
            resultado["errores"].append(error_msg)
            fix["estado"] = "fallido"
            resultado["error"] = error_msg
        else:
            propuesta = fix.get("propuesta", "")
            if not propuesta:
                fix["estado"] = "omitido"
                resultado["errores"].append(
                    "No hay acción definida para este fix")
                resultado["error"] = "No hay acción definida para este fix"
                # Guardar estado omitido y loguear
                fixes = _load_pending_fixes()
                for f in fixes:
                    if f.get("id") == fix.get("id"):
                        f.update(fix)
                _save_fixes(fixes)
                _log_semantic_event({
                    "tipo": "correccion_omitida",
                    "fix_id": fix.get("id"),
                    "target": fix.get("target"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "mensaje": "Fix omitido: no hay acción definida"
                })
                _enviar_alerta_slack(
                    fix,
                    motivo="Fix omitido: no hay acción definida"
                )
                return resultado

            # 2. Aplicar la propuesta (simulación básica)
            if "chmod" in propuesta:
                os.system(propuesta)
            elif "shebang" in propuesta:
                contenido = target_path.read_text(encoding="utf-8")
                if not contenido.startswith("#!"):
                    target_path.write_text(
                        propuesta + "\n" + contenido, encoding="utf-8")
            else:
                # Si la propuesta no es reconocida, omitir
                fix["estado"] = "omitido"
                resultado["errores"].append(
                    "No hay acción definida para este fix")
                resultado["error"] = "No hay acción definida para este fix"
                fixes = _load_pending_fixes()
                for f in fixes:
                    if f.get("id") == fix.get("id"):
                        f.update(fix)
                _save_fixes(fixes)
                _log_semantic_event({
                    "tipo": "correccion_omitida",
                    "fix_id": fix.get("id"),
                    "target": fix.get("target"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "mensaje": "Fix omitido: no hay acción definida"
                })
                _enviar_alerta_slack(
                    fix,
                    motivo="Fix omitido: no hay acción definida"
                )
                return resultado

            # 3. Actualizar estado y resultado
            fix["estado"] = "aplicado"
            resultado["ejecutado"] = True

            # 4. Validación post-aplicación
            validacion = _validate_fix(fix)
            resultado["validado"] = validacion.get("validado", False)
            if not resultado["validado"]:
                resultado["errores"].append(
                    validacion.get("error", "Validación fallida"))
                fix["estado"] = "fallido_validacion"
                resultado["error"] = validacion.get(
                    "error", "Validación fallida")

        # 5. Guardar en pending_fixes.json
        fixes = _load_pending_fixes()
        for f in fixes:
            if f.get("id") == fix.get("id"):
                f.update(fix)
        _save_fixes(fixes)

        # 6. Log semántico
        if fix.get("estado") == "aplicado" and resultado["validado"]:
            tipo_log = "correccion_aplicada"
            mensaje_log = "Fix aplicado y validado con éxito"
        elif fix.get("estado") == "aplicado" and not resultado["validado"]:
            tipo_log = "correccion_fallida"
            mensaje_log = "Fix aplicado pero falló validación"
        elif fix.get("estado") == "omitido":
            tipo_log = "correccion_omitida"
            mensaje_log = "Fix omitido: no hay acción definida"
        else:
            tipo_log = "correccion_fallida"
            mensaje_log = resultado.get("error", "Fix fallido")

        _log_semantic_event({
            "tipo": tipo_log,
            "fix_id": fix.get("id"),
            "target": fix.get("target"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mensaje": mensaje_log
        })

        # 7. Notificar Slack
        _enviar_alerta_slack(
            fix,
            motivo=mensaje_log
        )

    except Exception as e:
        logging.error(f"Error ejecutando fix {fix.get('id')}: {e}")
        resultado["errores"].append(str(e))
        fix["estado"] = "fallido"
        # Actualizar y guardar estado fallido
        fixes = _load_pending_fixes()
        for f in fixes:
            if f.get("id") == fix.get("id"):
                f.update(fix)
        _save_fixes(fixes)
        _log_semantic_event({
            "tipo": "correccion_fallida",
            "fix_id": fix.get("id"),
            "target": fix.get("target"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mensaje": f"Fix fallido: {e}"
        })
        _enviar_alerta_slack(fix, motivo=f"Fix fallido: {e}")

    return resultado


def _validate_fix(fix: dict) -> dict:
    """
    Validación granular post-aplicación del fix.
    Retorna {"validado": True/False, "error": "..."}
    """
    # Ejemplo simple: validar que el archivo existe y no está vacío
    target_path = Path("/home/site/wwwroot") / fix.get("target", "")
    if not target_path.exists():
        return {"validado": False, "error": "Target no encontrado tras aplicar fix"}
    try:
        contenido = target_path.read_text(encoding="utf-8")
        if not contenido.strip():
            return {"validado": False, "error": "Archivo vacío tras aplicar fix"}
    except Exception as e:
        return {"validado": False, "error": f"Error leyendo archivo: {e}"}
    return {"validado": True}


async def _trigger_deploy(fix: dict):
    """Dispara el script de despliegue si la corrección es crítica."""
    if fix.get("tipo") in ["seguridad", "error_critico"] and fix.get("prioridad", 0) >= 9:
        logging.info(
            f"Disparando despliegue automático debido a la corrección crítica: {fix['id']}")
        cmd = "powershell.exe -File ./fix_functionapp_final.ps1"

        try:
            # Usamos asyncio.create_subprocess_shell para no bloquear
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()

            resultado = "exitoso" if proc.returncode == 0 else "fallido"
            if stdout:
                logging.info(f'[stdout]\n{stdout.decode()}')
            if stderr:
                logging.error(f'[stderr]\n{stderr.decode()}')

        except Exception as e:
            logging.error(f"Fallo al ejecutar el script de despliegue: {e}")
            resultado = "fallido"

        _log_semantic_event({
            "tipo": "deploy_automatico",
            "fecha": datetime.now().isoformat(),
            "origen": "auto_promoter",
            "trigger": f"fix_{fix['id']}",
            "resultado": resultado
        })


def _enviar_alerta_slack(fix: dict, motivo: str):
    mensaje = {
        "text": f"⚠️ *Fix pendiente de revisión humana*\n"
        f"*ID:* {fix.get('id')}\n"
        f"*Acción:* {fix.get('accion')}\n"
        f"*Target:* {fix.get('target')}\n"
        f"*Prioridad:* {fix.get('prioridad')}\n"
        f"*Motivo:* {motivo}\n"
        f"👉 Revisión: https://copiloto-semantico-func-us2.azurewebsites.net/api/revisar-correcciones"
    }
    try:
        webhook = os.environ.get("SLACK_WEBHOOK_URL")
        if webhook:
            requests.post(webhook, json=mensaje)
        else:
            logging.warning("SLACK_WEBHOOK_URL no definido en configuración.")
    except Exception as e:
        logging.error(f"Fallo al notificar a Slack: {e}")


async def promover_correcciones_pendientes():
    """Proceso automatizado para revisar y promover correcciones pendientes."""
    all_fixes = _load_pending_fixes()
    pending_fixes = [fix for fix in all_fixes if fix.get(
        "estado") == "pendiente"]

    if not pending_fixes:
        logging.info("No hay correcciones pendientes para promover.")
        return {}

    promoted_ids = []
    failed_details = []

    for fix in pending_fixes:
        evaluacion = _evaluate_auto_promotion(fix)

        if evaluacion.get("promocionable"):
            logging.info(
                f"Promoviendo corrección {fix['id']}: {fix['descripcion']}")

            resultado_ejecucion = _execute_fix(fix)

            if resultado_ejecucion.get("validado"):
                promoted_ids.append(fix["id"])

                # Si es crítico, disparar despliegue
                await _trigger_deploy(fix)
            else:
                error_razon = resultado_ejecucion.get(
                    "error", "Validación fallida")
                failed_details.append({"id": fix["id"], "razon": error_razon})
                fix["estado"] = "fallido_promocion"
                fix["error"] = error_razon
                _enviar_alerta_slack(
                    fix, motivo=f"Fallo durante ejecución: {error_razon}")
        else:
            logging.info(
                f"La corrección {fix['id']} no es promocionable automáticamente: {evaluacion.get('razon')}")
            if fix.get("prioridad", 0) >= 8:
                _enviar_alerta_slack(
                    fix, motivo="No cumple criterios para promoción automática")

    _save_fixes(all_fixes)

    reporte = {
        "timestamp": datetime.now().isoformat(),
        "total_pendientes_revisadas": len(pending_fixes),
        "promovidos_count": len(promoted_ids),
        "fallidos_count": len(failed_details),
        "detalles_promovidos": promoted_ids,
        "detalles_fallidos": failed_details
    }

    _log_semantic_event({
        "tipo": "promocion_batch",
        "fecha": datetime.now().isoformat(),
        "origen": "auto_promoter",
        "reporte": reporte
    })

    return reporte

if __name__ == '__main__':
    main()
