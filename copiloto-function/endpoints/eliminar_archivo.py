"""
Endpoint: /api/eliminar-archivo
Elimina archivos de Blob Storage o filesystem local
"""
from function_app import app
import logging
import json
import os
import sys
import glob
from pathlib import Path
from datetime import datetime
import azure.functions as func
from azure.core.exceptions import HttpResponseError

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def _generar_mensaje_no_encontrado(ruta: str, sugerencias: list) -> str:
    """Genera mensaje en lenguaje natural para el agente"""
    if len(sugerencias) == 1:
        return f"El archivo '{ruta}' no existe. Encontré '{sugerencias[0]}'. ¿Quieres usar esa ruta?"
    elif len(sugerencias) > 1:
        primeras = sugerencias[:3]
        lista = "', '".join(primeras)
        return f"El archivo '{ruta}' no existe. Encontré varias opciones: '{lista}'. ¿Cuál quieres usar?"
    else:
        return f"El archivo '{ruta}' no existe y no encontré alternativas similares. Por favor, proporciona la ruta correcta."


def _generar_respuesta_no_encontrado(ruta: str, sugerencias: list) -> dict:
    """Genera respuesta estructurada cuando no se encuentra un archivo"""
    resultado = {
        "sugerencias": sugerencias,
        "accion_recomendada": (
            "proponer_unica" if len(sugerencias) == 1 else "pedir_ruta"
        ),
        "mensaje_agente": _generar_mensaje_no_encontrado(ruta, sugerencias)
    }
    
    if len(sugerencias) == 1:
        resultado["accion_sugerida"] = {
            "endpoint": "/api/eliminar-archivo",
            "http_method": "DELETE",
            "payload": {"ruta": sugerencias[0]}
        }
    
    return resultado


@app.function_name(name="eliminar_archivo_http")
@app.route(route="eliminar-archivo", methods=["POST", "DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def eliminar_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Elimina un archivo del Blob Storage o del filesystem local"""
    from function_app import get_blob_client, CONTAINER_NAME, PROJECT_ROOT
    from memory_manual import aplicar_memoria_manual
    from cosmos_memory_direct import aplicar_memoria_cosmos_directo
    from services.memory_service import memory_service

    try:
        # Parsear body
        try:
            data = req.get_json() or {}
        except ValueError:
            data = {}

        # Extraer ruta
        ruta = (
            data.get("ruta") or data.get("path") or
            req.params.get("ruta") or req.params.get("path") or ""
        ).strip().replace("\\", "/")

        # Validaciones
        if not ruta:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'ruta' es requerido",
                    "ejemplo": {"ruta": "docs/archivo.txt"}
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        # Normalizar ruta absoluta a relativa si es necesario
        if ":" in ruta or ruta.startswith("/"):
            try:
                ruta_path = Path(ruta)
                if ruta_path.is_absolute():
                    # Intentar hacer relativa a PROJECT_ROOT
                    try:
                        ruta = str(ruta_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                    except ValueError:
                        # Si no está dentro de PROJECT_ROOT, usar la ruta tal cual
                        pass
            except Exception:
                pass

        if ".." in ruta.split("/"):
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Ruta inválida: no se permiten referencias a directorios padre"
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        # Detectar si es un patrón glob
        es_patron = "*" in ruta or "?" in ruta
        
        archivo_encontrado = False
        resultado = None
        intentos = []
        archivos_eliminados = []

        # 1️⃣ Intentar eliminar en Blob Storage
        client = get_blob_client()
        if client:
            try:
                container = client.get_container_client(CONTAINER_NAME)
                blob = container.get_blob_client(ruta)

                if blob.exists():
                    archivo_encontrado = True
                    blob.delete_blob(delete_snapshots="include")
                    resultado = {
                        "exito": True,
                        "mensaje": f"Archivo '{ruta}' eliminado de Blob Storage",
                        "ubicacion": f"blob://{CONTAINER_NAME}/{ruta}",
                        "tipo": "blob"
                    }
                    intentos.append("blob_storage_exitoso")
                else:
                    intentos.append("blob_storage_no_encontrado")
            except HttpResponseError as e:
                intentos.append(f"blob_storage_error: {str(e)[:50]}")
                logging.warning(f"Error en Blob Storage: {e}")
            except Exception as e:
                intentos.append(f"blob_storage_exception: {str(e)[:50]}")
                logging.warning(f"Error inesperado en Blob: {e}")

        # 2️⃣ Intentar eliminar localmente
        if not resultado:
            try:
                ruta_base = Path(ruta)
                if not ruta_base.is_absolute():
                    ruta_base = PROJECT_ROOT / ruta
                
                if es_patron:
                    archivos_encontrados = glob.glob(str(ruta_base), recursive=False)
                    logging.info(f"🔍 Patrón: {ruta_base} → {len(archivos_encontrados)} encontrados")
                    
                    if archivos_encontrados:
                        for archivo_path in archivos_encontrados:
                            archivo_obj = Path(archivo_path)
                            if archivo_obj.is_file():
                                nombre_archivo = archivo_obj.name
                                try:
                                    archivo_obj.unlink()
                                    archivo_encontrado = True
                                    archivos_eliminados.append(nombre_archivo)
                                    logging.info(f"✅ Eliminado: {nombre_archivo}")
                                except PermissionError as e:
                                    logging.warning(f"❌ Sin permisos: {nombre_archivo}")
                                except Exception as e:
                                    logging.warning(f"❌ Error: {nombre_archivo} - {str(e)[:50]}")
                        
                        if archivos_eliminados:
                            resultado = {
                                "exito": True,
                                "mensaje": f"Eliminados {len(archivos_eliminados)} archivos que coinciden con '{ruta}'",
                                "archivos_eliminados": archivos_eliminados,
                                "total": len(archivos_eliminados),
                                "tipo": "local_patron"
                            }
                            intentos.append(f"local_patron_exitoso_{len(archivos_eliminados)}")
                        else:
                            intentos.append("local_patron_sin_archivos_validos")
                    else:
                        intentos.append("local_patron_no_encontrado")
                else:
                    if ruta_base.exists():
                        if ruta_base.is_file():
                            nombre_archivo = ruta_base.name
                            try:
                                ruta_base.unlink()
                                archivo_encontrado = True
                                archivos_eliminados.append(nombre_archivo)
                                resultado = {
                                    "exito": True,
                                    "mensaje": f"Archivo '{nombre_archivo}' eliminado localmente",
                                    "ubicacion": str(ruta_base),
                                    "tipo": "local"
                                }
                                intentos.append("local_exitoso")
                            except Exception as e:
                                logging.warning(f"Error eliminando {nombre_archivo}: {e}")
                                intentos.append(f"local_error: {str(e)[:50]}")
                        else:
                            intentos.append("local_es_directorio")
                    else:
                        intentos.append("local_no_encontrado")
            except Exception as e:
                intentos.append(f"local_error: {str(e)[:50]}")
                logging.warning(f"Error eliminando archivo local: {e}")

        # 3️⃣ Si no se encontró el archivo
        if not archivo_encontrado:
            # Buscar archivos similares en Blob y localmente
            sugerencias = []
            
            # Buscar en Blob Storage
            try:
                if client:
                    container = client.get_container_client(CONTAINER_NAME)
                    nombre_base = os.path.basename(ruta)
                    for blob in container.list_blobs():
                        if nombre_base.lower() in blob.name.lower():
                            sugerencias.append(f"blob://{blob.name}")
                            if len(sugerencias) >= 5:
                                break
            except Exception:
                pass
            
            # Buscar localmente
            try:
                archivo_local = Path(ruta)
                if not archivo_local.is_absolute():
                    archivo_local = PROJECT_ROOT / ruta
                
                # Buscar en el directorio padre
                if archivo_local.parent.exists():
                    nombre_base = archivo_local.name
                    for archivo in archivo_local.parent.iterdir():
                        if archivo.is_file() and nombre_base.lower() in archivo.name.lower():
                            sugerencias.append(str(archivo.relative_to(PROJECT_ROOT)))
                            if len(sugerencias) >= 10:
                                break
            except Exception as e:
                logging.warning(f"Error buscando archivos similares localmente: {e}")

            mensaje_error = f"Patrón '{ruta}' no encontró archivos" if es_patron else f"Archivo '{ruta}' no encontrado"
            resultado = {
                "exito": False,
                "error": mensaje_error,
                "intentos": intentos,
                "es_patron": es_patron
            }
            resultado.update(_generar_respuesta_no_encontrado(ruta, sugerencias))

        # Enriquecer respuesta
        if resultado:
            resultado["timestamp"] = datetime.now().isoformat()
            resultado["ruta_solicitada"] = ruta
            resultado["intentos_realizados"] = intentos
            resultado["es_patron"] = es_patron
            if archivos_eliminados:
                resultado["archivos_eliminados"] = archivos_eliminados
        else:
            resultado = {
                "exito": False,
                "error": "Error inesperado procesando solicitud",
                "timestamp": datetime.now().isoformat(),
                "ruta_solicitada": ruta,
                "intentos_realizados": intentos,
                "es_patron": es_patron
            }

        # Aplicar memoria
        resultado = aplicar_memoria_cosmos_directo(req, resultado)
        resultado = aplicar_memoria_manual(req, resultado)

        # Registrar en memoria
        try:
            memory_service.registrar_llamada(
                source="eliminar_archivo",
                endpoint="/api/eliminar-archivo",
                method=req.method,
                params={
                    "ruta": ruta,
                    "session_id": req.headers.get("Session-ID"),
                    "agent_id": req.headers.get("Agent-ID")
                },
                response_data=resultado,
                success=resultado.get("exito", False)
            )
        except Exception as e:
            logging.warning(f"Error registrando en memoria: {e}")

        # Siempre devolver 200 para que el agente pueda procesar la respuesta
        return func.HttpResponse(
            json.dumps(resultado, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception("eliminar_archivo_http failed")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
