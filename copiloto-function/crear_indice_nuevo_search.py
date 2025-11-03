#!/usr/bin/env python3
"""
Crea el índice agent-memory-index en el nuevo servicio de búsqueda
"""

import os
import json
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

def crear_indice():
    """Crea el índice en el nuevo servicio"""
    
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "agent-memory-index")
    
    print(f"Endpoint: {endpoint}")
    print(f"Index: {index_name}")
    
    if not endpoint or not key:
        print("ERROR: Configuracion incompleta")
        return False
    
    try:
        # Cliente de índices
        index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        # Definir campos del índice
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="session_id", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="agent_id", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="endpoint", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="texto_semantico", type=SearchFieldDataType.String, searchable=True),
            SimpleField(name="exito", type=SearchFieldDataType.Boolean, filterable=True),
            SearchableField(name="tipo", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True)
        ]
        
        # Crear índice
        index = SearchIndex(
            name=index_name,
            fields=fields
        )
        
        print(f"Creando indice '{index_name}'...")
        result = index_client.create_or_update_index(index)
        
        print(f"Indice creado exitosamente: {result.name}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Creador de Indice en Nuevo Search Service")
    print("=" * 50)
    crear_indice()
