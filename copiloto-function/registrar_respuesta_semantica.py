# -*- coding: utf-8 -*-
"""
Registrador de Respuestas Semánticas del Agente
Vectoriza y persiste las respuestas generadas por el copiloto/agente.
"""
import logging
from datetime import datetime
from typing import Optional


def sintetizar_texto(texto: str, max_chars: int = 1200) -> str:
    """Sintetiza texto preservando información clave."""
    texto = texto.strip()
    if len(texto) <= max_chars:
        return texto

    # Buscar último punto antes del límite
    cutoff = texto[:max_chars]
    last_punct = max(cutoff.rfind('.'), cutoff.rfind('!'), cutoff.rfind('?'))

    if last_punct > int(max_chars * 0.4):
        return cutoff[:last_punct + 1].strip()

    # Cortar en último espacio
    if ' ' in cutoff:
        last_space = cutoff.rfind(' ')
        return cutoff[:last_space].strip() + "..."

    return cutoff + "..."


def registrar_respuesta_semantica(
    response_text: str,
    session_id: str,
    agent_id: str = "foundry_user",
    endpoint: str = "copiloto"
) -> bool:
    """
    Crea embedding y guarda la respuesta del agente como evento semántico.

    Args:
        response_text: Texto de la respuesta del agente
        session_id: ID de sesión
        agent_id: ID del agente
        endpoint: Endpoint que generó la respuesta

    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        # Validar entrada
        if not response_text or len(str(response_text).strip()) < 50:
            logging.info("⏭️ Respuesta muy corta, no se vectoriza")
            return False

        # 🧩 Normalizar: convertir dict/list a cadena JSON
        if isinstance(response_text, (dict, list)):
            import json
            response_text = json.dumps(response_text, ensure_ascii=False)

        # Sintetizar texto antes de vectorizar
        texto_sintetizado = sintetizar_texto(response_text, max_chars=1200)
        logging.info(
            f"📝 Texto sintetizado: {len(response_text)} → {len(texto_sintetizado)} chars")

        # Generar embedding
        from embedding_generator import generar_embedding
        vector = generar_embedding(texto_sintetizado)
        if not vector:
            logging.warning("⚠️ No se pudo generar embedding para respuesta")
            return False

        # Crear documento para Cosmos (con estructura completa)
        documento_cosmos = {
            "id": f"{session_id}_semantic_{int(datetime.utcnow().timestamp())}",
            "session_id": session_id,
            "agent_id": agent_id,
            "endpoint": endpoint,
            "event_type": "respuesta_semantica",
            "texto_semantico": texto_sintetizado,
            "tipo": "respuesta_semantica",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vector": vector,
            "exito": True,
            "data": {
                "origen": "agent_output",
                "tipo": "respuesta_semantica",
                "longitud_original": len(response_text),
                "longitud_sintetizada": len(texto_sintetizado)
            }
        }

        # Guardar en Cosmos
        from services.memory_service import memory_service
        memory_service.memory_container.upsert_item(documento_cosmos)
        logging.info(
            f"✅ Respuesta guardada en Cosmos: {documento_cosmos['id']}")

        # Crear documento aplanado para AI Search (sin campos anidados)
        documento_search = {
            "id": documento_cosmos["id"],
            "session_id": session_id,
            "agent_id": agent_id,
            "endpoint": endpoint,
            "event_type": "respuesta_semantica",
            "texto_semantico": texto_sintetizado,
            "tipo": "respuesta_semantica",
            "timestamp": documento_cosmos["timestamp"],
            "vector": vector,
            "exito": True,
            "origen": "agent_output",
            "longitud_original": len(response_text),
            "longitud_sintetizada": len(texto_sintetizado)
        }

        # Indexar en AI Search
        from services.azure_search_client import AzureSearchService
        AzureSearchService().indexar_documentos([documento_search])
        logging.info(
            f"🔍 Respuesta indexada en AI Search: {documento_cosmos['id']}")

        return True

    except Exception as e:
        logging.error(f"❌ Error registrando respuesta semántica: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
