import os
from azure.cosmos import CosmosClient

def verificar_cosmos_containers():
    """Verifica que containers existen en Cosmos DB"""
    try:
        endpoint = os.environ.get("COSMOSDB_ENDPOINT")
        key = os.environ.get("COSMOSDB_KEY")
        
        if not endpoint or not key:
            print("Variables COSMOSDB no configuradas")
            return
            
        client = CosmosClient(endpoint, key)
        db = client.get_database_client("agentMemory")
        
        print("Containers disponibles en agentMemory:")
        containers = list(db.list_containers())
        for container in containers:
            print(f"  - {container['id']}")
        
        # Verificar memory container
        if any(c['id'] == 'memory' for c in containers):
            container = db.get_container_client("memory")
            
            # Buscar documentos semanticos
            query = "SELECT TOP 5 * FROM c WHERE c.categoria = 'semantic_snapshot' ORDER BY c._ts DESC"
            items = list(container.query_items(query, enable_cross_partition_query=True))
            
            print(f"\nDocumentos semanticos en memory: {len(items)}")
            for i, doc in enumerate(items, 1):
                session = doc.get('session_id', 'N/A')
                contenido = str(doc.get('contenido', 'N/A'))[:50]
                print(f"  {i}. {session} | {contenido}...")
                
            if len(items) == 0:
                print("PROBLEMA: No hay documentos semanticos")
                print("La memoria semantica NO se esta persistiendo")
            else:
                print("OK: Memoria semantica encontrada")
        else:
            print("ERROR: Container 'memory' no existe")
            
    except Exception as e:
        print(f"Error: {str(e)[:100]}")

if __name__ == "__main__":
    verificar_cosmos_containers()