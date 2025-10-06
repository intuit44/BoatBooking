# -*- coding: utf-8 -*-
"""
Script para configurar índices optimizados en Cosmos DB
"""
import os
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

def setup_optimized_indexes():
    # Cliente Cosmos
    endpoint = os.environ.get('COSMOSDB_ENDPOINT')
    key = os.environ.get('COSMOSDB_KEY')
    
    if key:
        client = CosmosClient(endpoint, key)
    else:
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)
    
    database = client.get_database_client('agentMemory')
    
    # Política de indexación optimizada para fixes
    fixes_indexing_policy = {
        "indexingMode": "consistent",
        "includedPaths": [
            {"path": "/id/?"},
            {"path": "/estado/?"},
            {"path": "/prioridad/?"},
            {"path": "/target/?"},
            {"path": "/timestamp/?"},
            {"path": "/run_id/?"},
            {"path": "/idempotencyKey/?"}
        ],
        "excludedPaths": [
            {"path": "/*"},
            {"path": "/\"_etag\"/?"}
        ]
    }
    
    # Política para semantic_events
    events_indexing_policy = {
        "indexingMode": "consistent", 
        "includedPaths": [
            {"path": "/id/?"},
            {"path": "/tipo/?"},
            {"path": "/timestamp/?"},
            {"path": "/data/run_id/?"}
        ],
        "excludedPaths": [
            {"path": "/*"},
            {"path": "/\"_etag\"/?"}
        ]
    }
    
    try:
        # Actualizar fixes container
        fixes_container = database.get_container_client('fixes')
        fixes_container.replace_container(
            partition_key='/estado',
            indexing_policy=fixes_indexing_policy
        )
        print("✅ Índices optimizados para 'fixes'")
        
        # Actualizar semantic_events container  
        events_container = database.get_container_client('semantic_events')
        events_container.replace_container(
            partition_key='/tipo',
            indexing_policy=events_indexing_policy
        )
        print("✅ Índices optimizados para 'semantic_events'")
        
    except Exception as e:
        print(f"❌ Error configurando índices: {e}")

if __name__ == "__main__":
    setup_optimized_indexes()