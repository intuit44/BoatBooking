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
        # Detectar session_id y agent_id
        session_id = (
            req.params.get("session_id") or
            (req.get_json() or {}).get("session_id") or
            req.headers.get("X-Session-ID") or
            f"auto_{hash(str(req.headers.get('User-Agent', '')) + str(req.url))}"
        )
        
        agent_id = (
            req.params.get("agent_id") or
            (req.get_json() or {}).get("agent_id") or
            req.headers.get("X-Agent-ID") or
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