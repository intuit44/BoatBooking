"""
🔄 Reset completo: Recrear índice y migrar solo documentos recientes
"""

import os
import logging
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, VectorSearch,
    VectorSearchProfile, HnswAlgorithmConfiguration, SimpleField, SearchableField
)
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración
COSMOS_ENDPOINT = os.getenv("COSMOSDB_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOSDB_KEY")
COSMOS_DATABASE = "agentMemory"
COSMOS_CONTAINER = "memory"

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "agent-memory-index"

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

# Configuración: migrar solo últimos N días
DIAS_A_MIGRAR = 2  # Solo 2 días para tier Free
MAX_DOCUMENTOS = 100  # Límite máximo de documentos
VECTOR_DIMENSIONS = 1536  # Reducir dimensiones para tier Free (en lugar de 3072)

def recrear_indice():
    """Elimina y recrea el índice vacío"""
    logging.info("🔄 Recreando índice...")
    
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    try:
        index_client.delete_index(INDEX_NAME)
        logging.info(f"✅ Índice {INDEX_NAME} eliminado")
    except:
        pass
    
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="agent_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="session_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="endpoint", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SearchableField(name="tipo", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="texto_semantico", type=SearchFieldDataType.String),
        SearchField(
            name="vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="vector-profile"
        ),
        SimpleField(name="exito", type=SearchFieldDataType.Boolean, filterable=True)
    ]
    
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")],
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")]
    )
    
    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    index_client.create_index(index)
    logging.info(f"✅ Índice recreado con dimensiones {VECTOR_DIMENSIONS}")

def migrar_documentos_recientes():
    """Migra solo documentos de los últimos DIAS_A_MIGRAR días"""
    logging.info(f"📊 Migrando documentos de últimos {DIAS_A_MIGRAR} días...")
    
    # Clientes
    cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = cosmos_client.get_database_client(COSMOS_DATABASE)
    container = database.get_container_client(COSMOS_CONTAINER)
    
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version="2024-02-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Fecha límite
    fecha_limite = datetime.utcnow() - timedelta(days=DIAS_A_MIGRAR)
    timestamp_limite = int(fecha_limite.timestamp())
    
    # Query solo documentos recientes con límite
    query = f"SELECT TOP {MAX_DOCUMENTOS} * FROM c WHERE c._ts >= {timestamp_limite} ORDER BY c._ts DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    logging.info(f"📊 Documentos recientes encontrados: {len(items)} (máx: {MAX_DOCUMENTOS})")
    
    indexados = 0
    errores = 0
    
    for item in items:
        try:
            texto = item.get("texto_semantico") or item.get("comando") or item.get("mensaje") or ""
            
            if len(texto.strip()) < 5:
                continue
            
            # Generar embedding con dimensiones reducidas
            response = openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=texto,
                dimensions=VECTOR_DIMENSIONS  # Reducir dimensiones
            )
            vector = response.data[0].embedding
            
            # Preparar documento
            timestamp = item.get("timestamp", datetime.utcnow().isoformat())
            if isinstance(timestamp, str) and not timestamp.endswith('Z'):
                timestamp = timestamp.split('.')[0] + 'Z'
            
            doc = {
                "id": item.get("id"),
                "agent_id": item.get("agent_id", "unknown"),
                "session_id": item.get("session_id", "unknown"),
                "endpoint": item.get("endpoint", ""),
                "timestamp": timestamp,
                "tipo": item.get("tipo", "memoria"),
                "texto_semantico": texto,
                "vector": vector,
                "exito": item.get("exito", True)
            }
            
            # Indexar
            result = search_client.upload_documents(documents=[doc])
            
            if result[0].succeeded:
                indexados += 1
                if indexados % 10 == 0:
                    logging.info(f"✅ Indexados: {indexados}")
            else:
                errores += 1
                
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            errores += 1
    
    logging.info(f"""
    ✅ Migración completada
    📊 Indexados: {indexados}/{MAX_DOCUMENTOS}
    ❌ Errores: {errores}
    📅 Período: Últimos {DIAS_A_MIGRAR} días
    """)

if __name__ == "__main__":
    recrear_indice()
    migrar_documentos_recientes()
