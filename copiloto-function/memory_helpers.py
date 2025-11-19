# -*- coding: utf-8 -*-
"""
Memory Helpers - Utilidades para acceder a memoria desde endpoints
"""

import logging
from typing import Dict, Any, Optional
import azure.functions as func
from foundry_thread_extractor import obtener_thread_desde_foundry, extraer_thread_de_contexto

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

def extraer_session_info(req: func.HttpRequest, skip_api_call: bool = True) -> Dict[str, Optional[str]]:
    """
    Extrae session_id y agent_id del request - NORMALIZA AUTOMÁTICAMENTE
    
    PRIORIDAD:
    1. Headers: X-Thread-ID, Thread-ID, X-Session-ID
    2. Query params: thread_id, session_id
    3. Body JSON: thread_id, session_id, context.thread_id
    4. Foundry API (solo si skip_api_call=False)
    
    Args:
        skip_api_call: Si True, NO consulta Foundry API (por defecto True)
    """
    session_id = None
    agent_id = None
    body = None
    params = {}
    
    try:
        # 1. Headers (prioridad alta - Foundry usa headers)
        session_id = (
            req.headers.get("X-Thread-ID")
            or req.headers.get("Thread-ID")
            or req.headers.get("X-Session-ID")
            or req.headers.get("Session-ID")
        )
        agent_id = (
            req.headers.get("X-Agent-ID")
            or req.headers.get("Agent-ID")
            or req.headers.get("X-Agent")
            or req.headers.get("Agent")
        )
        
        # 2. Query params
        try:
            params = req.params or {}
        except Exception:
            params = {}

        if not session_id:
            session_id = (
                params.get("thread_id")
                or params.get("session_id")
                or params.get("Session-ID")
                or params.get("Thread-ID")
            )
        if not agent_id:
            agent_id = params.get("agent_id") or params.get("Agent-ID")
        
        # 3. Body JSON
        if not session_id or not agent_id:
            try:
                body = req.get_json()
                if body:
                    if isinstance(body, dict):
                        lower_map = {
                            (k.lower() if isinstance(k, str) else k): v
                            for k, v in body.items()
                        }
                        session_id = session_id or lower_map.get("thread_id") or lower_map.get(
                            "session_id") or body.get("Thread-ID") or body.get("Session-ID")
                        agent_id = agent_id or lower_map.get("agent_id") or body.get(
                            "Agent-ID") or body.get("agent")
            except:
                pass
        
        # 4. Extraer de contexto en payload (Foundry puede enviarlo aquí)
        if not session_id and body:
            session_id = extraer_thread_de_contexto(body)
        
        # 5. Foundry API como último recurso (con timeout)
        if not session_id and not skip_api_call:
            try:
                session_id = obtener_thread_desde_foundry(agent_id, timeout=1)
                if session_id:
                    logging.info(f"Thread capturado desde Foundry API: {session_id}")
            except Exception as e:
                logging.debug(f"Foundry API no disponible: {e}")
            
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
        if memoria is not None and isinstance(memoria, dict) and memoria.get("tiene_historial"):
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
