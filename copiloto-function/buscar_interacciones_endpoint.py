"""
Endpoint: /api/buscar-interacciones
Búsqueda inteligente de interacciones usando queries dinámicas
"""
import logging
import json
import os
from datetime import datetime
import azure.functions as func
from azure.cosmos import CosmosClient
from semantic_query_builder import construir_query_dinamica, interpretar_intencion_agente, ejecutar_query_cosmos

def register_buscar_interacciones_endpoint(app: func.FunctionApp):
    """Registra el endpoint en la Function App"""
    
    @app.function_name(name="buscar_interacciones")
    @app.route(route="buscar-interacciones", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def buscar_interacciones_http(req: func.HttpRequest) -> func.HttpResponse:
        """Búsqueda inteligente de interacciones con queries dinámicas"""
        try:
            session_id = req.headers.get("Session-ID") or req.params.get("session_id")
            agent_id = req.headers.get("Agent-ID") or req.params.get("agent_id")
            
            if not session_id:
                return func.HttpResponse(
                    json.dumps({"exito": False, "error": "Session-ID requerido"}),
                    mimetype="application/json", status_code=400
                )
            
            try:
                body = req.get_json()
            except:
                body = {}
            
            mensaje_agente = body.get("mensaje") or body.get("query") or req.params.get("query")
            
            if mensaje_agente:
                params = interpretar_intencion_agente(mensaje_agente, dict(req.headers))
                logging.info(f"🧠 Interpretación automática: {mensaje_agente}")
            else:
                params = {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "tipo": body.get("tipo") or req.params.get("tipo"),
                    "contiene": body.get("contiene") or req.params.get("contiene"),
                    "endpoint": body.get("endpoint") or req.params.get("endpoint"),
                    "exito": body.get("exito"),
                    "fecha_inicio": body.get("fecha_inicio") or req.params.get("fecha_inicio"),
                    "fecha_fin": body.get("fecha_fin") or req.params.get("fecha_fin"),
                    "orden": body.get("orden", "desc"),
                    "limite": int(body.get("limite", req.params.get("limite", 20)))
                }
            
            query = construir_query_dinamica(**{k: v for k, v in params.items() if v is not None})
            
            endpoint_cosmos = os.environ.get("COSMOS_ENDPOINT")
            key_cosmos = os.environ.get("COSMOS_KEY")
            
            if not endpoint_cosmos or not key_cosmos:
                return func.HttpResponse(
                    json.dumps({"exito": False, "error": "Cosmos DB no configurado", "query_generada": query}),
                    mimetype="application/json", status_code=500
                )
            
            client = CosmosClient(endpoint_cosmos, key_cosmos)
            database = client.get_database_client(os.environ.get("COSMOS_DATABASE", "memory"))
            container = database.get_container_client(os.environ.get("COSMOS_CONTAINER", "interactions"))
            
            resultados = ejecutar_query_cosmos(query, container)
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "resultados": resultados,
                    "total": len(resultados),
                    "query_ejecutada": query,
                    "parametros_usados": params,
                    "interpretacion": "automática" if mensaje_agente else "explícita",
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )
            
        except Exception as e:
            logging.error(f"❌ Error en buscar-interacciones: {e}")
            return func.HttpResponse(
                json.dumps({"exito": False, "error": str(e), "tipo_error": type(e).__name__}),
                mimetype="application/json", status_code=500
            )
