# -*- coding: utf-8 -*-
"""
Endpoints adicionales para consultar memoria
"""
import azure.functions as func
import json
from datetime import datetime
from services.memory_service import memory_service

app = func.FunctionApp()

@app.function_name(name="consultar_memoria")
@app.route(route="memoria", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def consultar_memoria(req: func.HttpRequest) -> func.HttpResponse:
    """Consulta interacciones recientes en memoria"""
    try:
        agent_id = req.params.get("agent_id")
        limit = int(req.params.get("limit", "10"))
        
        if agent_id:
            # Buscar por agente específico
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential
            import os
            
            endpoint = os.environ.get('COSMOSDB_ENDPOINT')
            key = os.environ.get('COSMOSDB_KEY')
            
            if key:
                client = CosmosClient(endpoint, key)
            else:
                client = CosmosClient(endpoint, DefaultAzureCredential())
            
            db = client.get_database_client('agentMemory')
            container = db.get_container_client('memory')
            
            query = "SELECT * FROM c WHERE c.data.agent_id = @agent_id ORDER BY c._ts DESC"
            items = list(container.query_items(
                query,
                parameters=[{"name": "@agent_id", "value": agent_id}],
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
        else:
            # Buscar todas las interacciones recientes
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential
            import os
            
            endpoint = os.environ.get('COSMOSDB_ENDPOINT')
            key = os.environ.get('COSMOSDB_KEY')
            
            if key:
                client = CosmosClient(endpoint, key)
            else:
                client = CosmosClient(endpoint, DefaultAzureCredential())
            
            db = client.get_database_client('agentMemory')
            container = db.get_container_client('memory')
            
            query = f"SELECT TOP {limit} * FROM c ORDER BY c._ts DESC"
            items = list(container.query_items(
                query,
                enable_cross_partition_query=True
            ))
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "interacciones": items,
                "total": len(items),
                "filtro_agente": agent_id,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }),
            mimetype="application/json",
            status_code=500
        )

@app.function_name(name="estadisticas_memoria")
@app.route(route="memoria/stats", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def estadisticas_memoria(req: func.HttpRequest) -> func.HttpResponse:
    """Estadísticas de uso de memoria"""
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        import os
        
        endpoint = os.environ.get('COSMOSDB_ENDPOINT')
        key = os.environ.get('COSMOSDB_KEY')
        
        if key:
            client = CosmosClient(endpoint, key)
        else:
            client = CosmosClient(endpoint, DefaultAzureCredential())
        
        db = client.get_database_client('agentMemory')
        container = db.get_container_client('memory')
        
        # Estadísticas por agente
        query_agents = """
        SELECT c.data.agent_id as agent_id, COUNT(1) as count
        FROM c 
        WHERE c.event_type = 'agent_interaction'
        GROUP BY c.data.agent_id
        """
        
        agents_stats = list(container.query_items(
            query_agents,
            enable_cross_partition_query=True
        ))
        
        # Estadísticas por fuente
        query_sources = """
        SELECT c.data.source as source, COUNT(1) as count
        FROM c
        WHERE c.event_type = 'agent_interaction'
        GROUP BY c.data.source
        """
        
        sources_stats = list(container.query_items(
            query_sources,
            enable_cross_partition_query=True
        ))
        
        # Total de interacciones
        query_total = "SELECT VALUE COUNT(1) FROM c WHERE c.event_type = 'agent_interaction'"
        total_interactions = list(container.query_items(
            query_total,
            enable_cross_partition_query=True
        ))[0] if container.query_items(query_total, enable_cross_partition_query=True) else 0
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "estadisticas": {
                    "total_interacciones": total_interactions,
                    "por_agente": agents_stats,
                    "por_fuente": sources_stats
                },
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }),
            mimetype="application/json",
            status_code=500
        )