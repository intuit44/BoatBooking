# -*- coding: utf-8 -*-
"""
Semantic Memory - Sistema de memoria semántica que lee de Cosmos DB
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from services.cosmos_store import CosmosMemoryStore
import uuid

def obtener_estado_sistema(horas_atras: int = 24) -> Dict[str, Any]:
    """
    Lee las últimas interacciones de Cosmos DB y determina el estado del sistema
    """
    try:
        cosmos = CosmosMemoryStore()
        desde = datetime.utcnow() - timedelta(hours=horas_atras)
        
        # Consultar últimas interacciones
        query = f"""
        SELECT * FROM c 
        WHERE c.timestamp >= '{desde.isoformat()}' 
        ORDER BY c.timestamp DESC
        OFFSET 0 LIMIT 100
        """
        
        interacciones = list(cosmos.container.query_items(query, enable_cross_partition_query=True)) # type: ignore
        
        # Analizar estado
        estado = {
            "timestamp": datetime.utcnow().isoformat(),
            "periodo_analizado_horas": horas_atras,
            "total_interacciones": len(interacciones),
            "subsistemas_activos": set(),
            "agentes_activos": set(),
            "endpoints_mas_usados": {},
            "errores_recientes": [],
            "monitoreo_activo": False,
            "auditoria_activa": False,
            "supervision_activa": False
        }
        
        for item in interacciones:
            # Subsistemas activos
            source = item.get("source", "")
            if source:
                estado["subsistemas_activos"].add(source)
            
            # Agentes activos
            agent_id = item.get("agent_id")
            if agent_id:
                estado["agentes_activos"].add(agent_id)
            
            # Endpoints más usados
            endpoint = item.get("endpoint", "")
            if endpoint:
                estado["endpoints_mas_usados"][endpoint] = estado["endpoints_mas_usados"].get(endpoint, 0) + 1
            
            # Detectar errores
            if not item.get("success", True):
                estado["errores_recientes"].append({
                    "timestamp": item.get("timestamp"),
                    "source": source,
                    "error": item.get("response_data", {}).get("error", "Error desconocido")
                })
            
            # Detectar capacidades activas basadas en tipo
            tipo = item.get("tipo")
            if tipo == "monitoring_event":
                estado["monitoreo_activo"] = True
            if tipo == "auditoria_event":
                estado["auditoria_activa"] = True
            if tipo == "cognitive_snapshot":
                estado["supervision_activa"] = True
        
        # Convertir sets a listas para JSON
        estado["subsistemas_activos"] = list(estado["subsistemas_activos"])
        estado["agentes_activos"] = list(estado["agentes_activos"])
        
        return {"exito": True, "estado": estado}
        
    except Exception as e:
        logging.error(f"Error obteniendo estado del sistema: {e}")
        return {"exito": False, "error": str(e)}

def obtener_contexto_agente(agent_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene el contexto específico de un agente
    """
    try:
        cosmos = CosmosMemoryStore()
        
        query = f"""
        SELECT * FROM c 
        WHERE c.agent_id = '{agent_id}' 
        ORDER BY c.timestamp DESC
        OFFSET 0 LIMIT {limit}
        """
        
        interacciones = list(cosmos.container.query_items(query, enable_cross_partition_query=True)) # type: ignore
        
        contexto = {
            "agent_id": agent_id,
            "ultima_actividad": interacciones[0].get("timestamp") if interacciones else None,
            "total_interacciones": len(interacciones),
            "endpoints_usados": list(set(item.get("source", "") for item in interacciones)),
            "exitos": sum(1 for item in interacciones if item.get("success", True)),
            "errores": sum(1 for item in interacciones if not item.get("success", True)),
            "interacciones_recientes": interacciones[:5]
        }
        
        return {"exito": True, "contexto": contexto}
        
    except Exception as e:
        logging.error(f"Error obteniendo contexto del agente {agent_id}: {e}")
        return {"exito": False, "error": str(e)}

def registrar_snapshot_semantico(
    session_id: str,
    agent_id: str,
    tipo: str,
    contenido: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Registra un snapshot semántico en Cosmos DB
    """
    try:
        cosmos = CosmosMemoryStore()
        
        documento = {
            "id": f"semantic_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            "session_id": session_id,
            "agent_id": agent_id,
            "tipo": tipo,
            "contenido": contenido,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "_ts": int(datetime.utcnow().timestamp()),
            "categoria": "semantic_snapshot"
        }
        
        # Insertar en Cosmos DB
        cosmos.container.create_item(documento)
        
        logging.info(f"🧠 Snapshot semántico registrado: {tipo} para {session_id[:8]}...")
        
        return {
            "exito": True,
            "documento_id": documento["id"],
            "timestamp": documento["timestamp"]
        }
        
    except Exception as e:
        logging.error(f"Error registrando snapshot semántico: {e}")
        return {"exito": False, "error": str(e)}