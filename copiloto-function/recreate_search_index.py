"""
🔄 Recrear índice Azure AI Search con dimensiones correctas para text-embedding-3-large
"""

import os
import logging
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SimpleField,
    SearchableField
)
from azure.core.credentials import AzureKeyCredential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "agent-memory-index"

if not SEARCH_ENDPOINT or not SEARCH_KEY:
    logging.error("❌ AZURE_SEARCH_ENDPOINT y AZURE_SEARCH_KEY requeridos")
    exit(1)

def recrear_indice():
    """Elimina y recrea el índice con dimensiones 3072"""
    
    logging.info(f"🔄 Recreando índice {INDEX_NAME}...")
    
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # Eliminar índice existente
    try:
        index_client.delete_index(INDEX_NAME)
        logging.info(f"✅ Índice {INDEX_NAME} eliminado")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo eliminar índice: {e}")
    
    # Crear nuevo índice con dimensiones 3072
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
            vector_search_dimensions=3072,  # text-embedding-3-large
            vector_search_profile_name="vector-profile"
        ),
        SimpleField(name="exito", type=SearchFieldDataType.Boolean, filterable=True)
    ]
    
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config"
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-config")
        ]
    )
    
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search
    )
    
    try:
        result = index_client.create_index(index)
        logging.info(f"✅ Índice {INDEX_NAME} creado con dimensiones 3072")
        logging.info(f"📊 Campos: {len(fields)}")
        logging.info(f"🔍 Vector dimensions: 3072 (text-embedding-3-large)")
    except Exception as e:
        logging.error(f"❌ Error creando índice: {e}")

if __name__ == "__main__":
    recrear_indice()
