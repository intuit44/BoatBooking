#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación manual de memoria para endpoints - solución directa
"""

import json
from datetime import datetime

def aplicar_memoria_manual(req, response_data):
    """
    Aplica memoria manualmente a cualquier respuesta
    """
    try:
        # Detectar session_id y agent_id (PRIORIZAR HEADERS)
        session_id = (
            req.headers.get("Session-ID") or
            req.headers.get("X-Session-ID") or
            req.headers.get("x-session-id") or
            req.params.get("session_id") or
            (req.get_json() or {}).get("session_id") or
            f"auto_{abs(hash(str(req.headers.get('User-Agent', 'default')) + str(req.headers.get('X-Forwarded-For', 'localhost'))))}"
        )
        
        agent_id = (
            req.headers.get("Agent-ID") or
            req.headers.get("X-Agent-ID") or
            req.headers.get("x-agent-id") or
            req.params.get("agent_id") or
            (req.get_json() or {}).get("agent_id") or
            "AutoAgent"
        )
        
        # Asegurar que response_data es un dict
        if not isinstance(response_data, dict):
            response_data = {"data": response_data}
        
        # Agregar metadata de memoria
        if "metadata" not in response_data:
            response_data["metadata"] = {}
        
        response_data["metadata"]["session_info"] = {
            "session_id": session_id,
            "agent_id": agent_id
        }
        response_data["metadata"]["memoria_disponible"] = True
        response_data["metadata"]["wrapper_aplicado"] = True
        response_data["metadata"]["aplicacion_manual"] = True
        response_data["metadata"]["timestamp"] = datetime.now().isoformat()
        
        return response_data
        
    except Exception as e:
        # Si falla, agregar error pero no romper
        if isinstance(response_data, dict):
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            response_data["metadata"]["memoria_error"] = str(e)
        
        return response_data