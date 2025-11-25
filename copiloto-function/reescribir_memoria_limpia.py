"""
Script para limpiar Cosmos y reindexar Azure AI Search con datos curados.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List

from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from openai import AzureOpenAI


def load_settings() -> Dict[str, Any]:
    try:
        with open("local.settings.json", "r", encoding="utf-8") as handle:
            return json.load(handle)["Values"]
    except Exception:
        return os.environ.copy()


def require(value: str | None, message: str) -> str:
    if not value:
        raise RuntimeError(message)
    return value


settings = load_settings()

cosmos_endpoint = require(
    settings.get("COSMOSDB_ENDPOINT") or settings.get("COSMOS_ENDPOINT"),
    "Faltan COSMOSDB_ENDPOINT/COSMOS_ENDPOINT.",
)
cosmos_key = require(
    settings.get("COSMOSDB_KEY") or settings.get("COSMOS_KEY"),
    "Faltan COSMOSDB_KEY/COSMOS_KEY.",
)
database_name = settings.get("COSMOSDB_DATABASE", "agentMemory")
container_name = settings.get("COSMOSDB_CONTAINER", "memory")

cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
container = cosmos_client.get_database_client(
    database_name).get_container_client(container_name)

search_endpoint = require(settings.get(
    "AZURE_SEARCH_ENDPOINT"), "Falta AZURE_SEARCH_ENDPOINT.")
search_key = require(settings.get("AZURE_SEARCH_KEY"),
                     "Falta AZURE_SEARCH_KEY.")
search_index = settings.get("AZURE_SEARCH_INDEX", "agent-memory-index")

openai_key = require(settings.get("AZURE_OPENAI_KEY"),
                     "Falta AZURE_OPENAI_KEY.")
openai_endpoint = require(settings.get(
    "AZURE_OPENAI_ENDPOINT"), "Falta AZURE_OPENAI_ENDPOINT.")

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=search_index,
    credential=AzureKeyCredential(search_key),
)

openai_client = AzureOpenAI(
    api_key=openai_key,
    api_version="2024-02-01",
    azure_endpoint=openai_endpoint,
)

ENDPOINTS_NOISE = {
    "historial-interacciones",
    "/api/historial-interacciones",
    "diagnostico",
    "diagnostico_recursos",
    "precalentar-memoria",
    "status",
    "health",
    "introspection",
    "guardar-memoria",
    "copiloto",
    "memoria-global",
    "memoria_global",
}
EVENT_TYPES_NOISE = {
    "snapshot",
    "meta_error",
    "system_log",
    "conversation_snapshot",
}
TEXT_NOISE = ("No se pudo", "Sesion estable", "Thread:",
              "assistant-", "sin novedades recientes")

ENDPOINTS_COGNITIVE = [
    "ejecutar-cli",
    "escribir-archivo",
    "leer-archivo",
    "crear-contenedor",
    "actualizar-configuracion",
    "desplegar",
]


def delete_noise() -> None:
    print("== Paso 1: Eliminando documentos con ruido ==")
    query = """
    SELECT c.id, c.session_id
    FROM c
    WHERE ARRAY_CONTAINS(@noiseEndpoints, c.endpoint, true)
       OR ARRAY_CONTAINS(@noiseEvents, c.event_type, true)
       OR STARTSWITH(c.session_id, @prefixConstant)
       OR STARTSWITH(c.session_id, @prefixUniversal)
       OR STARTSWITH(c.id, @prefixConstantId)
       OR ARRAY_CONTAINS(@sessionesRuido, c.session_id, true)
       OR (IS_DEFINED(c.texto_semantico) AND (
            CONTAINS(c.texto_semantico, @noiseA) OR
            CONTAINS(c.texto_semantico, @noiseB) OR
            CONTAINS(c.texto_semantico, @noiseC) OR
            CONTAINS(c.texto_semantico, @noiseD)
            OR CONTAINS(c.texto_semantico, @noiseE)
       ))
    """
    parameters = [
        {"name": "@noiseEndpoints", "value": list(ENDPOINTS_NOISE)},
        {"name": "@noiseEvents", "value": list(EVENT_TYPES_NOISE)},
        {"name": "@noiseA", "value": TEXT_NOISE[0]},
        {"name": "@noiseB", "value": TEXT_NOISE[1]},
        {"name": "@noiseC", "value": TEXT_NOISE[2]},
        {"name": "@noiseD", "value": TEXT_NOISE[3]},
        {"name": "@noiseE", "value": TEXT_NOISE[4]},
        {"name": "@prefixConstant", "value": "constant-session-id"},
        {"name": "@prefixUniversal", "value": "universal_session"},
        {"name": "@prefixConstantId", "value": "constant-session-id_"},
        {"name": "@sessionesRuido", "value": ["constant-session-id", "universal_session", "fallback_session"]},
    ]
    docs = list(container.query_items(
        query, parameters=parameters, enable_cross_partition_query=True))
    print(f"  Encontrados {len(docs)} documentos para eliminar.")
    for index, doc in enumerate(docs, start=1):
        container.delete_item(doc["id"], partition_key=doc["session_id"])
        if len(docs) < 50 or index % 50 == 0:
            print(f"  Eliminados {index}/{len(docs)}")
    print(f"== Eliminacion completada ({len(docs)} documentos). ==\n")


def clean_text(texto: str) -> str:
    if not texto:
        return ""
    lines = [
        line.strip()
        for line in texto.split("\n")
        if not any(token.lower() in line.lower() for token in ("thread:", "assistant-", "ruta_blob", "blob:"))
    ]
    joined = " ".join(line for line in lines if line)
    return joined[:600]


def cure_documents() -> None:
    print("== Paso 2: Curando documentos utiles ==")
    query = """
    SELECT * FROM c
    WHERE ARRAY_CONTAINS(@allowed, c.endpoint, true)
      AND (NOT IS_DEFINED(c.document_class) OR c.document_class = '')
    """
    docs = list(
        container.query_items(
            query,
            parameters=[{"name": "@allowed", "value": ENDPOINTS_COGNITIVE}],
            enable_cross_partition_query=True,
        )
    )
    print(f"  Encontradas {len(docs)} interacciones candidatas.")
    for doc in docs:
        doc["document_class"] = "cognitive_memory"
        doc["is_synthetic"] = False
        doc["tipo"] = doc.get("tipo") or "accion_usuario"
        texto = clean_text(doc.get("texto_semantico", ""))
        if texto:
            doc["texto_semantico"] = texto
        container.upsert_item(doc)
    print(f"== Curacion completada ({len(docs)} documentos). ==\n")


def wipe_index(sc: SearchClient) -> None:
    batch: List[Dict[str, Any]] = []
    results = sc.search("*", select=["id"], top=1000)
    for doc in results:
        batch.append({"@search.action": "delete", "id": doc["id"]})
        if len(batch) >= 100:
            sc.upload_documents(documents=batch)
            batch = []
    if batch:
        sc.upload_documents(documents=batch)


def embedding_for(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-large")
    return response.data[0].embedding


def reindex_curated() -> None:
    print("== Paso 3: Reindexando Azure AI Search ==")
    try:
        wipe_index(search_client)
        print("  Indice vaciado.")
    except Exception as exc:
        print(f"  Advertencia al vaciar el indice: {exc}")

    query = """
    SELECT * FROM c
    WHERE c.document_class = 'cognitive_memory'
      AND c.is_synthetic = false
    """
    docs = list(container.query_items(
        query, enable_cross_partition_query=True))
    print(f"  Documentos a indexar: {len(docs)}")

    batch: List[Dict[str, Any]] = []
    indexed = 0
    for doc in docs:
        texto = doc.get("texto_semantico", "")
        if not texto or len(texto) < 10:
            continue
        try:
            vector = embedding_for(texto)
        except Exception:
            continue
        payload = {
            "@search.action": "upload",
            "id": doc["id"],
            "agent_id": doc.get("session_id", "GlobalAgent"),
            "session_id": doc.get("session_id", "GlobalAgent"),
            "endpoint": doc.get("endpoint", ""),
            "timestamp": doc.get("timestamp", ""),
            "texto_semantico": texto,
            "vector": vector,
            "document_class": "cognitive_memory",
            "tipo": doc.get("tipo", "accion_usuario"),
            "is_synthetic": False,
        }
        batch.append(payload)
        if len(batch) >= 50:
            search_client.upload_documents(documents=batch)
            indexed += len(batch)
            print(f"  Indexados {indexed}/{len(docs)}")
            batch = []
    if batch:
        search_client.upload_documents(documents=batch)
        indexed += len(batch)
    print(f"== Reindexacion completada ({indexed} documentos). ==\n")


def main() -> None:
    delete_noise()
    cure_documents()
    reindex_curated()
    print("Proceso completado.")


if __name__ == "__main__":
    main()
