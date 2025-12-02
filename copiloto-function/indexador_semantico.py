# -*- coding: utf-8 -*-
"""
Indexador Semántico - Worker que consume cola y genera embeddings
Escucha cambios en Cosmos DB y los indexa en Azure AI Search
"""
import os
import json
import logging
import azure.functions as func
from openai import AzureOpenAI
from typing import Optional, List
# Cliente centralizado con MSI
from services.azure_search_client import AzureSearchService
from datetime import datetime
from services.memory_service import memory_service
# Cliente de OpenAI con Managed Identity
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

if os.getenv("AZURE_OPENAI_KEY"):
    openai_client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version="2024-02-01",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )
    EMBEDDING_MODEL = "text-embedding-3-large"
    logging.info("✅ Usando Azure OpenAI con API Key")
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
    logging.info("✅ Usando Azure OpenAI con Managed Identity")

# Cliente de Azure Search (usa Managed Identity automáticamente)
search = AzureSearchService()


def generar_embedding(texto: str) -> Optional[List[float]]:
    """Genera embedding usando Azure OpenAI o OpenAI directo"""
    try:
        response = openai_client.embeddings.create(
            input=texto[:8000],
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"❌ Error generando embedding: {e}")
        return None


@func.function_name(name="indexador_semantico")
@func.queue_trigger(arg_name="msg", queue_name="memory-indexing-queue", connection="AzureWebJobsStorage")
def indexador_semantico(msg: func.QueueMessage) -> None:
    """Procesa eventos de Cosmos DB y los indexa en Azure AI Search"""
    try:
        evento = json.loads(msg.get_body().decode('utf-8'))
        doc_id = evento.get("id")
        agent_id = evento.get("agent_id", "unknown")
        session_id = evento.get("session_id")
        endpoint = evento.get("endpoint", "unknown")
        timestamp = evento.get("timestamp")
        tipo = evento.get("event_type", "endpoint_call")
        texto_semantico = evento.get("texto_semantico", "")
        exito = evento.get("data", {}).get("success", True)

        # Validar texto semántico
        if not texto_semantico or len(texto_semantico.strip()) < 20:
            palabras = texto_semantico.strip().split()
            if len(palabras) < 3:
                logging.info(
                    f"⏭️ Evento {doc_id} demasiado corto o vacío, omitido")
                return

        # 👇 NUEVO: Verificar duplicado ANTES de generar embedding
        if memory_service.evento_ya_existe(texto_semantico):
            logging.info(
                f"⏭️ Embedding duplicado detectado, se omite generación e indexación para {doc_id}")
            return

        # Generar embedding
        vector = generar_embedding(texto_semantico)
        if not vector:
            logging.warning(f"⚠️ No se pudo generar embedding para {doc_id}")
            return

        # Crear documento para indexación
        # Formato correcto para Edm.DateTimeOffset: YYYY-MM-DDTHH:MM:SS.sssZ
        if isinstance(timestamp, str):
            timestamp_str = timestamp
        else:
            timestamp_str = timestamp.strftime(
                '%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        search_doc = {
            "id": doc_id.replace("/", "_"),
            "agent_id": agent_id,
            "session_id": session_id,
            "endpoint": endpoint,
            "timestamp": timestamp_str,
            "tipo_interaccion": tipo,
            "texto_semantico": texto_semantico[:10000],
            "vector_semantico": vector,
            "exito": exito
        }

        # Enviar a Azure Search
        result = search.indexar_documentos([search_doc])
        if result["exito"]:
            logging.info(f"✅ Indexado: {doc_id} - {agent_id} - {endpoint}")
        else:
            logging.error(f"❌ Error indexando {doc_id}: {result.get('error')}")

    except Exception as e:
        logging.error(f"💥 Error en indexador: {e}")
