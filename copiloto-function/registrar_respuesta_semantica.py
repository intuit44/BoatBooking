# -*- coding: utf-8 -*-
"""
Registrador de Respuestas Semánticas del Agente
Vectoriza y persiste las respuestas generadas por el copiloto/agente.
"""
import logging
from datetime import datetime
from typing import Optional


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
        if not response_text or len(response_text.strip()) < 50:
            logging.info("⏭️ Respuesta muy corta, no se vectoriza")
            return False

        # Generar embedding
        from embedding_generator import generar_embedding
        vector = generar_embedding(response_text)
        if not vector:
            logging.warning("⚠️ No se pudo generar embedding para respuesta")
            return False

        # Crear documento
        documento = {
            "id": f"{session_id}_semantic_{int(datetime.utcnow().timestamp())}",
            "session_id": session_id,
            "agent_id": agent_id,
            "endpoint": endpoint,
            "event_type": "respuesta_semantica",
            "texto_semantico": response_text[:2000],
            "tipo": "respuesta_semantica",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vector": vector,
            "exito": True,
            "data": {
                "origen": "agent_output",
                "tipo": "respuesta_semantica",
                "longitud_original": len(response_text)
            }
        }

        # Guardar en Cosmos
        from services.memory_service import memory_service
        memory_service.memory_container.upsert_item(documento)
        logging.info(f"✅ Respuesta guardada en Cosmos: {documento['id']}")

        # Indexar en AI Search
        from services.azure_search_client import AzureSearchService
        AzureSearchService().indexar_documentos([documento])
        logging.info(f"🔍 Respuesta indexada en AI Search: {documento['id']}")

        return True

    except Exception as e:
        logging.error(f"❌ Error registrando respuesta semántica: {e}")
        return False
