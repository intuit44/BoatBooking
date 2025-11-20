#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug Cosmos DB para ver qué hay realmente"""
import os
from azure.cosmos import CosmosClient

endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
key = os.environ.get("COSMOSDB_KEY")
database_name = "agentMemory"
container_name = "memory"

client = CosmosClient(endpoint, key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Query simple sin filtros
query = """
SELECT TOP 10 c.id, c.session_id, c.agent_id, c.endpoint, 
       LENGTH(c.texto_semantico) as texto_len,
       c.texto_semantico
FROM c
WHERE c.session_id = 'session_1759821004'
ORDER BY c._ts DESC
"""

items = list(container.query_items(
    query=query,
    enable_cross_partition_query=True
))

print(f"Total items encontrados: {len(items)}")
for i, item in enumerate(items, 1):
    print(f"\n{i}. ID: {item.get('id')}")
    print(f"   Session: {item.get('session_id')}")
    print(f"   Agent: {item.get('agent_id')}")
    print(f"   Endpoint: {item.get('endpoint')}")
    print(f"   Texto len: {item.get('texto_len')}")
    texto = item.get('texto_semantico', '')
    print(f"   Texto: {texto[:100] if texto else 'VACIO'}...")
