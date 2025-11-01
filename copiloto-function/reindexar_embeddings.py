# -*- coding: utf-8 -*-
"""
Reindexa documentos existentes en Azure AI Search con embeddings reales de Azure OpenAI
"""
import os
import json
import logging
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Cargar variables de entorno
search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
search_key = os.environ["AZURE_SEARCH_KEY"]
openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
openai_key = os.environ["AZURE_OPENAI_KEY"]

# Inicializar clientes
search_client = SearchClient(endpoint=search_endpoint, index_name="agent-memory-index",
                             credential=AzureKeyCredential(search_key))
openai_client = AzureOpenAI(
    api_key=openai_key,
    azure_endpoint=openai_endpoint,
    api_version="2024-02-01"
)

def generar_embedding(texto: str):
    """Genera embeddings reales usando Azure OpenAI"""
    try:
        response = openai_client.embeddings.create(
            input=texto[:8000],
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"❌ Error generando embedding: {e}")
        return None

def reindexar_documentos():
    """Reprocesa todos los documentos del índice"""
    print("🔍 Obteniendo documentos existentes...")
    resultados = search_client.search(search_text="*", top=1000)
    actualizados = []

    for doc in resultados:
        texto = doc.get("texto_semantico", "")
        if not texto.strip():
            continue
        
        vector = generar_embedding(texto)
        if vector:
            doc["vector"] = vector
            actualizados.append(doc)
            print(f"✅ Reindexado: {doc['id']} ({len(vector)} dimensiones)")
    
    if actualizados:
        print(f"\n🚀 Subiendo {len(actualizados)} documentos reindexados...")
        result = search_client.upload_documents(documents=actualizados)
        print("Resultado:", result)
    else:
        print("⚠️ No se encontraron documentos con texto válido para reindexar.")

if __name__ == "__main__":
    reindexar_documentos()
