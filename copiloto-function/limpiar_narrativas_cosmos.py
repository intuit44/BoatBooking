"""
Limpia narrativas pre-generadas de Cosmos DB
"""
import os
from azure.cosmos import CosmosClient
from datetime import datetime

# Configuración
COSMOS_ENDPOINT = os.environ.get("COSMOSDB_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOSDB_KEY")
DATABASE_NAME = "agentMemory"
CONTAINER_NAME = "memory"

# Narrativas a eliminar
NARRATIVAS_PROHIBIDAS = [
    "he revisado el historial",
    "encontré",
    "interacciones relevantes",
    "resumen de la última actividad",
    "consulta de historial completada"
]

def limpiar_narrativas():
    """Limpia documentos con narrativas pre-generadas"""
    
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    
    print("🔍 Buscando documentos con narrativas pre-generadas...")
    
    # Query para encontrar documentos con narrativas
    query = "SELECT * FROM c WHERE c.endpoint = 'copiloto' OR c.endpoint = 'historial-interacciones'"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    print(f"📊 Encontrados {len(items)} documentos de copiloto/historial")
    
    eliminados = 0
    actualizados = 0
    
    for item in items:
        texto = item.get("texto_semantico", "").lower()
        
        # Verificar si contiene narrativas prohibidas
        tiene_narrativa = any(n in texto for n in NARRATIVAS_PROHIBIDAS)
        
        if tiene_narrativa:
            print(f"🗑️  Eliminando: {item['id']} - '{texto[:80]}...'")
            container.delete_item(item=item['id'], partition_key=item['session_id'])
            eliminados += 1
    
    print(f"\n✅ Limpieza completada:")
    print(f"   - Eliminados: {eliminados}")
    print(f"   - Total procesados: {len(items)}")

if __name__ == "__main__":
    print("="*60)
    print("🧹 LIMPIEZA DE NARRATIVAS PRE-GENERADAS EN COSMOS DB")
    print("="*60)
    print()
    
    limpiar_narrativas()
    
    print("\n✅ LISTO - Narrativas eliminadas de Cosmos DB")
    print("   Ahora el modelo generará sus propias respuestas")
