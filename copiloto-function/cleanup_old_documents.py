"""
🧹 Limpieza de documentos antiguos en Azure AI Search
Elimina documentos con timestamp anterior a N días
"""

import os
import logging
from datetime import datetime, timedelta
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "agent-memory-index"

# Configuración: mantener solo últimos N días
DIAS_A_MANTENER = 5

def limpiar_documentos_antiguos():
    """Elimina documentos con más de DIAS_A_MANTENER días"""
    
    logging.info(f"🧹 Limpiando documentos anteriores a {DIAS_A_MANTENER} días...")
    
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # Calcular fecha límite
    fecha_limite = datetime.utcnow() - timedelta(days=DIAS_A_MANTENER)
    fecha_limite_str = fecha_limite.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    logging.info(f"📅 Fecha límite: {fecha_limite_str}")
    
    # Buscar documentos antiguos
    try:
        # Azure Search requiere formato ISO sin comillas para DateTimeOffset
        results = search_client.search(
            search_text="*",
            filter=f"timestamp lt {fecha_limite_str}",
            select="id,timestamp",
            top=50000
        )
        
        docs_to_delete = []
        for doc in results:
            docs_to_delete.append({"id": doc["id"]})
        
        logging.info(f"📊 Documentos a eliminar: {len(docs_to_delete)}")
        
        if not docs_to_delete:
            logging.info("✅ No hay documentos antiguos para eliminar")
            return
        
        # Eliminar en lotes de 1000
        batch_size = 1000
        total_eliminados = 0
        
        for i in range(0, len(docs_to_delete), batch_size):
            batch = docs_to_delete[i:i+batch_size]
            result = search_client.delete_documents(documents=batch)
            
            eliminados = sum(1 for r in result if r.succeeded)
            total_eliminados += eliminados
            
            logging.info(f"🗑️ Eliminados: {eliminados}/{len(batch)} (Total: {total_eliminados})")
        
        logging.info(f"✅ Limpieza completada: {total_eliminados} documentos eliminados")
        
    except Exception as e:
        logging.error(f"❌ Error en limpieza: {e}")

if __name__ == "__main__":
    limpiar_documentos_antiguos()
