"""
Elimina TODAS las interacciones de la sesión 'assistant' en Cosmos DB
"""
import os
from azure.cosmos import CosmosClient

endpoint_url = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
key = os.environ.get("COSMOSDB_KEY")
database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
container_name = "memory"

if not key:
    print("❌ COSMOSDB_KEY no configurada")
    exit(1)

client = CosmosClient(endpoint_url, key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Eliminar TODAS las interacciones de la sesión assistant
query = "SELECT * FROM c WHERE c.session_id = 'assistant'"
items = list(container.query_items(query=query, enable_cross_partition_query=True))

print(f"🔍 Encontradas {len(items)} interacciones totales para session_id='assistant'")

if len(items) == 0:
    print("✅ No hay interacciones para eliminar")
    exit(0)

eliminadas = 0
for item in items:
    try:
        container.delete_item(item=item['id'], partition_key=item['session_id'])
        eliminadas += 1
        if eliminadas % 10 == 0:
            print(f"🗑️  Eliminadas {eliminadas}/{len(items)}...")
    except Exception as e:
        print(f"⚠️  Error eliminando {item['id']}: {e}")

print(f"\n✅ Limpieza completada: {eliminadas}/{len(items)} interacciones eliminadas")
print("🔄 Ahora reinicia el servidor y prueba nuevamente")
