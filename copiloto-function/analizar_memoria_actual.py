"""
Script de analisis: revisa que hay en Cosmos antes de limpiar.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any, Dict, Iterable

from azure.cosmos import CosmosClient


def load_settings() -> Dict[str, Any]:
    """Load configuration from local.settings.json or environment."""
    try:
        with open("local.settings.json", "r", encoding="utf-8") as handle:
            return json.load(handle)["Values"]
    except Exception:
        return os.environ.copy()


def require(value: str | None, message: str) -> str:
    if not value:
        raise RuntimeError(message)
    return value


def top_counts(values: Iterable[str], limit: int = 10) -> list[tuple[str, int]]:
    return Counter(values).most_common(limit)


def main() -> None:
    settings = load_settings()
    cosmos_endpoint = require(
        settings.get("COSMOSDB_ENDPOINT") or settings.get("COSMOS_ENDPOINT"),
        "Faltan COSMOSDB_ENDPOINT o COSMOS_ENDPOINT.",
    )
    cosmos_key = require(
        settings.get("COSMOSDB_KEY") or settings.get("COSMOS_KEY"),
        "Faltan COSMOSDB_KEY o COSMOS_KEY.",
    )
    database_name = settings.get("COSMOSDB_DATABASE", "agentMemory")
    container_name = settings.get("COSMOSDB_CONTAINER", "memory")

    client = CosmosClient(cosmos_endpoint, cosmos_key)
    container = client.get_database_client(database_name).get_container_client(container_name)

    print("== Analizando contenido actual de Cosmos ==")
    items = list(container.query_items("SELECT * FROM c", enable_cross_partition_query=True))
    print(f"Total documentos: {len(items)}\n")

    print("Por endpoint:")
    for endpoint, count in top_counts(item.get("endpoint", "sin_endpoint") for item in items):
        print(f"  {endpoint}: {count}")

    print("\nPor event_type:")
    for event_type, count in top_counts(item.get("event_type", "sin_event_type") for item in items):
        print(f"  {event_type}: {count}")

    con_class = sum(1 for item in items if "document_class" in item)
    print(f"\nCon document_class: {con_class}")
    print(f"Sin document_class: {len(items) - con_class}")

    noise_tokens = ("No se pudo", "Sesion estable", "Thread:", "assistant-")
    noise_docs = [
        item for item in items if any(token in item.get("texto_semantico", "") for token in noise_tokens)
    ]
    print(f"\nDocumentos con posible ruido en texto_semantico: {len(noise_docs)}")

    print("\n--- Ejemplos de ruido ---")
    for sample in noise_docs[:5]:
        texto = sample.get("texto_semantico", "")
        print(f"\n  ID: {sample.get('id')}")
        print(f"  Endpoint: {sample.get('endpoint')}")
        print(f"  Texto: {texto[:150]}{'...' if len(texto) > 150 else ''}")


if __name__ == "__main__":
    main()
