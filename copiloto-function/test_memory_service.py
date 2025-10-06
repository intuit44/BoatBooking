# -*- coding: utf-8 -*-
"""
Test del memory_service con Cosmos DB
"""
from dotenv import load_dotenv
load_dotenv()

from services.memory_service import memory_service
import json

def test_memory_service():
    print("TESTING MEMORY SERVICE")
    print("=" * 40)
    
    # Test 1: Registrar interacción
    print("\n1. Registrando interacción de agente...")
    success = memory_service.record_interaction(
        agent_id="AI-FOUNDATION",
        source="test_script",
        input_data={"action": "test", "data": "sample"},
        output_data={"result": "success", "message": "Test completed"}
    )
    print(f"Resultado: {'✅ Guardado' if success else '❌ Error'}")
    
    # Test 2: Log evento semántico
    print("\n2. Registrando evento semántico...")
    success = memory_service.log_event("test_event", {
        "description": "Test event from script",
        "priority": "high"
    })
    print(f"Resultado: {'✅ Guardado' if success else '❌ Error'}")
    
    print("\n3. Para verificar en Cosmos DB, ejecuta:")
    print("python -c \"")
    print("from services.memory_service import memory_service")
    print("from azure.cosmos import CosmosClient")
    print("from azure.identity import DefaultAzureCredential")
    print("import os")
    print("")
    print("# Conectar a Cosmos")
    print("endpoint = os.environ.get('COSMOSDB_ENDPOINT')")
    print("key = os.environ.get('COSMOSDB_KEY')")
    print("if key:")
    print("    client = CosmosClient(endpoint, key)")
    print("else:")
    print("    client = CosmosClient(endpoint, DefaultAzureCredential())")
    print("")
    print("db = client.get_database_client('agentMemory')")
    print("container = db.get_container_client('memory')")
    print("")
    print("# Consultar últimos registros")
    print("for doc in container.query_items(")
    print("    query='SELECT TOP 5 c.id, c.agent_id, c.source, c.timestamp FROM c ORDER BY c._ts DESC',")
    print("    enable_cross_partition_query=True")
    print("):")
    print("    print(doc)")
    print("\"")

if __name__ == "__main__":
    test_memory_service()