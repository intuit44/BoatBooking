"""
Helper para registrar output del agente sin pasar por endpoints.
Reutiliza el flujo existente de registrar_respuesta_semantica.
"""
import logging


def registrar_output_agente(texto: str, session_id: str, agent_id: str = "foundry_user") -> bool:
    """
    Registra output del agente generado directamente (sin endpoint).
    
    Args:
        texto: Texto de la respuesta del agente
        session_id: ID de sesión
        agent_id: ID del agente
        
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        from registrar_respuesta_semantica import registrar_respuesta_semantica
        
        return registrar_respuesta_semantica(
            response_text=texto,
            session_id=session_id,
            agent_id=agent_id,
            endpoint="agent_output"
        )
    except Exception as e:
        logging.error(f"Error registrando output del agente: {e}")
        return False
