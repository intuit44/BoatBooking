# -*- coding: utf-8 -*-
"""
Memory Pre-check - Consulta automática de memoria antes de responder
"""

import logging
from typing import Dict, Any, Optional
import azure.functions as func
from datetime import datetime
import json

def consultar_memoria_antes_responder(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Consulta automáticamente la memoria antes de que el endpoint responda.
    Si encuentra historial, devuelve un resumen para incluir en la respuesta.
    """
    try:
        from memory_helpers import extraer_session_info, obtener_memoria_request
        
        # Extraer información de sesión
        session_info = extraer_session_info(req)
        session_id = session_info.get("session_id")
        agent_id = session_info.get("agent_id")
        
        if not session_id:
            return None
            
        # Intentar obtener memoria
        memoria = obtener_memoria_request(req)
        
        if memoria and memoria.get("tiene_historial"):
            interacciones = memoria.get("interacciones_recientes", [])
            
            if interacciones:
                # Generar resumen de las últimas interacciones
                resumen = generar_resumen_interacciones(interacciones[-3:])  # Últimas 3
                
                return {
                    "contexto_recuperado": True,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "total_interacciones": memoria.get("total_interacciones_sesion", 0),
                    "ultima_actividad": memoria.get("ultima_actividad"),
                    "resumen_reciente": resumen,
                    "continuidad_sesion": True
                }
        
        return {
            "contexto_recuperado": False,
            "session_id": session_id,
            "agent_id": agent_id,
            "nueva_sesion": True
        }
        
    except Exception as e:
        logging.warning(f"Error consultando memoria previa: {e}")
        return None

def generar_resumen_interacciones(interacciones: list) -> str:
    """
    Genera un resumen conciso de las últimas interacciones
    """
    if not interacciones:
        return "Sin interacciones previas"
    
    resumen_items = []
    
    for interaccion in interacciones:
        if isinstance(interaccion, dict):
            endpoint = interaccion.get("endpoint", "unknown")
            timestamp = interaccion.get("timestamp", "")
            exito = interaccion.get("exito", True)
            
            # Formatear timestamp
            try:
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    tiempo = dt.strftime("%H:%M")
                else:
                    tiempo = "??:??"
            except:
                tiempo = "??:??"
            
            status = "✅" if exito else "❌"
            resumen_items.append(f"{tiempo} {status} {endpoint}")
    
    return " | ".join(resumen_items)

def aplicar_precheck_memoria(req: func.HttpRequest, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica el pre-check de memoria a cualquier respuesta de endpoint
    """
    try:
        memoria_previa = consultar_memoria_antes_responder(req)
        
        if memoria_previa:
            # Asegurar que response_data es mutable
            if not isinstance(response_data, dict):
                response_data = {"data": response_data}
            
            # Agregar contexto de memoria al inicio de la respuesta
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"]["memoria_previa"] = memoria_previa
            
            # Si hay contexto recuperado, agregarlo prominentemente
            if memoria_previa.get("contexto_recuperado"):
                response_data["contexto_sesion"] = {
                    "mensaje": f"Continuando sesión con {memoria_previa['total_interacciones']} interacciones previas",
                    "resumen": memoria_previa["resumen_reciente"],
                    "ultima_actividad": memoria_previa["ultima_actividad"]
                }
        
        return response_data
        
    except Exception as e:
        logging.warning(f"Error aplicando precheck memoria: {e}")
        return response_data