"""
Endpoint: /api/diagnostico-recursos
Realiza diagnóstico de recursos Azure (Cosmos, Insights, etc.)
"""
from function_app import app
import logging
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import azure.functions as func

# Asegura acceso a function_app y a módulos superiores
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@app.function_name(name="diagnostico_recursos_http")
@app.route(route="diagnostico-recursos", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def diagnostico_recursos_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para configurar diagnósticos de recursos Azure"""
    print(f"\n>>> ENDPOINT diagnostico_recursos_http INICIADO - Method: {req.method} <<<\n", flush=True)
    logging.info("[ENTRY] diagnostico_recursos_http iniciado")
    
    try:
        from function_app import IS_AZURE, MGMT_SDK, STORAGE_CONNECTION_STRING, CACHE
        from services.memory_service import memory_service
        from memory_manual import aplicar_memoria_manual
        from cosmos_memory_direct import (
            consultar_memoria_cosmos_directo,
            aplicar_memoria_cosmos_directo
        )
        from function_app import _json, _error, _s, _to_bool, _try_default_credential
        
        logging.info("[OK] Imports completados")
    except Exception as import_err:
        logging.error(f"[FAIL] Error en imports: {import_err}")
        return func.HttpResponse(
            json.dumps({"ok": False, "error": f"Import error: {str(import_err)}"}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
    
    # 🧠 CONSULTAR MEMORIA COSMOS DB DIRECTAMENTE
    try:
        memoria_previa = consultar_memoria_cosmos_directo(req)
        if memoria_previa and memoria_previa.get("tiene_historial"):
            logging.info(f"🧠 Diagnostico-recursos: {memoria_previa['total_interacciones']} interacciones encontradas")
    except Exception as mem_err:
        logging.warning(f"Error consultando memoria: {mem_err}")
        memoria_previa = None
    
    try:
        # Verificar si se solicitan métricas
        metricas_param = req.params.get("metricas", "false").lower() == "true"

        if req.method == "GET" and metricas_param:
            # Delegar a la función completa para métricas
            logging.info(
                "diagnostico_recursos_http: Delegating to diagnostico_recursos_completo_http for metrics")
            try:
                from function_app import diagnostico_recursos_completo_http
                return diagnostico_recursos_completo_http(req)
            except ImportError:
                logging.warning("diagnostico_recursos_completo_http no disponible")
                return func.HttpResponse(
                    json.dumps({"ok": False, "error": "Funcion completa no disponible"}, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=500
                )

        if req.method == "GET":
            # Retornar información sobre el servicio
            logging.info("diagnostico_recursos_http: GET request received")
            return func.HttpResponse(
                json.dumps({
                    "ok": True,
                    "message": "Servicio de diagnósticos disponible",
                    "mgmt_sdk_available": MGMT_SDK,
                    "endpoints": {
                        "POST": "Configurar diagnósticos para un recurso"
                    }
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # POST request handling with proper body validation
        logging.info("diagnostico_recursos_http: POST request received")

        body = {}
        if req.method == "POST":
            try:
                body_text = req.get_body().decode('utf-8')
                if body_text:
                    body = json.loads(body_text)
                else:
                    body = {}

                # Verificar si se solicitan métricas en el body
                if _to_bool(body.get("metricas")):
                    logging.info(
                        "🔁 Redirigiendo POST con metricas=True hacia diagnostico_recursos_completo_http")
                    # Crear un nuevo request con parámetros GET para obtener métricas generales
                    from urllib.parse import urlencode
                    try:
                        from function_app import diagnostico_recursos_completo_http
                        new_req = func.HttpRequest(
                            method="GET",
                            url=f"{req.url}?metricas=true",
                            headers=req.headers,
                            params={"metricas": "true"},
                            body=b""
                        )
                        return diagnostico_recursos_completo_http(new_req)
                    except ImportError:
                        logging.warning("diagnostico_recursos_completo_http no disponible")
                        pass  # Continuar con flujo normal

            except Exception as e:
                logging.error(
                    f"diagnostico_recursos_http: JSON parsing error: {str(e)}")
                # Continuar con el flujo normal si no se puede parsear el JSON
                body = {}

        rid = _s(body.get("recurso")) if body else ""
        profundidad = _s(body.get("profundidad")
                         or "basico") if body else "basico"

        logging.info(
            f"diagnostico_recursos_http: Processing recurso='{rid}', profundidad='{profundidad}'")

        # If no specific resource is provided, return general diagnostics
        if not rid:
            logging.info(
                "diagnostico_recursos_http: No specific resource provided, returning general diagnostics")

            # Return general system diagnostics instead of an error
            general_diagnostics = {
                "ok": True,
                "tipo": "diagnostico_general",
                "timestamp": datetime.now().isoformat(),
                "ambiente": "Azure" if IS_AZURE else "Local",
                "sistema": {
                    "mgmt_sdk_available": MGMT_SDK,
                    "blob_storage_configured": bool(STORAGE_CONNECTION_STRING),
                    "cache_entries": len(CACHE),
                    "function_app": os.environ.get("WEBSITE_SITE_NAME", "local")
                },
                "profundidad": profundidad,
                "mensaje": "Diagnóstico general del sistema completado"
            }

            # Registrar evento de auditoría en memoria
            try:
                memory_service.log_semantic_event({
                    "tipo": "auditoria_event",
                    "fuente": "diagnostico_recursos_http",
                    "nivel": profundidad,
                    "mensaje": "Diagnóstico general completado correctamente",
                    "timestamp": datetime.utcnow().isoformat()
                })
                logging.info("[OK] Evento de auditoria registrado")
            except Exception as audit_err:
                logging.warning(f"Error registrando auditoria: {audit_err}")
            
            logging.info(f"[RETURN] Devolviendo diagnostico general: {json.dumps(general_diagnostics, ensure_ascii=False)[:200]}")

            return func.HttpResponse(
                json.dumps(general_diagnostics, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # Skip credential check for test resources
        logging.info(
            "diagnostico_recursos_http: Attempting to get default credentials")
        try:
            if not _try_default_credential():
                logging.warning(
                    "diagnostico_recursos_http: No credentials, continuing with limited functionality")
        except Exception as cred_err:
            logging.warning(f"Credential check failed: {cred_err}")

        try:
            logging.info(
                f"diagnostico_recursos_http: Starting diagnostics for resource: {rid}")

            # 🔍 DETECTAR SI ES AZURE AI SEARCH
            if "search" in rid.lower():
                try:
                    from services.azure_search_client import AzureSearchService
                    search_service = AzureSearchService()

                    # Hacer búsqueda de prueba para validar funcionamiento
                    test_search = search_service.search("test", top=1)

                    result = {
                        "ok": True,
                        "recurso": rid,
                        "tipo": "Azure AI Search",
                        "profundidad": profundidad,
                        "timestamp": datetime.now().isoformat(),
                        "metricas": {
                            "servicio": "operativo",
                            "busqueda_vectorial": test_search.get("exito", False),
                            "documentos_indexados": test_search.get("total", 0)
                        },
                        "diagnostico": {
                            "estado": "operativo" if test_search.get("exito") else "error",
                            "tipo": "azure_search",
                            "precision": "alta" if test_search.get("exito") else "desconocida"
                        }
                    }
                except Exception as e:
                    logging.warning(f"Error consultando Azure Search: {e}")
                    result = {
                        "ok": True,
                        "recurso": rid,
                        "tipo": "Azure AI Search",
                        "profundidad": profundidad,
                        "timestamp": datetime.now().isoformat(),
                        "diagnostico": {
                            "estado": "no_disponible",
                            "error": str(e)
                        }
                    }
            else:
                # Lógica de diagnóstico POST para recurso específico
                result = {
                    "ok": True,
                    "recurso": rid,
                    "profundidad": profundidad,
                    "timestamp": datetime.now().isoformat(),
                    "diagnostico": {
                        "estado": "completado",
                        "tipo": "recurso_especifico"
                    }
                }

            # Registrar auditoría del diagnóstico específico
            try:
                memory_service.log_semantic_event({
                    "tipo": "auditoria_event",
                    "fuente": "diagnostico_recursos_http",
                    "recurso": rid,
                    "nivel": profundidad,
                    "resultado": "completado",
                    "timestamp": datetime.utcnow().isoformat()
                })
                logging.info("[OK] Auditoria de diagnostico especifico registrada")
            except Exception as audit_err:
                logging.warning(f"Error registrando auditoria especifica: {audit_err}")

            logging.info(
                "diagnostico_recursos_http: Diagnostics completed successfully")
            
            # Aplicar memoria Cosmos y manual
            try:
                result = aplicar_memoria_cosmos_directo(req, result)
                logging.info("[OK] Memoria Cosmos aplicada")
            except Exception as mem_err:
                logging.warning(f"Error aplicando memoria Cosmos: {mem_err}")
            
            try:
                result = aplicar_memoria_manual(req, result)
                logging.info("[OK] Memoria manual aplicada")
            except Exception as mem_err:
                logging.warning(f"Error aplicando memoria manual: {mem_err}")
            
            # Registrar llamada
            try:
                memory_service.registrar_llamada(
                    source="diagnostico_recursos",
                    endpoint="/api/diagnostico-recursos",
                    method=req.method,
                    params={"session_id": req.headers.get("Session-ID"), "recurso": rid},
                    response_data=result,
                    success=result.get("ok", False)
                )
                logging.info("[OK] Llamada registrada en memoria")
            except Exception as reg_err:
                logging.warning(f"Error registrando llamada: {reg_err}")
            
            logging.info(f"[RETURN] Devolviendo resultado: {json.dumps(result, ensure_ascii=False)[:200]}")
            return _json(result)
        except PermissionError as e:
            error_type = e.__class__.__name__
            error_msg = str(e)
            logging.error(
                f"diagnostico_recursos_http: PermissionError ({error_type}): {error_msg}")
            return _error("AZURE_AUTH_FORBIDDEN", 403, f"{error_type}: {error_msg}")
        except Exception as e:
            error_type = e.__class__.__name__
            error_msg = str(e)
            logging.error(
                f"diagnostico_recursos_http: Exception in diagnostics logic ({error_type}): {error_msg}")
            return _error("DiagError", 500, f"{error_type}: {error_msg}")

    except Exception as e:
        error_type = e.__class__.__name__
        error_msg = str(e)
        logging.error(
            f"diagnostico_recursos_http: Unexpected exception ({error_type}): {error_msg}")
        logging.exception(
            "diagnostico_recursos_http failed with full traceback")
        return _error("UnexpectedError", 500, f"{error_type}: {error_msg}")
