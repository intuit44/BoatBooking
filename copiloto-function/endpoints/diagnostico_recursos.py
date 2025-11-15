"""
Endpoint: /api/diagnostico-recursos (CONSOLIDADO)
Realiza diagnóstico completo de recursos Azure con métricas avanzadas
"""
from function_app import app
import logging
import json
import os
import sys
import re
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, TypeVar
import azure.functions as func

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

T = TypeVar('T')

def _safe(obj: Any, attr: str, default: T) -> T:
    """Devuelve obj.attr o default si obj es None o el atributo no existe/vale None."""
    try:
        if obj is None:
            return default
        val = getattr(obj, attr, default)
        return default if val is None else val
    except Exception:
        return default


def obtener_credenciales_azure():
    """Obtiene credenciales de Azure (Managed Identity en Azure, CLI en local)"""
    from azure.identity import ManagedIdentityCredential, AzureCliCredential
    try:
        if os.getenv("WEBSITE_INSTANCE_ID"):
            credential = ManagedIdentityCredential()
            logging.info("Usando ManagedIdentityCredential (Azure).")
        else:
            credential = AzureCliCredential()
            logging.info("Usando AzureCliCredential (Local).")
        return credential
    except Exception as e:
        logging.error(f"Error obteniendo credenciales de Azure: {str(e)}")
        return None


def obtener_estado_function_app(app_name: str, resource_group: str, subscription_id: str) -> dict:
    from function_app import MGMT_SDK, WebSiteManagementClient
    from azure.core.exceptions import ResourceNotFoundError, AzureError
    
    if not MGMT_SDK or WebSiteManagementClient is None:
        return {"nombre": app_name, "estado": "Unknown", "error": "SDK de administración no instalado"}

    try:
        credential = obtener_credenciales_azure()
        if not credential:
            return {"nombre": app_name, "estado": "Unknown", "error": "Sin credenciales de Azure"}

        client = WebSiteManagementClient(credential, subscription_id)
        webapp = client.web_apps.get(resource_group, app_name)
        config = client.web_apps.get_configuration(resource_group, app_name)

        server_farm_id = _safe(webapp, "server_farm_id", "") or ""
        plan = server_farm_id.split("/")[-1] if server_farm_id else "Unknown"
        default_host = _safe(webapp, "default_host_name", "")

        return {
            "nombre": _safe(webapp, "name", app_name),
            "estado": _safe(webapp, "state", "Unknown"),
            "plan": plan,
            "runtime": _safe(config, "python_version", None) or _safe(config, "linux_fx_version", "Unknown"),
            "url": f"https://{default_host}" if default_host else "",
            "location": _safe(webapp, "location", "Unknown"),
            "kind": _safe(webapp, "kind", "app"),
            "enabled": bool(_safe(webapp, "enabled", True)),
            "availability_state": _safe(webapp, "availability_state", "Unknown"),
        }
    except ResourceNotFoundError:
        return {"nombre": app_name, "estado": "NotFound", "error": f"Function App '{app_name}' no encontrada en '{resource_group}'"}
    except AzureError as e:
        return {"nombre": app_name, "estado": "Error", "error": str(e)}
    except Exception as e:
        logging.exception("obtener_estado_function_app failed")
        return {"nombre": app_name, "estado": "Unknown", "error": str(e), "tipo_error": type(e).__name__}


def obtener_info_storage_account(account_name: str, resource_group: str, subscription_id: str) -> dict:
    from function_app import MGMT_SDK, StorageManagementClient
    from azure.core.exceptions import ResourceNotFoundError
    
    if not MGMT_SDK or StorageManagementClient is None:
        return {"nombre": account_name, "estado": "Unknown", "error": "SDK de administración no instalado"}

    try:
        credential = obtener_credenciales_azure()
        if not credential:
            return {"nombre": account_name, "estado": "Unknown", "error": "Sin credenciales"}

        client = StorageManagementClient(credential, subscription_id)
        sa = client.storage_accounts.get_properties(resource_group, account_name)

        try:
            keys_obj = client.storage_accounts.list_keys(resource_group, account_name)
            keys_list = getattr(keys_obj, "keys", None)
            has_keys = bool(keys_list) and len(keys_list) > 0
        except Exception:
            has_keys = False

        sku = _safe(sa, "sku", None)
        sku_name = getattr(sku, "name", "Unknown") if sku else "Unknown"
        sku_tier = getattr(sku, "tier", "Unknown") if sku else "Unknown"
        pe = _safe(sa, "primary_endpoints", None)
        blob_endpoint = getattr(pe, "blob", None) if pe else None

        return {
            "nombre": _safe(sa, "name", account_name),
            "tipo": sku_name,
            "tier": sku_tier,
            "replicacion": sku_name,
            "location": _safe(sa, "location", "Unknown"),
            "estado": _safe(sa, "status_of_primary", "Available"),
            "access_tier": _safe(sa, "access_tier", "Hot"),
            "kind": _safe(sa, "kind", "StorageV2"),
            "provisioning_state": _safe(sa, "provisioning_state", "Unknown"),
            "has_keys": has_keys,
            "blob_endpoint": blob_endpoint,
        }
    except ResourceNotFoundError:
        return {"nombre": account_name, "estado": "NotFound", "error": f"Storage Account '{account_name}' no encontrado"}
    except Exception as e:
        logging.exception("obtener_info_storage_account failed")
        return {"nombre": account_name, "estado": "Unknown", "error": str(e), "tipo_error": type(e).__name__}


def obtener_metricas_function_app(app_name: str, resource_group: str, subscription_id: str) -> dict:
    """Obtiene métricas de la Function App usando el SDK"""
    from function_app import MGMT_SDK, MonitorManagementClient
    
    if not MGMT_SDK or MonitorManagementClient is None:
        return {"error": "SDK de administración no instalado"}

    try:
        credential = obtener_credenciales_azure()
        if not credential:
            return {"error": "No se pudieron obtener credenciales"}

        client = MonitorManagementClient(credential, subscription_id)
        resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Web/sites/{app_name}"
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        metricas = {}

        metricas_a_consultar = [
            "Http5xx", "Requests", "Http2xx", "Http4xx", "HttpResponseTime",
            "AverageResponseTime", "MemoryWorkingSet", "FunctionExecutionCount", "FunctionExecutionUnits"
        ]

        for metrica_name in metricas_a_consultar:
            try:
                result = client.metrics.list(
                    resource_id,
                    timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                    interval=timedelta(hours=1),
                    metricnames=metrica_name,
                    aggregation='Average,Count,Total'
                )

                for item in getattr(result, 'value', []):
                    if item.timeseries:
                        for ts in item.timeseries:
                            if ts.data:
                                ultimo_valor = ts.data[-1]
                                metricas[metrica_name] = {
                                    "average": ultimo_valor.average,
                                    "count": ultimo_valor.count,
                                    "total": ultimo_valor.total,
                                    "timestamp": ultimo_valor.time_stamp.isoformat() if ultimo_valor.time_stamp else None
                                }
                                break
                        break
            except Exception as e:
                metricas[metrica_name] = {"error": str(e)}

        return metricas
    except Exception as e:
        logging.error(f"Error obteniendo métricas: {str(e)}")
        return {"error": str(e)}


def diagnosticar_function_app_con_sdk() -> dict:
    """Diagnóstico completo usando SDK de Azure - OPTIMIZADO"""
    from function_app import IS_AZURE, CACHE, CONTAINER_NAME, get_blob_client
    
    diagnostico = {
        "timestamp": datetime.now().isoformat(),
        "function_app": os.environ.get("WEBSITE_SITE_NAME", "local"),
        "checks": {},
        "recomendaciones": [],
        "metricas": {},
        "recursos": {},
        "alertas": [],
        "optimizado": True
    }

    app_insights_key = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")

    diagnostico["checks"]["configuracion"] = {
        "blob_storage": False,
        "openai_configurado": bool(os.environ.get("AZURE_OPENAI_KEY")),
        "app_insights": bool(app_insights_key),
        "ambiente": "Azure" if IS_AZURE else "Local"
    }

    # Verificar Blob Storage
    client = get_blob_client()
    if client:
        try:
            container_client = client.get_container_client(CONTAINER_NAME)
            if container_client.exists():
                blob_count = sum(1 for _ in container_client.list_blobs())
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": True,
                    "container": CONTAINER_NAME,
                    "archivos": blob_count
                }
                diagnostico["checks"]["configuracion"]["blob_storage"] = True
            else:
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": False,
                    "error": f"El contenedor '{CONTAINER_NAME}' no existe"
                }
        except Exception as e:
            diagnostico["checks"]["blob_storage_detalles"] = {"conectado": False, "error": str(e)}

    # Métricas de cache
    diagnostico["metricas"]["cache"] = {
        "archivos_en_cache": len(CACHE),
        "memoria_cache_bytes": sum(len(str(v)) for v in CACHE.values())
    }

    # Obtener métricas de Function App en Azure con ejecución paralela
    if IS_AZURE:
        app_name = "copiloto-semantico-func-us2"
        resource_group = "boat-rental-app-group"
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "")

        if app_name and subscription_id and resource_group:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                def get_function_state():
                    try:
                        return obtener_estado_function_app(app_name, resource_group, subscription_id)
                    except Exception as e:
                        return {"nombre": app_name, "estado": "Unknown", "error": str(e)}

                def get_storage_info():
                    try:
                        if client:
                            account_name = client.account_name
                            if account_name:
                                return obtener_info_storage_account(account_name, resource_group, subscription_id)
                    except Exception as e:
                        return {"estado": "error", "error": str(e)}
                    return {"estado": "no_client"}

                future_function = executor.submit(get_function_state)
                future_storage = executor.submit(get_storage_info)

                try:
                    diagnostico["recursos"]["function_app"] = future_function.result(timeout=5)
                except concurrent.futures.TimeoutError:
                    diagnostico["recursos"]["function_app"] = {"estado": "timeout", "mensaje": "Consulta excedió 5s"}

                try:
                    diagnostico["recursos"]["storage_account"] = future_storage.result(timeout=3)
                except concurrent.futures.TimeoutError:
                    diagnostico["recursos"]["storage_account"] = {"estado": "timeout", "mensaje": "Consulta excedió 3s"}

            # Obtener métricas de Function App
            try:
                metricas_fa = obtener_metricas_function_app(app_name, resource_group, subscription_id)
                if metricas_fa and not metricas_fa.get("error"):
                    diagnostico["metricas"]["function_app"] = metricas_fa
                else:
                    diagnostico["metricas"]["function_app"] = {"error": metricas_fa.get("error", "No se pudieron obtener métricas")}
            except Exception as e:
                diagnostico["metricas"]["function_app"] = {"error": str(e)}

    # Generar recomendaciones
    if diagnostico.get("recursos", {}).get("function_app", {}).get("estado") != "Running":
        diagnostico["recomendaciones"].append({
            "nivel": "critico",
            "mensaje": "La Function App no está en estado Running",
            "accion": "Verificar configuración y reiniciar si es necesario"
        })

    if not diagnostico["checks"].get("blob_storage_detalles", {}).get("conectado"):
        diagnostico["recomendaciones"].append({
            "nivel": "importante",
            "mensaje": "Blob Storage no está conectado",
            "accion": "Verificar connection string y permisos"
        })

    if diagnostico["metricas"]["cache"]["archivos_en_cache"] > 100:
        diagnostico["recomendaciones"].append({
            "nivel": "sugerencia",
            "mensaje": "Cache con muchos archivos",
            "accion": "Considerar limpiar cache para optimizar memoria"
        })

    metricas_fa = diagnostico.get("metricas", {}).get("function_app", {})
    if metricas_fa.get("Http5xx", {}).get("total", 0) > 10:
        diagnostico["recomendaciones"].append({
            "nivel": "importante",
            "mensaje": f"Se detectaron {metricas_fa['Http5xx']['total']} errores HTTP 5xx",
            "accion": "Revisar logs para identificar causa de errores"
        })

    return diagnostico


@app.function_name(name="diagnostico_recursos_http")
@app.route(route="diagnostico-recursos", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def diagnostico_recursos_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint consolidado para diagnósticos de recursos Azure"""
    logging.info("[ENTRY] diagnostico_recursos_http iniciado")
    
    try:
        from function_app import IS_AZURE, MGMT_SDK, STORAGE_CONNECTION_STRING, CACHE, CONTAINER_NAME, get_blob_client
        from services.memory_service import memory_service
        from memory_manual import aplicar_memoria_manual
        from cosmos_memory_direct import consultar_memoria_cosmos_directo, aplicar_memoria_cosmos_directo
        from function_app import _json, _error, _s, _to_bool, _try_default_credential
        
        logging.info("[OK] Imports completados")
    except Exception as import_err:
        logging.error(f"[FAIL] Error en imports: {import_err}")
        return func.HttpResponse(
            json.dumps({"ok": False, "error": f"Import error: {str(import_err)}"}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
    
    # 🧠 CONSULTAR MEMORIA
    try:
        memoria_previa = consultar_memoria_cosmos_directo(req)
        if memoria_previa and memoria_previa.get("tiene_historial"):
            logging.info(f"🧠 Diagnostico-recursos: {memoria_previa['total_interacciones']} interacciones")
    except Exception as mem_err:
        logging.warning(f"Error consultando memoria: {mem_err}")
        memoria_previa = None
    
    try:
        metricas_param = req.params.get("metricas", "false").lower() == "true"

        # GET con métricas = diagnóstico completo
        if req.method == "GET" and metricas_param:
            logging.info("Ejecutando diagnóstico completo con métricas")
            try:
                diagnostico = diagnosticar_function_app_con_sdk()
                
                # Agregar storage stats
                client = get_blob_client()
                if client:
                    contenedores = list(client.list_containers())
                    total_blobs = sum(sum(1 for _ in client.get_container_client(c.name).list_blobs()) 
                                    for c in contenedores if c.name)
                    
                    diagnostico["recursos"]["storage_stats"] = {
                        "contenedores": len(contenedores),
                        "total_blobs": total_blobs,
                        "contenedor_principal": CONTAINER_NAME
                    }
                
                diagnostico["ok"] = True
                diagnostico["modo"] = "completo_con_metricas"
                
                return func.HttpResponse(
                    json.dumps(diagnostico, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200
                )
            except Exception as e:
                logging.error(f"Error en diagnóstico completo: {str(e)}")
                return func.HttpResponse(
                    json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=500
                )

        if req.method == "GET":
            return func.HttpResponse(
                json.dumps({
                    "ok": True,
                    "message": "Servicio de diagnósticos disponible",
                    "mgmt_sdk_available": MGMT_SDK,
                    "endpoints": {
                        "GET?metricas=true": "Diagnóstico completo con métricas avanzadas",
                        "POST": "Configurar diagnósticos para un recurso"
                    }
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # POST handling
        body = {}
        if req.method == "POST":
            try:
                body_text = req.get_body().decode('utf-8')
                body = json.loads(body_text) if body_text else {}

                # POST con métricas = diagnóstico completo
                if _to_bool(body.get("metricas")):
                    logging.info("Ejecutando diagnóstico completo desde POST")
                    diagnostico = diagnosticar_function_app_con_sdk()
                    diagnostico["ok"] = True
                    diagnostico["modo"] = "completo_post"
                    
                    return func.HttpResponse(
                        json.dumps(diagnostico, ensure_ascii=False),
                        mimetype="application/json",
                        status_code=200
                    )
            except Exception as e:
                logging.error(f"JSON parsing error: {str(e)}")
                body = {}

        rid = _s(body.get("recurso")) if body else ""
        profundidad = _s(body.get("profundidad") or "basico") if body else "basico"

        # Sin recurso específico = diagnóstico general
        if not rid:
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

            try:
                memory_service.log_semantic_event({
                    "tipo": "auditoria_event",
                    "fuente": "diagnostico_recursos_http",
                    "nivel": profundidad,
                    "mensaje": "Diagnóstico general completado",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as audit_err:
                logging.warning(f"Error registrando auditoria: {audit_err}")

            return func.HttpResponse(
                json.dumps(general_diagnostics, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # Diagnóstico de recurso específico
        try:
            if "search" in rid.lower():
                try:
                    from services.azure_search_client import AzureSearchService
                    search_service = AzureSearchService()
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
                    result = {
                        "ok": True,
                        "recurso": rid,
                        "tipo": "Azure AI Search",
                        "profundidad": profundidad,
                        "timestamp": datetime.now().isoformat(),
                        "diagnostico": {"estado": "no_disponible", "error": str(e)}
                    }
            else:
                result = {
                    "ok": True,
                    "recurso": rid,
                    "profundidad": profundidad,
                    "timestamp": datetime.now().isoformat(),
                    "diagnostico": {"estado": "completado", "tipo": "recurso_especifico"}
                }

            try:
                memory_service.log_semantic_event({
                    "tipo": "auditoria_event",
                    "fuente": "diagnostico_recursos_http",
                    "recurso": rid,
                    "nivel": profundidad,
                    "resultado": "completado",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as audit_err:
                logging.warning(f"Error registrando auditoria: {audit_err}")

            result = aplicar_memoria_cosmos_directo(req, result)
            result = aplicar_memoria_manual(req, result)
            
            try:
                memory_service.registrar_llamada(
                    source="diagnostico_recursos",
                    endpoint="/api/diagnostico-recursos",
                    method=req.method,
                    params={"session_id": req.headers.get("Session-ID"), "recurso": rid},
                    response_data=result,
                    success=result.get("ok", False)
                )
            except Exception as reg_err:
                logging.warning(f"Error registrando llamada: {reg_err}")
            
            return _json(result)
        except PermissionError as e:
            return _error("AZURE_AUTH_FORBIDDEN", 403, f"{type(e).__name__}: {str(e)}")
        except Exception as e:
            return _error("DiagError", 500, f"{type(e).__name__}: {str(e)}")

    except Exception as e:
        logging.exception("diagnostico_recursos_http failed")
        return _error("UnexpectedError", 500, f"{type(e).__name__}: {str(e)}")
