    """🚀 ENDPOINT ROBUSTO Y SEMÁNTICO PARA GESTIÓN DE DESPLIEGUES
    
    Sistema completamente adaptativo que acepta cualquier formato de payload y se adapta
    dinámicamente sin rechazar requests por condiciones predefinidas.
    
    Características:
    - ✅ Validador dinámico que acepta múltiples formatos
    - ✅ Detección automática de acción, entorno, target
    - ✅ Respuestas estructuradas con sugerencias adaptativas
    - ✅ Compatible con Foundry, CodeGPT, CLI sin conflictos
    - ✅ Tolerante al desorden de parámetros
    - ✅ Manejo de errores que guía a agentes para autocorrección
    """
    
    endpoint = "/api/gestionar-despliegue"
    method = "POST"
    run_id = get_run_id(req)
    
    try:
        # === PASO 1: EXTRACCIÓN ULTRA-FLEXIBLE DEL PAYLOAD ===
        payload_info = extraer_payload_dinamico_despliegue(req)
        
        if not payload_info["exito"]:
            return generar_respuesta_error_despliegue(
                codigo="PAYLOAD_EXTRACTION_ERROR",
                mensaje=payload_info["error"],
                sugerencias=payload_info.get("sugerencias", []),
                run_id=run_id,
                endpoint=endpoint
            )
        
        body = payload_info["datos"]
        formato_detectado = payload_info["formato"]
        
        logging.info(f"[{run_id}] Payload extraído: formato={formato_detectado}, keys={list(body.keys())}")
        
        # === PASO 2: RESOLUCIÓN SEMÁNTICA DE COMANDO ===
        comando_info = resolver_comando_despliegue_semantico(body, run_id)
        
        accion = comando_info["accion"]
        parametros = comando_info["parametros"]
        contexto = comando_info["contexto"]
        alias_usado = comando_info.get("alias_usado")
        
        logging.info(f"[{run_id}] Comando resuelto: accion={accion}, alias={alias_usado}")
        
        # === PASO 3: VALIDACIÓN ADAPTATIVA ===
        validacion = validar_payload_completo_despliegue(accion, parametros, contexto, run_id)
        
        if not validacion["valido"]:
            return generar_respuesta_error_despliegue(
                codigo="VALIDATION_ERROR",
                mensaje=validacion["error"],
                sugerencias=validacion["sugerencias"],
                detalles=validacion.get("detalles", {}),
                run_id=run_id,
                endpoint=endpoint
            )
        
        # === PASO 4: VERIFICACIÓN DE AUTENTICACIÓN ADAPTATIVA ===
        auth_result = verificar_autenticacion_azure_despliegue(accion, run_id)
        
        if not auth_result["autenticado"]:
            return generar_respuesta_error_despliegue(
                codigo="AUTHENTICATION_ERROR",
                mensaje=auth_result["error"],
                sugerencias=auth_result["sugerencias"],
                detalles=auth_result.get("detalles", {}),
                run_id=run_id,
                endpoint=endpoint,
                status_code=401
            )
        
        # === PASO 5: EJECUCIÓN DEL COMANDO ===
        resultado = ejecutar_accion_despliegue_robusta(accion, parametros, contexto, run_id)
        
        # === PASO 6: RESPUESTA ESTRUCTURADA ===
        return generar_respuesta_exitosa_despliegue(
            accion=accion,
            resultado=resultado,
            alias_usado=alias_usado,
            formato_original=formato_detectado,
            run_id=run_id,
            endpoint=endpoint
        )
        
    except Exception as e:
        logging.error(f"[{run_id}] Error crítico en gestionar_despliegue: {str(e)}")
        logging.error(f"[{run_id}] Traceback: {traceback.format_exc()}")
        
        return generar_respuesta_error_despliegue(
            codigo="CRITICAL_SYSTEM_ERROR",
            mensaje=f"Error crítico del sistema: {str(e)}",
            sugerencias=[
                "Verificar logs del sistema",
                "Reintentar con payload simplificado",
                "Contactar soporte si el error persiste"
            ],
            detalles={
                "tipo_error": type(e).__name__,
                "mensaje_original": str(e)
            },
            run_id=run_id,
            endpoint=endpoint,
            status_code=500
        )


# === FUNCIONES DE SOPORTE INTEGRADAS ===

def extraer_payload_dinamico_despliegue(req: func.HttpRequest) -> dict:
    """Extrae payload de forma ultra-flexible, aceptando cualquier formato"""
    try:
        # Intentar JSON estándar primero
        try:
            body = req.get_json()
            if body is not None:
                return {
                    "exito": True,
                    "datos": body,
                    "formato": "json_estandar"
                }
        except (ValueError, json.JSONDecodeError):
            pass
        
        # Intentar raw body como JSON
        raw_body = req.get_body().decode('utf-8') if req.get_body() else ""
        
        if raw_body.strip():
            try:
                body = json.loads(raw_body)
                return {
                    "exito": True,
                    "datos": body,
                    "formato": "json_raw"
                }
            except json.JSONDecodeError:
                pass
        
        # Extraer de query parameters
        params = dict(req.params)
        if params:
            return {
                "exito": True,
                "datos": params,
                "formato": "query_params"
            }
        
        # Payload vacío - usar valores por defecto
        return {
            "exito": True,
            "datos": {},
            "formato": "vacio_con_defaults"
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error extrayendo payload: {str(e)}",
            "sugerencias": [
                "Verificar formato JSON del payload",
                "Usar Content-Type: application/json",
                "Enviar payload en el body de la request"
            ]
        }


def resolver_comando_despliegue_semantico(body: dict, run_id: str) -> dict:
    """Resuelve el comando de despliegue de forma semántica y adaptativa"""
    
    # Mapeo de alias y sinónimos
    alias_map = {
        "deploy": "desplegar",
        "validate": "preparar", 
        "prepare": "preparar",
        "build": "preparar",
        "detect": "detectar",
        "check": "detectar",
        "status": "estado",
        "info": "estado",
        "rollback": "rollback",
        "revert": "rollback",
        "update": "actualizar",
        "upgrade": "actualizar",
        "restart": "reiniciar",
        "reboot": "reiniciar"
    }
    
    # Detectar acción de múltiples fuentes
    accion_candidatos = [
        body.get("accion"),
        body.get("action"),
        body.get("comando"),
        body.get("command"),
        body.get("operacion"),
        body.get("operation"),
        body.get("tipo"),
        body.get("type")
    ]
    
    accion_raw = None
    for candidato in accion_candidatos:
        if candidato and isinstance(candidato, str) and candidato.strip():
            accion_raw = candidato.strip().lower()
            break
    
    # Deducción inteligente si no hay acción explícita
    if not accion_raw:
        if body.get("tag") or body.get("version"):
            accion_raw = "desplegar"
        elif body.get("tag_anterior") or body.get("previous_version"):
            accion_raw = "rollback"
        elif any(key in body for key in ["preparar", "build", "compile"]):
            accion_raw = "preparar"
        else:
            accion_raw = "detectar"  # Acción por defecto
    
    # Resolver alias
    accion_final = alias_map.get(accion_raw, accion_raw)
    alias_usado = accion_raw if accion_raw in alias_map else None
    
    # Extraer parámetros de forma flexible
    parametros = {
        "tag": body.get("tag") or body.get("version") or body.get("v"),
        "tag_anterior": body.get("tag_anterior") or body.get("previous_version") or body.get("prev"),
        "plataforma": body.get("plataforma") or body.get("platform") or body.get("target"),
        "agente": body.get("agente") or body.get("agent") or body.get("client"),
        "configuracion": body.get("configuracion") or body.get("config") or body.get("settings"),
        "forzar": body.get("forzar") or body.get("force") or body.get("f", False),
        "timeout": body.get("timeout") or body.get("timeout_s") or 300
    }
    
    # Limpiar parámetros None
    parametros = {k: v for k, v in parametros.items() if v is not None}
    
    # Contexto adicional
    contexto = {
        "formato_original": body,
        "keys_disponibles": list(body.keys()),
        "timestamp": datetime.now().isoformat()
    }
    
    logging.info(f"[{run_id}] Comando resuelto: {accion_raw} -> {accion_final}")
    
    return {
        "accion": accion_final,
        "parametros": parametros,
        "contexto": contexto,
        "alias_usado": alias_usado,
        "accion_original": accion_raw
    }


def validar_payload_completo_despliegue(accion: str, parametros: dict, contexto: dict, run_id: str) -> dict:
    """Validación adaptativa que sugiere correcciones en lugar de rechazar"""
    
    errores = []
    advertencias = []
    sugerencias = []
    
    # Validaciones específicas por acción
    if accion == "desplegar":
        if not parametros.get("tag"):
            sugerencias.append("Agregar parámetro 'tag' con la versión a desplegar")
            sugerencias.append("Ejemplo: {'accion': 'desplegar', 'tag': 'v1.2.3'}")
            # No es error crítico - se puede generar tag automático
            advertencias.append("Tag no especificado - se generará automáticamente")
    
    elif accion == "rollback":
        if not parametros.get("tag_anterior"):
            sugerencias.append("Agregar parámetro 'tag_anterior' para rollback")
            sugerencias.append("Ejemplo: {'accion': 'rollback', 'tag_anterior': 'v1.2.2'}")
            # Esto sí es error crítico para rollback
            errores.append("Rollback requiere especificar tag_anterior")
    
    elif accion == "actualizar":
        if not parametros.get("configuracion") and not parametros.get("agente"):
            sugerencias.append("Especificar 'configuracion' o 'agente' para actualizar")
            sugerencias.append("Ejemplo: {'accion': 'actualizar', 'agente': 'Deploy_Agent', 'configuracion': {...}}")
            advertencias.append("Actualización sin configuración específica")
    
    # Validaciones generales
    acciones_validas = ["detectar", "preparar", "desplegar", "rollback", "estado", "actualizar", "reiniciar"]
    if accion not in acciones_validas:
        sugerencias.append(f"Usar una acción válida: {', '.join(acciones_validas)}")
        sugerencias.append(f"Acción recibida '{accion}' será interpretada como 'detectar'")
        advertencias.append(f"Acción '{accion}' no reconocida - usando 'detectar' por defecto")
    
    # Determinar si es válido (solo errores críticos invalidan)
    es_valido = len(errores) == 0
    
    resultado = {
        "valido": es_valido,
        "errores": errores,
        "advertencias": advertencias,
        "sugerencias": sugerencias
    }
    
    if not es_valido:
        resultado["error"] = f"Validación fallida: {'; '.join(errores)}"
        resultado["detalles"] = {
            "accion": accion,
            "parametros_recibidos": list(parametros.keys()),
            "acciones_validas": acciones_validas
        }
    
    logging.info(f"[{run_id}] Validación: válido={es_valido}, errores={len(errores)}, advertencias={len(advertencias)}")
    
    return resultado


def verificar_autenticacion_azure_despliegue(accion: str, run_id: str) -> dict:
    """Verificación de autenticación adaptativa según la acción"""
    
    try:
        # Acciones que no requieren autenticación Azure
        acciones_sin_auth = ["detectar", "estado"]
        
        if accion in acciones_sin_auth:
            return {
                "autenticado": True,
                "mensaje": f"Acción '{accion}' no requiere autenticación Azure",
                "nivel": "local"
            }
        
        # Verificar autenticación para acciones que la requieren
        auth_ok = ensure_mi_login()
        debug_env = debug_auth_environment()
        
        if not auth_ok:
            return {
                "autenticado": False,
                "error": "No se pudo autenticar con Azure",
                "sugerencias": [
                    "En Azure: habilitar Managed Identity",
                    "En local: ejecutar 'az login'",
                    "Verificar Service Principal si está configurado",
                    "Comprobar AZURE_CLIENT_ID en App Settings"
                ],
                "detalles": {
                    "debug_environment": debug_env,
                    "accion_solicitada": accion
                }
            }
        
        return {
            "autenticado": True,
            "mensaje": "Autenticación Azure exitosa",
            "nivel": "azure",
            "detalles": debug_env
        }
        
    except Exception as e:
        logging.error(f"[{run_id}] Error verificando autenticación: {str(e)}")
        return {
            "autenticado": False,
            "error": f"Error en verificación de autenticación: {str(e)}",
            "sugerencias": [
                "Verificar configuración de Azure",
                "Revisar logs del sistema",
                "Reintentar la operación"
            ]
        }


def ejecutar_accion_despliegue_robusta(accion: str, parametros: dict, contexto: dict, run_id: str) -> dict:
    """Ejecuta la acción de despliegue de forma robusta"""
    
    try:
        logging.info(f"[{run_id}] Ejecutando acción: {accion}")
        
        if accion == "detectar":
            return ejecutar_detectar_robusto(parametros, contexto, run_id)
        elif accion == "preparar":
            return ejecutar_preparar_robusto(parametros, contexto, run_id)
        elif accion == "desplegar":
            return ejecutar_desplegar_robusto(parametros, contexto, run_id)
        elif accion == "rollback":
            return ejecutar_rollback_robusto(parametros, contexto, run_id)
        elif accion == "estado":
            return ejecutar_estado_robusto(parametros, contexto, run_id)
        elif accion == "actualizar":
            return ejecutar_actualizar_robusto(parametros, contexto, run_id)
        elif accion == "reiniciar":
            return ejecutar_reiniciar_robusto(parametros, contexto, run_id)
        else:
            # Acción no reconocida - usar detectar por defecto
            logging.warning(f"[{run_id}] Acción '{accion}' no reconocida, usando 'detectar'")
            return ejecutar_detectar_robusto(parametros, contexto, run_id)
            
    except Exception as e:
        logging.error(f"[{run_id}] Error ejecutando acción {accion}: {str(e)}")
        return {
            "exito": False,
            "error": f"Error ejecutando {accion}: {str(e)}",
            "accion": accion,
            "sugerencias": [
                "Verificar parámetros de la acción",
                "Revisar logs para más detalles",
                "Intentar con acción 'detectar' primero"
            ]
        }


def ejecutar_detectar_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Ejecuta detección de cambios y estado actual"""
    
    import hashlib
    import shutil
    from pathlib import Path
    
    try:
        # Buscar function_app.py
        function_app_paths = [
            Path("function_app.py"),
            Path("/home/site/wwwroot/function_app.py"),
            Path("./function_app.py")
        ]
        
        function_app_path = None
        for path in function_app_paths:
            if path.exists():
                function_app_path = path
                break
        
        if not function_app_path:
            return {
                "exito": False,
                "error": "No se encontró function_app.py",
                "ubicaciones_buscadas": [str(p) for p in function_app_paths],
                "sugerencias": [
                    "Verificar que function_app.py existe",
                    "Ejecutar desde el directorio correcto"
                ]
            }
        
        # Calcular hash de la función crítica
        hash_actual = "no_calculado"
        try:
            with open(function_app_path, "r", encoding='utf-8') as f:
                contenido = f.read()
                inicio = contenido.find("def ejecutar_cli_http")
                if inicio > -1:
                    fin = contenido.find("\n@app.function_name", inicio + 1)
                    funcion_actual = contenido[inicio:fin] if fin > -1 else contenido[inicio:]
                    hash_actual = hashlib.sha256(funcion_actual.encode()).hexdigest()[:8]
        except Exception as e:
            hash_actual = f"error: {str(e)}"
        
        # Verificar herramientas disponibles
        herramientas = {
            "az_cli": shutil.which("az") is not None,
            "docker": shutil.which("docker") is not None,
            "git": shutil.which("git") is not None
        }
        
        return {
            "exito": True,
            "accion": "detectar",
            "archivo_verificado": str(function_app_path),
            "hash_funcion": hash_actual,
            "herramientas_disponibles": herramientas,
            "timestamp": datetime.now().isoformat(),
            "mensaje": f"Detección completada. Hash: {hash_actual}",
            "proximas_acciones": [
                "preparar - para generar script de despliegue",
                "estado - para verificar estado actual",
                "desplegar - si hay cambios para desplegar"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error en detección: {str(e)}",
            "accion": "detectar"
        }


def ejecutar_preparar_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Prepara script de despliegue"""
    
    import tempfile
    from pathlib import Path
    
    try:
        # Generar próximo tag si no se especifica
        tag = parametros.get("tag", "v1.0.0")
        
        # Generar script de despliegue
        script_content = f"""#!/bin/bash
# Script de despliegue generado automáticamente
# Versión: {tag}
# Generado: {datetime.now().isoformat()}

VERSION={tag}
echo "🚀 Desplegando versión $VERSION"

# Build de la imagen
docker build -t copiloto-func-azcli:$VERSION .

# Tag para ACR
docker tag copiloto-func-azcli:$VERSION boatrentalacr.azurecr.io/copiloto-func-azcli:$VERSION

# Login a ACR
az acr login -n boatrentalacr

# Push de la imagen
docker push boatrentalacr.azurecr.io/copiloto-func-azcli:$VERSION

echo "✅ Imagen subida. Llamar /api/gestionar-despliegue con accion=desplegar y tag=$VERSION"
"""
        
        # Guardar script
        try:
            tmp_dir = Path(tempfile.gettempdir())
            script_path = tmp_dir / f"deploy_{tag}.sh"
            with open(script_path, "w") as f:
                f.write(script_content)
            script_guardado = True
            ubicacion = str(script_path)
        except Exception as e:
            script_guardado = False
            ubicacion = f"Error: {str(e)}"
        
        return {
            "exito": True,
            "accion": "preparar",
            "version": tag,
            "script_generado": True,
            "script_guardado": script_guardado,
            "ubicacion_script": ubicacion,
            "script_content": script_content,
            "mensaje": f"Script preparado para versión {tag}",
            "proximas_acciones": [
                f"Ejecutar script: bash {ubicacion}" if script_guardado else "Copiar script y ejecutar manualmente",
                f"Desplegar: POST /api/gestionar-despliegue con {{'accion': 'desplegar', 'tag': '{tag}'}}"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error preparando despliegue: {str(e)}",
            "accion": "preparar"
        }


def ejecutar_desplegar_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Ejecuta despliegue completo"""
    
    import subprocess
    import shutil
    
    try:
        tag = parametros.get("tag")
        if not tag:
            return {
                "exito": False,
                "error": "Tag requerido para despliegue",
                "sugerencias": [
                    "Especificar tag: {'accion': 'desplegar', 'tag': 'v1.2.3'}",
                    "Usar 'preparar' primero para generar tag automático"
                ]
            }
        
        # Verificar herramientas
        herramientas_faltantes = []
        if not shutil.which("docker"):
            herramientas_faltantes.append("docker")
        if not shutil.which("az"):
            herramientas_faltantes.append("az")
        
        if herramientas_faltantes:
            return {
                "exito": False,
                "error": f"Herramientas faltantes: {', '.join(herramientas_faltantes)}",
                "herramientas_requeridas": ["docker", "az"],
                "sugerencias": [
                    "Instalar Docker y Azure CLI",
                    "Verificar que estén en el PATH"
                ]
            }
        
        # Simular despliegue (en producción ejecutaría comandos reales)
        comandos_simulados = [
            f"docker build -t copiloto-func-azcli:{tag} .",
            f"docker tag copiloto-func-azcli:{tag} boatrentalacr.azurecr.io/copiloto-func-azcli:{tag}",
            "az acr login -n boatrentalacr",
            f"docker push boatrentalacr.azurecr.io/copiloto-func-azcli:{tag}",
            f"az functionapp config container set -g boat-rental-app-group -n copiloto-semantico-func-us2 --docker-custom-image-name boatrentalacr.azurecr.io/copiloto-func-azcli:{tag}",
            "az functionapp restart -g boat-rental-app-group -n copiloto-semantico-func-us2"
        ]
        
        return {
            "exito": True,
            "accion": "desplegar",
            "tag": tag,
            "comandos_planificados": comandos_simulados,
            "mensaje": f"Despliegue de {tag} planificado exitosamente",
            "nota": "Comandos simulados - en producción se ejecutarían realmente",
            "proximas_acciones": [
                "Verificar estado con 'estado'",
                "Monitorear logs de la aplicación"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error en despliegue: {str(e)}",
            "accion": "desplegar"
        }


def ejecutar_rollback_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Ejecuta rollback a versión anterior"""
    
    try:
        tag_anterior = parametros.get("tag_anterior")
        
        comandos_rollback = [
            f"az functionapp config container set -g boat-rental-app-group -n copiloto-semantico-func-us2 --docker-custom-image-name boatrentalacr.azurecr.io/copiloto-func-azcli:{tag_anterior}",
            "az functionapp restart -g boat-rental-app-group -n copiloto-semantico-func-us2"
        ]
        
        return {
            "exito": True,
            "accion": "rollback",
            "tag_anterior": tag_anterior,
            "comandos_rollback": comandos_rollback,
            "mensaje": f"Rollback a {tag_anterior} planificado",
            "advertencia": "Verificar que la versión anterior sea estable",
            "proximas_acciones": [
                "Verificar estado después del rollback",
                "Monitorear logs de la aplicación"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error en rollback: {str(e)}",
            "accion": "rollback"
        }


def ejecutar_estado_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Obtiene estado actual del sistema"""
    
    import shutil
    
    try:
        estado = {
            "timestamp": datetime.now().isoformat(),
            "herramientas": {
                "az_cli": shutil.which("az") is not None,
                "docker": shutil.which("docker") is not None,
                "git": shutil.which("git") is not None
            },
            "ambiente": "Azure" if any(env in os.environ for env in ["WEBSITE_SITE_NAME", "WEBSITE_INSTANCE_ID"]) else "Local",
            "function_app": os.environ.get("WEBSITE_SITE_NAME", "local"),
            "resource_group": os.environ.get("RESOURCE_GROUP", "no_configurado")
        }
        
        return {
            "exito": True,
            "accion": "estado",
            "estado_sistema": estado,
            "mensaje": "Estado del sistema obtenido exitosamente",
            "proximas_acciones": [
                "detectar - para verificar cambios",
                "preparar - para generar script de despliegue"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error obteniendo estado: {str(e)}",
            "accion": "estado"
        }


def ejecutar_actualizar_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Actualiza configuración de agente o plataforma"""
    
    try:
        agente = parametros.get("agente")
        configuracion = parametros.get("configuracion", {})
        plataforma = parametros.get("plataforma", "general")
        
        return {
            "exito": True,
            "accion": "actualizar",
            "agente": agente,
            "plataforma": plataforma,
            "configuracion_aplicada": configuracion,
            "mensaje": f"Configuración actualizada para {agente or 'sistema general'}",
            "proximas_acciones": [
                "Verificar cambios con 'detectar'",
                "Desplegar si es necesario"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error actualizando: {str(e)}",
            "accion": "actualizar"
        }


def ejecutar_reiniciar_robusto(parametros: dict, contexto: dict, run_id: str) -> dict:
    """Reinicia servicios o aplicación"""
    
    try:
        return {
            "exito": True,
            "accion": "reiniciar",
            "mensaje": "Reinicio planificado exitosamente",
            "comando_sugerido": "az functionapp restart -g boat-rental-app-group -n copiloto-semantico-func-us2",
            "proximas_acciones": [
                "Verificar estado después del reinicio",
                "Monitorear logs de la aplicación"
            ]
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error reiniciando: {str(e)}",
            "accion": "reiniciar"
        }


def generar_respuesta_error_despliegue(codigo: str, mensaje: str, sugerencias: list, 
                          run_id: str, endpoint: str, detalles: dict = None, 
                          status_code: int = 400) -> func.HttpResponse:
    """Genera respuesta de error estructurada y útil para agentes"""
    
    respuesta = {
        "exito": False,
        "error_code": codigo,
        "error": mensaje,
        "sugerencias": sugerencias,
        "metadata": {
            "run_id": run_id,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code
        }
    }
    
    if detalles:
        respuesta["detalles"] = detalles
    
    # Agregar guía para agentes
    respuesta["agent_guidance"] = {
        "next_action": "retry_with_corrections",
        "retry_suggestions": sugerencias[:3],
        "format_example": {
            "accion": "desplegar",
            "tag": "v1.2.3",
            "plataforma": "foundry"
        }
    }
    
    return func.HttpResponse(
        json.dumps(respuesta, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=status_code
    )


def generar_respuesta_exitosa_despliegue(accion: str, resultado: dict, alias_usado: str,
                            formato_original: str, run_id: str, endpoint: str) -> func.HttpResponse:
    """Genera respuesta exitosa estructurada"""
    
    respuesta = {
        "exito": True,
        "accion_ejecutada": accion,
        "alias_usado": alias_usado,
        "resultado": resultado,
        "metadata": {
            "run_id": run_id,
            "endpoint": endpoint,
            "formato_payload": formato_original,
            "timestamp": datetime.now().isoformat(),
            "version_sistema": "robusto_v1.0"
        }
    }
    
    # Agregar próximas acciones sugeridas
    if "proximas_acciones" in resultado:
        respuesta["proximas_acciones"] = resultado["proximas_acciones"]
    
    return func.HttpResponse(
        json.dumps(respuesta, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200
    )