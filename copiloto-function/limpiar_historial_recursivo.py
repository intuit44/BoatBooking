"""
Script para limpiar interacciones recursivas de historial-interacciones en Cosmos DB
"""
import os
import sys
from azure.cosmos import CosmosClient
from datetime import datetime

def limpiar_historial_recursivo():
    """Elimina o trunca interacciones de historial-interacciones con texto_semantico anidado"""
    
    # Intentar cargar desde local.settings.json
    try:
        import json
        with open("local.settings.json", "r") as f:
            settings = json.load(f)
            values = settings.get("Values", {})
            endpoint = values.get("COSMOS_ENDPOINT") or os.environ.get("COSMOS_ENDPOINT")
            key = values.get("COSMOS_KEY") or os.environ.get("COSMOS_KEY")
            database_name = values.get("COSMOS_DATABASE", "memory")
            container_name = values.get("COSMOS_CONTAINER", "interactions")
    except:
        endpoint = os.environ.get("COSMOS_ENDPOINT")
        key = os.environ.get("COSMOS_KEY")
        database_name = os.environ.get("COSMOS_DATABASE", "memory")
        container_name = os.environ.get("COSMOS_CONTAINER", "interactions")
    
    if not endpoint or not key:
        print("❌ Variables COSMOS_ENDPOINT y COSMOS_KEY requeridas")
        print("💡 Configúralas en local.settings.json o como variables de entorno")
        return
    
    try:
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        print(f"🔍 Conectado a Cosmos: {database_name}/{container_name}")
        
        # Query para encontrar interacciones de historial-interacciones
        query = """
        SELECT * FROM c 
        WHERE c.endpoint = 'historial-interacciones' 
        OR CONTAINS(c.endpoint, 'historial')
        """
        
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        print(f"📊 Encontradas {len(items)} interacciones de historial")
        
        eliminadas = 0
        truncadas = 0
        
        for item in items:
            texto_semantico = item.get("texto_semantico", "")
            
            # Si el texto_semantico es muy largo (>1000 chars), probablemente está anidado
            if len(texto_semantico) > 1000:
                # Opción 1: ELIMINAR la interacción completa
                # container.delete_item(item=item['id'], partition_key=item['session_id'])
                # eliminadas += 1
                
                # Opción 2: TRUNCAR el texto_semantico (más seguro)
                item["texto_semantico"] = "Interacción de historial (truncada por limpieza)"
                container.upsert_item(item)
                truncadas += 1
                
                if truncadas % 10 == 0:
                    print(f"   Procesadas {truncadas} interacciones...")
        
        print(f"\n✅ Limpieza completada:")
        print(f"   - Truncadas: {truncadas}")
        print(f"   - Eliminadas: {eliminadas}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧹 Iniciando limpieza de historial recursivo en Cosmos DB\n")
    limpiar_historial_recursivo()
