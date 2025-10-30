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
from services.azure_search_client import AzureSearchService  # Cliente centralizado con MSI
from datetime import datetime

# Cliente de OpenAI (embeddings)
openai_client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)

# Cliente de Azure Search (usa Managed Identity automáticamente)
search = AzureSearchService()


def generar_embedding(texto: str) -> Optional[List[float]]:
    """Genera embedding usando Azure OpenAI"""
    try:
        response = openai_client.embeddings.create(
            input=texto[:8000],
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error generando embedding: {e}")
        return None


@func.function_name(name="indexador_semantico")  # type: ignore
@func.queue_trigger(arg_name="msg", queue_name="memory-indexing-queue", connection="AzureWebJobsStorage")  # type: ignore
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
            logging.info(f"⏭️ Evento {doc_id} sin texto semántico suficiente, omitido")
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
            timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        search_doc = {
            "id": doc_id.replace("/", "_"),
            "agent_id": agent_id,
            "session_id": session_id,
            "endpoint": endpoint,
            "timestamp": timestamp_str,
            "tipo": tipo,
            "texto_semantico": texto_semantico[:10000],
            "vector": vector,
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
