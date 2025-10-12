# -*- coding: utf-8 -*-
"""
Memory Helpers - Utilidades para acceder a memoria desde endpoints
"""

import logging
from typing import Dict, Any, Optional
import azure.functions as func

def obtener_memoria_request(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Obtiene el contexto de memoria del request (si fue agregado por el decorador)
    """
    try:
        if hasattr(req, '__dict__') and "_memoria_contexto" in req.__dict__:
            return req.__dict__["_memoria_contexto"]
    except:
        pass
    return None

def obtener_prompt_memoria(req: func.HttpRequest) -> str:
    """
    Obtiene el contexto de memoria formateado para prompt
    """
    try:
        if hasattr(req, '__dict__') and "_memoria_prompt" in req.__dict__:
            return req.__dict__["_memoria_prompt"]
    except:
        pass
    return ""

def extraer_session_info(req: func.HttpRequest) -> Dict[str, Optional[str]]:
    """
    Extrae session_id y agent_id del request
    """
    session_id = None
    agent_id = None
    
    try:
        # Intentar desde parámetros de query
        session_id = req.params.get("session_id")
        agent_id = req.params.get("agent_id")
        
        # Intentar desde body JSON
        if not session_id or not agent_id:
            try:
                body = req.get_json()
                if body:
                    session_id = session_id or body.get("session_id")
                    agent_id = agent_id or body.get("agent_id")
            except:
                pass
        
        # Intentar desde headers
        if not session_id:
            session_id = req.headers.get("X-Session-ID")
        if not agent_id:
            agent_id = req.headers.get("X-Agent-ID")
            
    except Exception as e:
        logging.warning(f"Error extrayendo session info: {e}")
    
    return {"session_id": session_id, "agent_id": agent_id}

def agregar_memoria_a_respuesta(response_data: Dict[str, Any], req: func.HttpRequest) -> Dict[str, Any]:
    """
    Agrega información de memoria a la respuesta SIEMPRE (incluso si no hay historial)
    """
    try:
        # Obtener identificadores de sesión (siempre presentes ahora)
        session_id = getattr(req, '_session_id', None) if hasattr(req, '__dict__') else None
        agent_id = getattr(req, '_agent_id', None) if hasattr(req, '__dict__') else None
        
        if "metadata" not in response_data:
            response_data["metadata"] = {}
        
        # SIEMPRE agregar información de sesión
        response_data["metadata"]["session_info"] = {
            "session_id": session_id,
            "agent_id": agent_id
        }
        
        # Agregar información de memoria si está disponible
        memoria = obtener_memoria_request(req)
        if memoria and memoria.get("tiene_historial"):
            response_data["metadata"]["memoria_disponible"] = True
            response_data["metadata"]["memoria_sesion"] = {
                "interacciones_previas": memoria.get("total_interacciones_sesion", 0),
                "ultima_actividad": memoria.get("ultima_actividad"),
                "continuidad_sesion": True
            }
        else:
            response_data["metadata"]["memoria_disponible"] = False
            
    except Exception as e:
        logging.warning(f"Error agregando memoria a respuesta: {e}")
    
    return response_data