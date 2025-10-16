# -*- coding: utf-8 -*-
"""
Session Memory - Sistema de consulta automática de memoria por sesión
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from services.semantic_memory import obtener_contexto_agente, obtener_estado_sistema

def consultar_memoria_sesion(session_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Consulta memoria previa para una sesión específica
    """
    try:
        from services.cosmos_store import CosmosMemoryStore
        
        cosmos = CosmosMemoryStore()
        
        # Verificar que el container esté disponible
        if not cosmos.container:
            logging.warning("Cosmos DB container no disponible")
            return {"exito": False, "error": "Cosmos DB no disponible"}
        
        # Consultar interacciones previas de esta sesión
        query = f"""
        SELECT * FROM c 
        WHERE c.session_id = '{session_id}' 
        ORDER BY c.timestamp DESC
        OFFSET 0 LIMIT 20
        """
        
        interacciones_sesion = list(cosmos.container.query_items(query, enable_cross_partition_query=True))
        
        # Si hay agent_id, también consultar contexto del agente
        contexto_agente = {}
        if agent_id:
            resultado_agente = obtener_contexto_agente(agent_id, limit=10)
            if resultado_agente.get("exito"):
                contexto_agente = resultado_agente["contexto"]
        
        # Construir contexto de memoria
        memoria = {
            "session_id": session_id,
            "agent_id": agent_id,
            "tiene_historial": len(interacciones_sesion) > 0,
            "total_interacciones_sesion": len(interacciones_sesion),
            "interacciones_recientes": interacciones_sesion[:5],
            "contexto_agente": contexto_agente,
            "timestamp_consulta": datetime.utcnow().isoformat()
        }
        
        # Extraer patrones de la sesión
        if interacciones_sesion:
            memoria["ultima_actividad"] = interacciones_sesion[0].get("timestamp")
            memoria["endpoints_usados"] = list(set(item.get("source", "") for item in interacciones_sesion))
            memoria["temas_tratados"] = extraer_temas_sesion(interacciones_sesion)
        
        return {"exito": True, "memoria": memoria}
        
    except Exception as e:
        logging.error(f"Error consultando memoria de sesión {session_id}: {e}")
        return {"exito": False, "error": str(e)}

def extraer_temas_sesion(interacciones: List[Dict]) -> List[str]:
    """
    Extrae temas principales de las interacciones de una sesión
    """
    temas = set()
    
    for item in interacciones:
        # Extraer de source/endpoint
        source = item.get("source", "")
        if source:
            temas.add(source.replace("_", " ").replace("-", " "))
        
        # Extraer de parámetros si contienen información relevante
        params = item.get("params", {})
        if isinstance(params, dict):
            for key, value in params.items():
                if isinstance(value, str) and len(value) < 50:
                    if any(keyword in value.lower() for keyword in ["diagnostico", "config", "app", "azure"]):
                        temas.add(value)
    
    return list(temas)[:5]  # Máximo 5 temas

def generar_contexto_prompt(memoria: Dict[str, Any]) -> str:
    """
    Genera contexto para incluir en el prompt del agente
    """
    if not memoria.get("tiene_historial"):
        return ""
    
    contexto_parts = []
    
    # Información de sesión
    if memoria.get("total_interacciones_sesion", 0) > 0:
        contexto_parts.append(f"Sesión activa con {memoria['total_interacciones_sesion']} interacciones previas.")
    
    # Última actividad
    if memoria.get("ultima_actividad"):
        contexto_parts.append(f"Última actividad: {memoria['ultima_actividad']}")
    
    # Endpoints usados
    if memoria.get("endpoints_usados"):
        endpoints = ", ".join(memoria["endpoints_usados"][:3])
        contexto_parts.append(f"Endpoints recientes: {endpoints}")
    
    # Temas tratados
    if memoria.get("temas_tratados"):
        temas = ", ".join(memoria["temas_tratados"][:3])
        contexto_parts.append(f"Temas tratados: {temas}")
    
    # Contexto del agente
    if memoria.get("contexto_agente", {}).get("total_interacciones", 0) > 0:
        ctx = memoria["contexto_agente"]
        contexto_parts.append(f"Agente con {ctx['total_interacciones']} interacciones totales")
    
    return " | ".join(contexto_parts)

def es_sesion_nueva(session_id: str) -> bool:
    """
    Determina si es una sesión nueva (sin historial previo)
    """
    try:
        resultado = consultar_memoria_sesion(session_id)
        return not resultado.get("memoria", {}).get("tiene_historial", False)
    except:
        return True  # Asumir nueva si hay error