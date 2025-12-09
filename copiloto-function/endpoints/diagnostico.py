"""
Endpoint: /api/diagnostico
Diagnóstico de sesión + Tests dinámicos de servicios (Redis, Cosmos, Blob, Search, etc.)
"""
from memory_decorator import registrar_memoria
from services.memory_service import memory_service
from semantic_query_builder import construir_query_dinamica, ejecutar_query_cosmos
from function_app import app
import logging
import json
import os
import sys
import time

from datetime import datetime
import azure.functions as func

# Importar el app principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@app.function_name(name="diagnostico")
@app.route(route="diagnostico", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
@registrar_memoria("diagnostico")
def diagnostico_http(req: func.HttpRequest) -> func.HttpResponse:
    """Diagnóstico de sesión + Tests dinámicos de servicios"""
    try:
        # Intentar obtener body
        try:
            body = req.get_json()
        except:
            body = {}

        # 🧪 MODO TEST: Ejecutar pruebas de servicios
        test = body.get("test") or req.params.get("test")
        if test:
            return _ejecutar_test(test, body.get("payload", {}))

        # 📊 MODO DIAGNÓSTICO: Análisis de sesión
        session_id = (
            req.headers.get("Session-ID") or
            req.headers.get("X-Session-ID") or
            req.params.get("session_id") or
            req.params.get("Session-ID")
        )

        # Si no hay session_id ni test, retornar info del servicio
        if not session_id:
            return func.HttpResponse(
                json.dumps({
                    "ok": True,
                    "message": "Servicio de diagnósticos disponible",
                    "modos": {
                        "diagnostico": "GET /api/diagnostico?session_id=xxx",
                        "tests": "POST /api/diagnostico con {\"test\": \"nombre_test\", \"payload\": {...}}"
                    },
                    "tests_disponibles": [
                        "redis_msi", "redis_write", "redis_read",
                        "blob_write", "blob_read", "blob_list",
                        "cosmos_write", "cosmos_read", "cosmos_query",
                        "search_index", "search_query",
                        "openai_embedding", "openai_chat"
                    ]
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )

        # Consultar todas las interacciones de la sesión
        params = {
            "session_id": session_id,
            "fecha_inicio": body.get("fecha_inicio") or req.params.get("fecha_inicio", "últimas 24h"),
            "limite": 100
        }

        query = construir_query_dinamica(**params)
        resultados = ejecutar_query_cosmos(
            query, memory_service.memory_container)

        # Análisis de diagnóstico
        diagnostico = {
            "total_interacciones": len(resultados),
            "exitosas": 0,
            "fallidas": 0,
            "endpoints_usados": {},
            "errores_detectados": [],
            "patrones": []
        }

        for item in resultados:
            exito = item.get("exito", True)
            endpoint = item.get("endpoint", "unknown")
            texto = safe_cosmos_get(item, "texto_semantico") or safe_cosmos_get(
                item, "content") or safe_cosmos_get(item, "message")

            if exito:
                diagnostico["exitosas"] += 1
            else:
                diagnostico["fallidas"] += 1
                diagnostico["errores_detectados"].append({
                    "endpoint": endpoint,
                    "timestamp": item.get("timestamp"),
                    "texto": texto[:100]
                })

            diagnostico["endpoints_usados"][endpoint] = diagnostico["endpoints_usados"].get(
                endpoint, 0) + 1

        # Detectar patrones
        if diagnostico["fallidas"] > diagnostico["exitosas"]:
            diagnostico["patrones"].append("Alta tasa de errores detectada")

        if diagnostico["endpoints_usados"].get("historial-interacciones", 0) > 10:
            diagnostico["patrones"].append(
                "Consultas frecuentes al historial (posible recursión)")

        # Calcular métricas
        tasa_exito = (diagnostico["exitosas"] / diagnostico["total_interacciones"]
                      * 100) if diagnostico["total_interacciones"] > 0 else 0

        diagnostico["metricas"] = {
            "tasa_exito": f"{tasa_exito:.1f}%",
            "tasa_error": f"{(100 - tasa_exito):.1f}%",
            "endpoint_mas_usado": max(diagnostico["endpoints_usados"], key=diagnostico["endpoints_usados"].get) if diagnostico["endpoints_usados"] else "N/A"
        }

        # Recomendaciones
        recomendaciones = []
        if tasa_exito < 50:
            recomendaciones.append(
                "Revisar configuración - tasa de éxito baja")
        if len(diagnostico["errores_detectados"]) > 5:
            recomendaciones.append(
                "Múltiples errores detectados - revisar logs")

        # 🧠 Generar respuesta_usuario para memoria semántica
        respuesta_usuario = f"""DIAGNÓSTICO DE SESIÓN {session_id[:8]}...

📊 Resumen:
- Total interacciones: {diagnostico['total_interacciones']}
- Exitosas: {diagnostico['exitosas']} ({tasa_exito:.1f}%)
- Fallidas: {diagnostico['fallidas']} ({(100-tasa_exito):.1f}%)
- Endpoint más usado: {diagnostico['metricas']['endpoint_mas_usado']}

{f'⚠️ Patrones detectados: ' + ', '.join(diagnostico['patrones']) if diagnostico['patrones'] else '✅ Sin patrones anómalos'}

{f'💡 Recomendaciones: ' + ', '.join(recomendaciones) if recomendaciones else '✅ Sistema funcionando correctamente'}
"""

        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "diagnostico": diagnostico,
                "recomendaciones": recomendaciones,
                "respuesta_usuario": respuesta_usuario,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            mimetype="application/json", status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error en diagnostico: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


def _ejecutar_test(test: str, payload: dict) -> func.HttpResponse:
    """Ejecuta tests dinámicos de servicios sin crear nuevos endpoints"""

    try:

        # ========== REDIS TESTS ==========
        if test in ["redis_msi", "redis_write"]:
            from services.redis_buffer_service import RedisBufferService
            buffer = RedisBufferService()
            key = payload.get("key", "diagnostico:test")
            value = {"status": "ok", "ts": time.time(), "test": test}
            buffer._json_set(key, value, ttl=payload.get("ttl", 60))
            result = buffer._json_get(key)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "key": key, "value": result}),
                mimetype="application/json"
            )

        elif test == "redis_read":
            from services.redis_buffer_service import RedisBufferService
            buffer = RedisBufferService()
            key = payload.get("key", "diagnostico:test")
            result = buffer._json_get(key)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "key": key, "value": result}),
                mimetype="application/json"
            )

        # ========== BLOB TESTS ==========
        elif test == "blob_write":
            from azure.storage.blob import BlobServiceClient
            conn_str = os.getenv("AzureWebJobsStorage")
            if not conn_str:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": "AzureWebJobsStorage not configured"}),
                    mimetype="application/json", status_code=500
                )
            blob_service = BlobServiceClient.from_connection_string(conn_str)
            blob_client = blob_service.get_blob_client(
                container="boat-rental-project",
                blob=payload.get("path", "diagnostico/prueba.txt")
            )
            content = payload.get("content", f"Test {time.time()}")
            blob_client.upload_blob(content, overwrite=True)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "path": blob_client.blob_name}),
                mimetype="application/json"
            )

        elif test == "blob_read":
            from blob_service import BlobService
            blob = BlobService()
            path = payload.get("path", "diagnostico/prueba.txt")
            content = blob.leer_blob(path)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "path": path, "content": content}),
                mimetype="application/json"
            )

        elif test == "blob_list":
            from blob_service import BlobService
            blob = BlobService()
            prefix = payload.get("prefix", "diagnostico/")
            top = payload.get("top", 10)
            files = blob.listar_blobs(prefix, top)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "prefix": prefix, "files": files}),
                mimetype="application/json"
            )

        # ========== COSMOS TESTS ==========
        elif test == "cosmos_write":
            if not memory_service.memory_container:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": "Cosmos DB container not initialized"}),
                    mimetype="application/json", status_code=500
                )
            item = payload.get("item", {
                "id": f"test_{int(time.time())}",
                "tipo": "diagnostico",
                "timestamp": time.time(),
                "session_id": f"diag_{int(time.time())}"
            })
            memory_service.memory_container.create_item(body=item)
            return func.HttpResponse(
                json.dumps({"exito": True, "test": test,
                           "item_id": item["id"]}),
                mimetype="application/json"
            )

        elif test == "cosmos_read":
            if not memory_service.memory_container:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": "Cosmos DB container not initialized"}),
                    mimetype="application/json", status_code=500
                )
            item_id = payload.get("id", "test_item")
            partition_key = payload.get("partition_key", item_id)
            try:
                item = memory_service.memory_container.read_item(
                    item=item_id, partition_key=partition_key)
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test, "item": item}),
                    mimetype="application/json"
                )
            except Exception as read_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"Item not found: {str(read_error)}"}),
                    mimetype="application/json", status_code=404
                )

        elif test == "cosmos_query":
            if not memory_service.memory_container:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": "Cosmos DB container not initialized"}),
                    mimetype="application/json", status_code=500
                )
            query = payload.get(
                "query", "SELECT TOP 5 * FROM c WHERE c.tipo = 'diagnostico' ORDER BY c._ts DESC")
            try:
                items = list(memory_service.memory_container.query_items(
                    query=query, enable_cross_partition_query=True))
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test,
                               "count": len(items), "items": items}),
                    mimetype="application/json"
                )
            except Exception as query_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"Query failed: {str(query_error)}"}),
                    mimetype="application/json", status_code=400
                )

        # ========== SEARCH TESTS ==========
        elif test == "search_index":
            try:
                from azure.search.documents import SearchClient
                from azure.identity import DefaultAzureCredential
                endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
                index = os.getenv("AZURE_SEARCH_INDEX_NAME",
                                  "agent-memory-index")

                if not endpoint:
                    return func.HttpResponse(
                        json.dumps({"exito": False, "test": test,
                                   "error": "AZURE_SEARCH_ENDPOINT not configured"}),
                        mimetype="application/json", status_code=500
                    )

                # Ensure types are plain str for the SearchClient constructor (avoid Optional[str])
                endpoint = str(endpoint)
                index = str(index)

                client = SearchClient(
                    endpoint=endpoint, index_name=index, credential=DefaultAzureCredential())
                stats = client.get_document_count()
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test,
                               "index": index, "document_count": stats}),
                    mimetype="application/json"
                )
            except Exception as search_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"Search service unavailable: {str(search_error)}"}),
                    mimetype="application/json", status_code=500
                )

        elif test == "search_query":
            try:
                from azure.search.documents import SearchClient
                from azure.identity import DefaultAzureCredential
                endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
                index = os.getenv("AZURE_SEARCH_INDEX_NAME",
                                  "agent-memory-index")

                if not endpoint:
                    return func.HttpResponse(
                        json.dumps({"exito": False, "test": test,
                                   "error": "AZURE_SEARCH_ENDPOINT not configured"}),
                        mimetype="application/json", status_code=500
                    )

                client = SearchClient(
                    endpoint=endpoint, index_name=index, credential=DefaultAzureCredential())
                query = payload.get("query", "*")
                results = list(client.search(search_text=query, top=5))
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test, "query": query,
                               "count": len(results), "results": results}),
                    mimetype="application/json"
                )
            except Exception as search_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"Search query failed: {str(search_error)}"}),
                    mimetype="application/json", status_code=500
                )

        # ========== OPENAI TESTS ==========
        elif test == "openai_embedding":
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    api_version="2024-02-01",
                    azure_endpoint=str(
                        os.getenv("AZURE_OPENAI_ENDPOINT") or "")
                )
                text = payload.get("text", "test embedding")
                response = client.embeddings.create(
                    input=text,
                    model=os.getenv("EMBEDDING_MODEL",
                                    "text-embedding-3-large")
                )
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test,
                               "dimensions": len(response.data[0].embedding)}),
                    mimetype="application/json"
                )
            except Exception as openai_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"OpenAI embedding failed: {str(openai_error)}"}),
                    mimetype="application/json", status_code=500
                )

        elif test == "openai_chat":
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    api_version="2024-02-01",
                    azure_endpoint=str(
                        os.getenv("AZURE_OPENAI_ENDPOINT") or "")
                )
                prompt = payload.get("prompt", "Di 'test ok'")
                response = client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50
                )
                return func.HttpResponse(
                    json.dumps({"exito": True, "test": test,
                               "response": response.choices[0].message.content}),
                    mimetype="application/json"
                )
            except Exception as openai_error:
                return func.HttpResponse(
                    json.dumps({"exito": False, "test": test,
                               "error": f"OpenAI chat failed: {str(openai_error)}"}),
                    mimetype="application/json", status_code=500
                )

        # ========== DEFAULT CASE ==========
        else:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": f"Test no soportado: {test}",
                    "tests_disponibles": [
                        "redis_msi", "redis_write", "redis_read",
                        "blob_write", "blob_read", "blob_list",
                        "cosmos_write", "cosmos_read", "cosmos_query",
                        "search_index", "search_query",
                        "openai_embedding", "openai_chat"
                    ]
                }),
                mimetype="application/json",
                status_code=400
            )

    except Exception as e:
        logging.error(f"❌ Error en test {test}: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "test": test, "error": str(e)}),
            mimetype="application/json", status_code=500
        )
