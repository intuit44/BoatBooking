"""
Generador de embeddings - Sin decoradores de Azure Functions
"""
import os
import logging
from openai import AzureOpenAI
from typing import Optional, List
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Cliente de OpenAI
if os.getenv("AZURE_OPENAI_KEY"):
    openai_client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version="2024-02-01",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )
    EMBEDDING_MODEL = "text-embedding-3-large"
else:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    openai_client = AzureOpenAI(
        azure_ad_token_provider=token_provider,
        api_version="2024-02-01",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )
    EMBEDDING_MODEL = "text-embedding-3-large"

def generar_embedding(texto: str) -> Optional[List[float]]:
    """Genera embedding usando Azure OpenAI"""
    try:
        response = openai_client.embeddings.create(
            input=texto[:8000],
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"❌ Error generando embedding: {e}")
        return None
