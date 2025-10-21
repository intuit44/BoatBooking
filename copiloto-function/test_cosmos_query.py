#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar query de Cosmos DB
"""

import os
import logging
from typing import List, Dict, Any

def test_cosmos_query():
    """Test directo de la query de Cosmos DB"""
    try:
        from azure.cosmos import CosmosClient
        
        # Configuración
        endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = "agentMemory"
        container_name = "memory"
        
        if not key:
            print("❌ COSMOSDB_KEY no configurada")
            return False
        
        # Conectar
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Query simplificada primero
        simple_query = "SELECT TOP 5 * FROM c WHERE c.agent_id = 'assistant'"
        
        print("🔍 Probando query simple sin parámetros...")
        items = list(container.query_items(
            query=simple_query,
            enable_cross_partition_query=True
        ))
        
        print(f"✅ Query simple: {len(items)} resultados")
        
        # Query con parámetros
        param_query = "SELECT TOP 5 * FROM c WHERE c.agent_id = @agent_id"
        parameters: List[Dict[str, Any]] = [{"name": "@agent_id", "value": "assistant"}]
        
        print("🔍 Probando query con parámetros...")
        print(f"Query: {param_query}")
        print(f"Parameters: {parameters}")
        
        items2 = list(container.query_items(
            query=param_query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        print(f"✅ Query con parámetros: {len(items2)} resultados")
        
        # Query completa
        full_query = """
        SELECT TOP 5 * FROM c 
        WHERE c.agent_id = @agent_id 
        AND c.event_type = 'endpoint_call'
        ORDER BY c._ts DESC
        """
        
        print("🔍 Probando query completa...")
        items3 = list(container.query_items(
            query=full_query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        print(f"✅ Query completa: {len(items3)} resultados")
        
        if items3:
            print("📄 Primer resultado:")
            item = items3[0]
            print(f"  - ID: {item.get('id', 'N/A')}")
            print(f"  - Agent ID: {item.get('agent_id', 'N/A')}")
            print(f"  - Event Type: {item.get('event_type', 'N/A')}")
            print(f"  - Timestamp: {item.get('timestamp', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_cosmos_query()