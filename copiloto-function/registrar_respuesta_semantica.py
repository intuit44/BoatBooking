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
        
        # Limpiar emojis y referencias técnicas
        import re
        response_text = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', response_text)
        response_text = response_text.replace("endpoint", "consulta").replace("**", "").strip()

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

        # Crear evento para usar flujo unificado de _log_cosmos
        from services.memory_service import memory_service
        
        evento = {
            "id": f"{session_id}_semantic_{int(datetime.utcnow().timestamp())}",
            "session_id": session_id,
            "agent_id": agent_id,
            "endpoint": endpoint,
            "event_type": "respuesta_semantica",
            "texto_semantico": texto_sintetizado,
            "tipo": "respuesta_semantica",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "exito": True,
            "data": {
                "origen": "agent_output",
                "tipo": "respuesta_semantica",
                "longitud_original": len(response_text),
                "longitud_sintetizada": len(texto_sintetizado),
                "success": True
            }
        }
        
        # Usar flujo unificado que incluye validación de duplicados e indexación
        ok = memory_service._log_cosmos(evento)
        if ok:
            logging.info(f"✅ Respuesta guardada e indexada: {evento['id']}")
        else:
            logging.warning(f"⚠️ No se pudo guardar respuesta (posible duplicado): {evento['id']}")

        return ok

    except Exception as e:
        logging.error(f"❌ Error registrando respuesta semántica: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
