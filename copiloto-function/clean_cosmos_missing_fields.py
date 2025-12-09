#!/usr/bin/env python3
"""
Limpieza de documentos en Cosmos DB que no tienen campo texto_semantico
Identifica, reporta y corrige registros inconsistentes
"""
import os
import logging
from typing import Dict, List, Any
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import json

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_cosmos_client():
    """Crear cliente Cosmos DB"""
    endpoint = os.environ.get("COSMOSDB_ENDPOINT")
    key = os.environ.get("COSMOSDB_KEY")

    if not endpoint or not key:
        logger.error(
            "❌ Variables COSMOSDB_ENDPOINT o COSMOSDB_KEY no configuradas")
        return None

    return CosmosClient(endpoint, key)


def find_documents_without_texto_semantico(container, batch_size=100):
    """Buscar documentos que no tienen texto_semantico"""
    logger.info("🔍 Buscando documentos sin texto_semantico...")

    # Query para documentos sin texto_semantico o con valor null/vacío
    query = """
    SELECT c.id, c.event_type, c.session_id, c._ts, c.data
    FROM c 
    WHERE NOT IS_DEFINED(c.texto_semantico) 
       OR c.texto_semantico = null 
       OR c.texto_semantico = ""
    """

    problematic_docs = []

    try:
        items = container.query_items(query, enable_cross_partition_query=True)
        for item in items:
            problematic_docs.append(item)

        logger.info(
            f"📊 Encontrados {len(problematic_docs)} documentos problemáticos")
        return problematic_docs

    except Exception as e:
        logger.error(f"❌ Error consultando documentos: {e}")
        return []


def generate_texto_semantico_fallback(doc: Dict[str, Any]) -> str:
    """Generar texto_semantico de fallback para documento"""

    # Intentar extraer contenido significativo
    content_sources = [
        doc.get('data', {}).get('content', ''),
        doc.get('data', {}).get('message', ''),
        doc.get('data', {}).get('texto', ''),
        doc.get('message', ''),
        doc.get('content', ''),
        str(doc.get('data', {})) if doc.get('data') else '',
    ]

    # Usar el primer contenido no vacío
    for source in content_sources:
        if isinstance(source, str) and len(source.strip()) > 10:
            return source.strip()[:500]  # Limitar tamaño

    # Fallback básico basado en metadatos
    event_type = doc.get('event_type', 'unknown')
    session_id = doc.get('session_id', 'unknown')
    doc_id = doc.get('id', 'unknown')

    return f"Evento {event_type} en sesión {session_id} (ID: {doc_id})"


def fix_document(container, doc: Dict[str, Any], dry_run=True) -> bool:
    """Corregir documento agregando texto_semantico"""

    doc_id = doc.get('id')
    if not doc_id:
        logger.warning("⚠️ Documento sin ID, saltando")
        return False

    # Generar texto_semantico
    new_texto = generate_texto_semantico_fallback(doc)

    if dry_run:
        logger.info(f"[DRY RUN] Corregiría {doc_id}: '{new_texto[:100]}...'")
        return True

    try:
        # Actualizar documento
        doc['texto_semantico'] = new_texto
        container.upsert_item(doc)
        logger.info(f"✅ Corregido {doc_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error corrigiendo {doc_id}: {e}")
        return False


def delete_document(container, doc: Dict[str, Any], dry_run=True) -> bool:
    """Eliminar documento problemático"""

    doc_id = doc.get('id')
    # Usar session_id como partition key
    partition_key = doc.get('session_id', doc.get('id'))

    if dry_run:
        logger.info(f"[DRY RUN] Eliminaría {doc_id}")
        return True

    try:
        container.delete_item(doc_id, partition_key=partition_key)
        logger.info(f"🗑️ Eliminado {doc_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error eliminando {doc_id}: {e}")
        return False


def main():
    """Función principal"""
    logger.info("🚀 Iniciando limpieza de Cosmos DB...")

    # Obtener configuración
    database_name = os.environ.get("COSMOS_DATABASE_NAME", "agentMemory")
    container_name = os.environ.get("COSMOS_CONTAINER_NAME", "memory")

    # Crear cliente
    client = get_cosmos_client()
    if not client:
        return

    try:
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Buscar documentos problemáticos
        problematic_docs = find_documents_without_texto_semantico(container)

        if not problematic_docs:
            logger.info("✅ No hay documentos problemáticos")
            return

        # Mostrar estadísticas
        logger.info(f"📊 ANÁLISIS DE {len(problematic_docs)} DOCUMENTOS:")

        event_types = {}
        for doc in problematic_docs:
            event_type = doc.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for event_type, count in event_types.items():
            logger.info(f"   • {event_type}: {count}")

        # Preguntar acción (simular respuesta automática para corrección)
        print("\n¿Qué deseas hacer?")
        print("1. Corregir documentos (agregar texto_semantico)")
        print("2. Eliminar documentos problemáticos")
        print("3. Solo mostrar reporte (dry run)")

        # Para automatización, elegir opción 1 (corregir)
        action = "1"

        if action == "1":
            logger.info("🔧 Corrigiendo documentos...")
            fixed = 0
            for doc in problematic_docs:
                if fix_document(container, doc, dry_run=False):
                    fixed += 1
            logger.info(
                f"✅ {fixed}/{len(problematic_docs)} documentos corregidos")

        elif action == "2":
            logger.info("🗑️ Eliminando documentos...")
            deleted = 0
            for doc in problematic_docs:
                if delete_document(container, doc, dry_run=False):
                    deleted += 1
            logger.info(
                f"🗑️ {deleted}/{len(problematic_docs)} documentos eliminados")

        else:
            logger.info("📋 Modo dry run - no se realizaron cambios")
            for doc in problematic_docs:
                fix_document(container, doc, dry_run=True)

    except Exception as e:
        logger.error(f"❌ Error accediendo a Cosmos DB: {e}")


if __name__ == "__main__":
    main()
