"""
🔧 Actualizar dimensiones del índice de Azure Search a 3072
"""
import sys
import os
import json

# Cargar variables de entorno desde local.settings.json
try:
    with open('local.settings.json') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            os.environ[key] = str(value)
except Exception as e:
    print(f"⚠️ No se pudo cargar local.settings.json: {e}")

sys.path.insert(0, os.path.dirname(__file__))

from services.azure_search_client import AzureSearchService
import logging

logging.basicConfig(level=logging.INFO)

def fix_index():
    """Actualiza el índice para usar 3072 dimensiones"""
    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        key = os.environ.get("AZURE_SEARCH_KEY")
        index_name = "agent-memory-index"
        
        logging.info("🔄 Recreando índice con 3072 dimensiones...")
        
        index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        # Eliminar índice existente
        try:
            index_client.delete_index(index_name)
            logging.info(f"✅ Índice {index_name} eliminado")
        except Exception as e:
            logging.warning(f"⚠️ No se pudo eliminar: {e}")
        
        # Crear nuevo índice con 3072 dimensiones
        from azure.search.documents.indexes.models import (
            SearchIndex, SearchField, SearchFieldDataType,
            VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration,
            SimpleField, SearchableField
        )
        
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
            name=index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        index_client.create_index(index)
        logging.info(f"✅ Índice {index_name} creado con 3072 dimensiones")
        logging.info("🎯 Ahora puedes ejecutar el test nuevamente")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_index()
