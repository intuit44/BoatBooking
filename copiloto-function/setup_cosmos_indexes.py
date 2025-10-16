# -*- coding: utf-8 -*-
"""
Script para configurar índices optimizados en Cosmos DB
"""
import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential

def setup_optimized_indexes():
    # Cliente Cosmos
    endpoint = os.environ.get('COSMOSDB_ENDPOINT')
    key = os.environ.get('COSMOSDB_KEY')
    
    if not endpoint:
        raise ValueError("COSMOSDB_ENDPOINT environment variable is required")
    
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
        database.replace_container(
            container='fixes',
            partition_key=PartitionKey(path='/estado'),
            indexing_policy=fixes_indexing_policy
        )
        print("✅ Índices optimizados para 'fixes'")
        
        # Actualizar semantic_events container  
        database.replace_container(
            container='semantic_events',
            partition_key=PartitionKey(path='/tipo'),
            indexing_policy=events_indexing_policy
        )
        print("✅ Índices optimizados para 'semantic_events'")
        
    except Exception as e:
        print(f"❌ Error configurando índices: {e}")

if __name__ == "__main__":
    setup_optimized_indexes()