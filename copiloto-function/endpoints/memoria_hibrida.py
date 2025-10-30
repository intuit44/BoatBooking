"""
Endpoint de Memoria Híbrida - Combina Cosmos DB + Azure AI Search
Detecta intención y usa la fuente óptima
"""
import azure.functions as func
import json
import logging
import os
from datetime import datetime
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from function_app import app
from services.memory_service import memory_service
from semantic_query_builder import construir_query_dinamica, ejecutar_query_cosmos

# Clientes
openai_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
)

search_client = SearchClient(
    endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
    index_name="agent-memory-index",
    credential=AzureKeyCredential(os.environ.get("AZURE_SEARCH_KEY"))
)

def detectar_intencion(query: str) -> str:
    """Detecta si la consulta es estructurada o semántica"""
    query_lower = query.lower()
    
    # Estructurada: filtros explícitos
    if any(k in query_lower for k in ["últimas", "desde", "endpoint", "exito=", "fecha"]):
        return "estructurada"
    
    # Semántica: preguntas libres
    if any(k in query_lower for k in ["qué", "cómo", "cuándo", "sobre", "relacionado", "hablamos"]):
        return "semantica"
    
    return "semantica"  # Por defecto

def buscar_semantico(query: str, agent_id: str, limit: int = 10) -> list:
    """Búsqueda vectorial en Azure AI Search"""
    try:
        # Generar embedding de la query
        response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-large"
        )
        query_vector = response.data[0].embedding
        
        # Búsqueda vectorial con filtros
        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "vector": query_vector,
                "k_nearest_neighbors": limit,
                "fields": "vector"
            }],
            filter=f"agent_id eq '{agent_id}'",
            select=["id", "agent_id", "endpoint", "timestamp", "texto_semantico"],
            top=limit
        )
        
        return [
            {
                "id": r["id"],
                "endpoint": r["endpoint"],
                "timestamp": r["timestamp"],
                "texto_semantico": r["texto_semantico"],
                "score": r["@search.score"],
                "fuente": "ai_search"
            }
            for r in results
        ]
    except Exception as e:
        logging.error(f"Error en búsqueda semántica: {e}")
        return []

@app.function_name(name="memoria_hibrida")
@app.route(route="memoria-hibrida", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def memoria_hibrida(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint híbrido que combina Cosmos DB + Azure AI Search
    
    GET /api/memoria-hibrida?query=qué hablamos sobre queries&agent_id=Agent914
    """
    try:
        # Extraer parámetros
        query = req.params.get("query") or req.params.get("q", "")
        agent_id = req.headers.get("Agent-ID") or req.params.get("agent_id", "GlobalAgent")
        limit = int(req.params.get("limit", "10"))
        
        if not query:
            return func.HttpResponse(
                json.dumps({"error": "Parámetro 'query' requerido"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Detectar intención
        intencion = detectar_intencion(query)
        logging.info(f"🎯 Intención detectada: {intencion}")
        
        resultados = []
        
        if intencion == "semantica":
            # Búsqueda vectorial en AI Search
            resultados = buscar_semantico(query, agent_id, limit)
            fuente = "Azure AI Search (vectorial)"
        else:
            # Búsqueda estructurada en Cosmos DB
            from semantic_query_builder import interpretar_intencion_agente
            params = interpretar_intencion_agente(query, dict(req.headers))
            params["agent_id"] = agent_id
            params["limite"] = limit
            
            query_sql = construir_query_dinamica(**params)
            items = ejecutar_query_cosmos(query_sql, memory_service.memory_container)
            
            resultados = [
                {
                    "id": item["id"],
                    "endpoint": item["endpoint"],
                    "timestamp": item["timestamp"],
                    "texto_semantico": item["texto_semantico"],
                    "fuente": "cosmos_db"
                }
                for item in items
            ]
            fuente = "Cosmos DB (SQL)"
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "query": query,
                "intencion": intencion,
                "fuente": fuente,
                "total": len(resultados),
                "resultados": resultados
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error en memoria híbrida: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
