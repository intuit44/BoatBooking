# -*- coding: utf-8 -*-
"""
Memory Route Wrapper - Envoltura automática para Azure Functions
Aplica lectura y escritura de memoria semántica sin modificar los endpoints originales.
"""
import os
import logging
import azure.functions as func
import json
import time
from typing import Callable
from datetime import datetime
from azure.storage.queue import QueueClient


def recuperar_contexto_conversacional(session_id: str, endpoint_actual: str) -> str:
    """
    Recupera el contexto conversacional desde la última invocación de endpoint.
    Retorna el bloque de conversación entre la última acción y esta.
    """
    try:
        from services.memory_service import memory_service

        # Obtener historial de la sesión
        interacciones = memory_service.get_session_history(
            session_id, limit=50)

        if not interacciones:
            return ""

        # Buscar la última invocación de endpoint (excluyendo context_snapshot)
        contexto_acumulado = []

        for interaccion in interacciones:
            source = interaccion.get("data", {}).get("source", "")

            # Si encontramos otra invocación de endpoint, detenemos
            if source != "context_snapshot" and source != "guardar_memoria":
                break

            # Acumular texto semántico
            texto = interaccion.get("texto_semantico", "")
            if texto and len(texto) > 20:
                contexto_acumulado.append(texto)

        # Retornar contexto concatenado
        if contexto_acumulado:
            # Orden cronológico
            return " | ".join(reversed(contexto_acumulado))

        return ""

    except Exception as e:
        logging.warning(f"⚠️ Error recuperando contexto: {e}")
        return ""


def memory_route(app: func.FunctionApp) -> Callable:
    """Fábrica que envuelve app.route para aplicar memoria automáticamente."""
    original_route = app.route

    def route_with_memory(*args, **kwargs) -> Callable:
        def decorator(func_ref: Callable) -> Callable:
            try:
                route_path = kwargs.get("route", "")
                source_name = route_path.strip(
                    "/").replace("-", "_") or func_ref.__name__

                def wrapper(req: func.HttpRequest) -> func.HttpResponse:
                    """Lectura y escritura de memoria automática."""
                    print(
                        f"\n>>> WRAPPER EJECUTANDOSE para: {source_name} <<<\n", flush=True)
                    logging.warning(
                        f"🚨 Wrapper ACTIVADO en endpoint: {source_name}")
                    from services.memory_service import memory_service

                    # 0️⃣ CAPTURA COMPLETA DE ENTRADA DEL USUARIO
                    try:
                        body = req.get_json() if req.method in [
                            "POST", "PUT", "PATCH"] else {}
                        user_message = body.get("mensaje") or body.get(
                            "query") or body.get("prompt")

                        if user_message and len(user_message.strip()) > 3:
                            session_id = req.headers.get(
                                "Session-ID") or "universal_session"
                            agent_id = req.headers.get(
                                "Agent-ID") or "foundry_user"

                            # Crear evento completo
                            evento = {
                                "id": f"{session_id}_user_input_{int(datetime.utcnow().timestamp())}",
                                "session_id": session_id,
                                "agent_id": agent_id,
                                "endpoint": route_path or "input-ui",
                                "event_type": "user_input",
                                "texto_semantico": user_message.strip(),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "exito": True,
                                "tipo": "user_input",
                                "data": {"origen": "foundry_ui", "tipo": "user_input"}
                            }

                            # Guardar en Cosmos + AI Search (flujo completo automático)
                            ok_cosmos = memory_service._log_cosmos(evento)
                            if ok_cosmos:
                                logging.info(
                                    f"✅ Guardado e indexado: {evento['id']} ({len(user_message)} chars)")
                            else:
                                logging.warning(
                                    "⚠️ No se pudo guardar el input del usuario.")
                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando input del usuario: {e}")

                    # 1️⃣ CONSULTAR MEMORIA COMPLETA: Cosmos DB + Conversación Rica
                    memoria_previa = {}
                    try:
                        from cosmos_memory_direct import consultar_memoria_cosmos_directo

                        # Obtener session_id y agent_id
                        session_id = req.headers.get(
                            "Session-ID") or req.params.get("session_id") or "global"
                        agent_id = req.headers.get(
                            "Agent-ID") or req.params.get("agent_id") or "unknown_agent"

                        # 🔥 CONSULTA COMPLETA: Recupera TODA la conversación rica desde Cosmos DB
                        memoria_previa = consultar_memoria_cosmos_directo(req)

                        if memoria_previa and memoria_previa.get("tiene_historial"):
                            total = memoria_previa.get(
                                "total_interacciones", 0)
                            logging.info(
                                f"🧠 [{source_name}] Memoria COMPLETA: {total} interacciones, sesión={session_id}, agente={agent_id}")
                            logging.info(
                                f"📝 Resumen: {memoria_previa.get('resumen_conversacion', '')[:200]}...")
                        else:
                            memoria_previa = {
                                "tiene_historial": False, "endpoint": route_path, "session_id": session_id}
                            logging.info(
                                f"🧠 [{source_name}] Sin memoria previa para sesión {session_id}")

                        setattr(req, "_memoria_contexto", memoria_previa)
                    except Exception as e:
                        logging.warning(
                            f"⚠️ [{source_name}] Error consultando memoria completa: {e}")
                        import traceback
                        logging.warning(traceback.format_exc())
                        # Fallback: intentar con memory_service local
                        try:
                            session_id = req.headers.get(
                                "Session-ID") or "global"
                            historial = memory_service.get_session_history(
                                session_id, limit=100)
                            memoria_previa = {
                                "tiene_historial": len(historial) > 0,
                                "interacciones_recientes": historial,
                                "total_interacciones": len(historial),
                                "session_id": session_id
                            }
                            setattr(req, "_memoria_contexto", memoria_previa)
                            logging.info(
                                f"🧠 [{source_name}] Fallback local: {len(historial)} interacciones")
                        except:
                            setattr(req, "_memoria_contexto", {
                                    "tiene_historial": False})

                    # 1.5️⃣ BÚSQUEDA VECTORIAL EN AI SEARCH POR ENDPOINT
                    docs_vectoriales = []
                    try:
                        from endpoints_search_memory import buscar_memoria_endpoint

                        # Buscar por endpoint + contenido del request
                        query_busqueda = f"{route_path}"
                        try:
                            body = req.get_json() or {}
                            if body.get("mensaje"):
                                query_busqueda += f" {body['mensaje']}"
                            elif body.get("query"):
                                query_busqueda += f" {body['query']}"
                        except:
                            pass

                        memoria_payload = {
                            "query": query_busqueda,
                            "top": 20  # Más resultados
                        }

                        resultado_vectorial = buscar_memoria_endpoint(
                            memoria_payload)

                        if resultado_vectorial.get("exito") and resultado_vectorial.get("documentos"):
                            docs_vectoriales = resultado_vectorial["documentos"]
                            logging.info(
                                f"🔍 [{source_name}] AI Search: {len(docs_vectoriales)} docs vectoriales para endpoint {route_path}")

                            # Inyectar en memoria_previa
                            if memoria_previa:
                                memoria_previa["docs_vectoriales"] = docs_vectoriales
                                memoria_previa["fuente_datos"] = "Endpoint+AISearch"
                    except Exception as e:
                        logging.warning(
                            f"⚠️ [{source_name}] Error en búsqueda vectorial: {e}")

                    # 2️⃣ EJECUTAR ENDPOINT ORIGINAL
                    try:
                        response = func_ref(req)
                        if response is None:
                            logging.error(
                                f"❌ [{source_name}] Endpoint devolvió None - esto no debería ocurrir")
                            return func.HttpResponse(
                                json.dumps(
                                    {"ok": False, "error": "Endpoint devolvió None"}, ensure_ascii=False),
                                mimetype="application/json",
                                status_code=500
                            )
                    except Exception as endpoint_error:
                        logging.error(
                            f"❌ [{source_name}] Excepción en endpoint: {endpoint_error}")
                        import traceback
                        logging.error(f"Traceback: {traceback.format_exc()}")
                        return func.HttpResponse(
                            json.dumps({
                                "ok": False,
                                "error": f"Error en endpoint: {str(endpoint_error)}",
                                "tipo_error": type(endpoint_error).__name__
                            }, ensure_ascii=False),
                            mimetype="application/json",
                            status_code=500
                        )

                    # 3️⃣ INYECTAR METADATA SIN PERDER CONTENIDO
                    try:
                        if isinstance(response, func.HttpResponse) and response.get_body():
                            body = response.get_body()
                            response_data = json.loads(body.decode("utf-8"))

                            if isinstance(response_data, dict):
                                # Inyectar metadata SIN tocar campos principales
                                if "metadata" not in response_data:
                                    response_data["metadata"] = {}

                                response_data["metadata"]["wrapper_aplicado"] = True

                                if memoria_previa.get("tiene_historial"):
                                    response_data["metadata"]["memoria_aplicada"] = True
                                    response_data["metadata"]["interacciones_previas"] = memoria_previa["total_interacciones"]
                                    response_data["metadata"]["docs_vectoriales"] = len(
                                        memoria_previa.get("docs_vectoriales", []))
                                    logging.info(
                                        f"🧠 [{source_name}] Metadata inyectada: {memoria_previa['total_interacciones']} interacciones")

                                # Recrear HttpResponse preservando TODO
                                new_body = json.dumps(
                                    response_data, ensure_ascii=False)
                                response = func.HttpResponse(
                                    new_body,
                                    status_code=response.status_code,
                                    mimetype="application/json; charset=utf-8"
                                )
                                logging.info(
                                    f"📊 [{source_name}] Response recreado: {len(new_body)} bytes, respuesta_usuario={'respuesta_usuario' in response_data}")
                    except Exception as e:
                        logging.error(
                            f"❌ [{source_name}] Error inyectando metadata: {e}")
                        import traceback
                        logging.error(traceback.format_exc())

                    # 4️⃣ CAPTURA AUTOMÁTICA DE CONVERSACIÓN RICA COMPLETA (solo si hay contexto real)
                    try:
                        session_id = (
                            req.headers.get("Session-ID")
                            or req.params.get("session_id")
                            or "global"
                        )

                        resumen_completo = (memoria_previa.get(
                            "resumen_conversacion", "") if memoria_previa else "")
                        total_interacciones = (memoria_previa.get(
                            "total_interacciones", 0) if memoria_previa else 0)
                        ultimo_tema = (memoria_previa.get(
                            "ultimo_tema", "") if memoria_previa else "")

                        # Determinar si la ejecución fue "activa" (backend/agent real)
                        ejecucion_activa = False
                        try:
                            if isinstance(response, func.HttpResponse):
                                # Considerar ejecución activa si la respuesta es 2xx/3xx y contiene cuerpo útil
                                status_ok = 200 <= (
                                    getattr(response, "status_code", 500) or 500) < 400
                                body_bytes = response.get_body() or b""
                                body_text = body_bytes.decode(
                                    "utf-8", errors="ignore") if body_bytes else ""
                                parsed = {}
                                try:
                                    parsed = json.loads(
                                        body_text) if body_text else {}
                                except:
                                    parsed = {}

                                tiene_valor_semantico = False
                                if isinstance(parsed, dict):
                                    for key in ("respuesta_usuario", "respuesta", "texto_semantico", "resultado", "output", "mensaje"):
                                        val = parsed.get(key)
                                        if isinstance(val, str) and len(val.strip()) > 20:
                                            tiene_valor_semantico = True
                                            break
                                    # también considerar casos con éxito explícito y mensaje corto pero significativo
                                    if not tiene_valor_semantico and (parsed.get("exito") or parsed.get("success")) and parsed.get("mensaje"):
                                        tiene_valor_semantico = len(
                                            str(parsed.get("mensaje")).strip()) > 20

                                ejecucion_activa = status_ok and (
                                    body_text.strip() != "") and tiene_valor_semantico
                        except Exception:
                            ejecucion_activa = False

                        # Excluir procesos automáticos / triviales
                        source_lower = source_name.lower() if source_name else ""
                        es_proceso_automatico = any(term in source_lower for term in (
                            "timer", "cron", "supervisor", "foundry", "scheduler"))

                        # Condiciones para crear snapshot:
                        # - existe resumen con contenido real y suficiente longitud
                        # - hay al menos 2 interacciones previas (no snapshots por primera interacción)
                        # - la ejecución actual parece ser activa (backend/agente con output semántico)
                        # - no es un proceso/cron automático
                        if (
                            resumen_completo
                            and len(resumen_completo.strip()) > 100
                            and total_interacciones >= 2
                            and ejecucion_activa
                            and not es_proceso_automatico
                        ):
                            try:
                                memory_service.registrar_llamada(
                                    source="conversation_snapshot",
                                    endpoint=route_path,
                                    method="AUTO",
                                    params={
                                        "session_id": session_id,
                                        "trigger": route_path,
                                        "agent_id": req.headers.get("Agent-ID", "unknown"),
                                        # Indicar que este snapshot es global/semántico (no ligado exclusivamente a session_id)
                                        "snapshot_scope": "global_semantic"
                                    },
                                    response_data={
                                        "texto_semantico": f"📸 Conversación consolidada antes de {route_path}: {resumen_completo[:1500]}",
                                        "tipo": "conversation_snapshot",
                                        "ultimo_tema": ultimo_tema,
                                        "total_interacciones": total_interacciones,
                                    },
                                    success=True,
                                )
                                logging.info(
                                    f"📸 Snapshot cognitivo creado ({total_interacciones} interacciones, {len(resumen_completo)} chars)")
                            except Exception as e:
                                logging.warning(
                                    f"⚠️ Error guardando snapshot cognitivo: {e}")
                        else:
                            logging.info(
                                "⏭️ Snapshot omitido (sin contenido semántico, insuficiente historial o ejecución no relevante)")

                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando snapshot cognitivo: {e}")

                    # 5️⃣ REGISTRO DE NUEVA INTERACCIÓN EN COSMOS
                    # ❌ EXCLUIR historial-interacciones para evitar recursión infinita
                    es_endpoint_historial = (
                        "historial" in route_path.lower() or
                        "historial" in source_name.lower() or
                        route_path.endswith("/historial-interacciones")
                    )

                    if not es_endpoint_historial:
                        try:
                            from services.memory_service import memory_service
                            session_id = (
                                req.headers.get("Session-ID")
                                or req.params.get("session_id")
                                or "constant-session-id"
                            )
                            agent_id = (
                                req.headers.get("Agent-ID")
                                or req.params.get("agent_id")
                                or "unknown_agent"
                            )

                            # Procesar el cuerpo de respuesta si existe
                            if isinstance(response, func.HttpResponse):
                                body = response.get_body()
                                output_data = json.loads(body.decode(
                                    "utf-8")) if body else {"status": response.status_code}
                            else:
                                output_data = {"raw_response": True}

                            # 🧠 EXTRACCIÓN COGNITIVA AGNÓSTICA - Prioriza voz del agente
                            texto_semantico = None
                            origen_semantico = "fallback"

                            if isinstance(output_data, dict):
                                # 1️⃣ VOZ DEL AGENTE (máxima prioridad cognitiva)
                                for campo in ["respuesta_usuario", "respuesta", "resultado", "output"]:
                                    if output_data.get(campo):
                                        valor = str(output_data[campo]).strip()
                                        if len(valor) > 20:  # Mínimo semántico
                                            texto_semantico = f"💬 {valor[:2000]}"
                                            origen_semantico = "voz_agente"
                                            break

                                # 2️⃣ RESUMEN TÉCNICO/SEMÁNTICO (generado por endpoint)
                                if not texto_semantico and output_data.get("texto_semantico"):
                                    valor = str(
                                        output_data["texto_semantico"]).strip()
                                    if len(valor) > 20:
                                        texto_semantico = valor[:2000]
                                        origen_semantico = "endpoint_semantico"

                                # 3️⃣ MENSAJE INFORMATIVO (feedback del sistema)
                                if not texto_semantico and output_data.get("mensaje"):
                                    valor = str(output_data["mensaje"]).strip()
                                    if len(valor) > 20 and "CONSULTA DE HISTORIAL" not in valor:
                                        texto_semantico = f"📝 {valor[:2000]}"
                                        origen_semantico = "mensaje_sistema"

                                # 4️⃣ CONTENIDO PROCESADO (agnóstico - cualquier endpoint)
                                if not texto_semantico and output_data.get("contenido"):
                                    contenido = str(
                                        output_data["contenido"]).strip()
                                    if len(contenido) > 50:
                                        resumen = contenido[:300] + "..." if len(
                                            contenido) > 300 else contenido
                                        ruta = output_data.get(
                                            "ruta", output_data.get("archivo", "datos"))
                                        texto_semantico = f"📄 Procesado '{ruta}' ({len(contenido)} chars): {resumen}"
                                        origen_semantico = "contenido_procesado"

                                # 5️⃣ FALLBACK TÉCNICO (última opción)
                                if not texto_semantico:
                                    if output_data.get("exito") or output_data.get("success"):
                                        estado = "exitoso"
                                    elif output_data.get("error"):
                                        estado = f"error: {str(output_data['error'])[:100]}"
                                    else:
                                        estado = "completado"
                                    texto_semantico = f"⚙️ Operación técnica {estado}"
                                    origen_semantico = "fallback_tecnico"

                            # Validación final
                            if not texto_semantico or len(texto_semantico.strip()) < 10:
                                texto_semantico = f"⚙️ Interacción técnica en {route_path}"
                                origen_semantico = "fallback_minimo"

                            # Limpiar campos verbosos
                            output_data_limpio = {
                                k: v for k, v in output_data.items()
                                if k not in ["interacciones", "contenido", "mensaje_original"]
                            } if isinstance(output_data, dict) else output_data

                            if isinstance(output_data_limpio, dict):
                                output_data_limpio["texto_semantico"] = texto_semantico
                                output_data = output_data_limpio

                            logging.info(
                                f"🧠 Semántica capturada [{origen_semantico}]: {texto_semantico[:100]}...")

                            # 🔥 ENRIQUECER CON CONTEXTO PREVIO ANTES DE GUARDAR
                            if memoria_previa and memoria_previa.get("tiene_historial"):
                                # Agregar resumen de conversación previa al output
                                if isinstance(output_data, dict):
                                    output_data["contexto_previo"] = {
                                        "total_interacciones": memoria_previa.get("total_interacciones", 0),
                                        "resumen": memoria_previa.get("resumen_conversacion", "")[:500],
                                        "ultimo_tema": memoria_previa.get("ultimo_tema", ""),
                                        "tiene_contexto": True
                                    }
                                    logging.info(
                                        f"🧠 [{source_name}] Contexto previo enriquecido: {memoria_previa.get('total_interacciones', 0)} interacciones")

                            # Solo guardar si hay valor semántico real
                            if origen_semantico not in ["fallback_minimo"] or len(texto_semantico) > 30:
                                memory_service.registrar_llamada(
                                    source=source_name,
                                    endpoint=route_path,
                                    method=req.method,
                                    params={
                                        "session_id": session_id, "agent_id": agent_id, "headers": dict(req.headers)},
                                    response_data=output_data,
                                    success=True
                                )
                                logging.info(
                                    f"💾 [{source_name}] Memoria cognitiva COMPLETA guardada ✅ (con contexto previo)")

                                # 🔥 REGISTRAR RESPUESTA SEMÁNTICA DEL AGENTE
                                try:
                                    from registrar_respuesta_semantica import registrar_respuesta_semantica

                                    # Extraer texto de respuesta del agente (priorizar respuesta_usuario)
                                    respuesta_texto = None
                                    if isinstance(output_data, dict):
                                        respuesta_texto = (
                                            output_data.get("respuesta_usuario") or
                                            output_data.get("respuesta") or
                                            output_data.get("resultado") or
                                            output_data.get("mensaje") or
                                            output_data.get("contenido")
                                        )

                                    if respuesta_texto and isinstance(respuesta_texto, str) and len(respuesta_texto.strip()) > 50:
                                        registrar_respuesta_semantica(
                                            respuesta_texto,
                                            session_id,
                                            agent_id,
                                            route_path
                                        )
                                        logging.info(
                                            f"🤖 Respuesta del agente capturada: {len(respuesta_texto)} chars")
                                except Exception as e:
                                    logging.warning(
                                        f"⚠️ Error registrando respuesta semántica: {e}")

                                # 🔥 Enviar a cola para indexación semántica
                                try:
                                    conn_str = os.environ.get(
                                        "AzureWebJobsStorage")
                                    if not conn_str:
                                        logging.warning(
                                            "⚠️ AzureWebJobsStorage no configurado: se omite envío a cola de indexación")
                                    else:
                                        queue_client = QueueClient.from_connection_string(
                                            conn_str,
                                            "memory-indexing-queue"
                                        )
                                        evento = {
                                            "id": f"{session_id}_{int(time.time())}",
                                            "agent_id": agent_id,
                                            "session_id": session_id,
                                            "endpoint": route_path,
                                            "timestamp": datetime.now().isoformat(),
                                            "event_type": "endpoint_call",
                                            "texto_semantico": texto_semantico,
                                            "data": {"success": True}
                                        }
                                        queue_client.send_message(
                                            json.dumps(evento))
                                        logging.info(
                                            f"📤 Enviado a cola de indexación")
                                except Exception as e:
                                    logging.warning(
                                        f"⚠️ Error enviando a cola: {e}")
                            else:
                                logging.info(
                                    f"🚫 [{source_name}] Descartado: sin valor semántico suficiente")

                            logging.info(
                                f"💾 [{source_name}] Interacción registrada en Cosmos ✅ - sesión {session_id}")
                        except Exception as e:
                            logging.warning(
                                f"⚠️ [{source_name}] Error registrando llamada: {e}")
                    else:
                        logging.info(
                            f"⏭️ [{source_name}] Endpoint de historial excluido del registro")

                    # 6️⃣ CAPTURA DE RESPUESTA COMPLETA FOUNDRY UI
                    try:
                        session_id = req.headers.get(
                            "Session-ID") or "universal_session"
                        agent_id = req.headers.get(
                            "Agent-ID") or "foundry_user"

                        if isinstance(response, func.HttpResponse):
                            body = response.get_body()
                            if body:
                                body_text = body.decode(
                                    "utf-8", errors="ignore").strip()
                                if len(body_text) > 50:
                                    from registrar_respuesta_semantica import registrar_respuesta_semantica
                                    registrar_respuesta_semantica(
                                        body_text,
                                        session_id,
                                        agent_id,
                                        route_path
                                    )
                                    logging.info(
                                        f"🤖 [Foundry UI] Respuesta capturada: {len(body_text)} chars")
                        else:
                            logging.info(
                                "⏭️ No se pudo leer cuerpo de respuesta Foundry UI (no es HttpResponse).")
                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando respuesta Foundry UI: {e}")

                    return response

                if "historial" not in route_path.lower():
                    logging.info(
                        f"✅ Memoria automática aplicada a endpoint: {route_path}")
                else:
                    logging.info(
                        f"⏭️ Endpoint de historial: wrapper aplicado SIN registro")
                return original_route(*args, **kwargs)(wrapper)

            except Exception as e:
                logging.error(f"💥 Error crítico en wrapper: {e}")
                return original_route(*args, **kwargs)(func_ref)

        return decorator

    return route_with_memory


def apply_memory_wrapper(app: func.FunctionApp) -> None:
    """Aplica el wrapper de memoria a una instancia de FunctionApp."""
    try:
        if not hasattr(app, "route") or not callable(app.route):
            logging.error("❌ app.route no existe o no es callable")
            return

        app.route = memory_route(app)
        logging.info("🧠 Memory wrapper aplicado exitosamente a app.route")

    except Exception as e:
        logging.error(f"💥 Error aplicando memory wrapper: {e}")
        logging.warning("La aplicación continuará sin memoria automática")


def wrap_function_app_with_memory(app: func.FunctionApp) -> func.FunctionApp:
    """Envuelve una FunctionApp con memoria automática y la retorna."""
    apply_memory_wrapper(app)
    logging.info("🚀 FunctionApp envuelta con sistema de memoria automática")
    return app
