#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares para autocorrección con memoria en ejecutar-cli
"""

import json
import re
import logging
from datetime import datetime

def buscar_parametro_en_memoria(memoria_contexto, argumento, comando_actual):
    """
    Busca un parámetro específico en el historial de memoria de la sesión
    """
    try:
        if not memoria_contexto or not memoria_contexto.get("interacciones_previas"):
            return None
        
        # Buscar en interacciones previas
        for interaccion in memoria_contexto["interacciones_previas"]:
            # Buscar en comandos ejecutados exitosamente
            if interaccion.get("tipo") == "comando_exitoso":
                comando_previo = interaccion.get("comando", "")
                
                # Extraer valor del argumento del comando previo
                valor = extraer_valor_argumento(comando_previo, argumento)
                if valor:
                    logging.info(f"🧠 Valor encontrado en memoria: --{argumento} {valor}")
                    return valor
            
            # Buscar en parámetros explícitos
            if interaccion.get("parametros"):
                parametros = interaccion["parametros"]
                if argumento in parametros:
                    return parametros[argumento]
                
                # Buscar variaciones del nombre
                variaciones = generar_variaciones_argumento(argumento)
                for variacion in variaciones:
                    if variacion in parametros:
                        return parametros[variacion]
        
        return None
        
    except Exception as e:
        logging.warning(f"Error buscando parámetro en memoria: {e}")
        return None

def extraer_valor_argumento(comando, argumento):
    """
    Extrae el valor de un argumento específico de un comando
    """
    try:
        # Patrones para extraer argumentos
        patterns = [
            rf'--{argumento}\s+([^\s]+)',
            rf'--{argumento}=([^\s]+)',
            rf'-{argumento[0]}\s+([^\s]+)',  # Forma corta
        ]
        
        for pattern in patterns:
            match = re.search(pattern, comando)
            if match:
                valor = match.group(1)
                # Limpiar comillas si las tiene
                valor = valor.strip('"\'')
                return valor
        
        return None
        
    except Exception as e:
        logging.warning(f"Error extrayendo valor de argumento: {e}")
        return None

def generar_variaciones_argumento(argumento):
    """
    Genera variaciones comunes de nombres de argumentos
    """
    variaciones = [argumento]
    
    # Mapeo de variaciones comunes
    mapeo_variaciones = {
        "container-name": ["container", "contenedor", "container_name"],
        "account-name": ["account", "cuenta", "storage-account", "account_name"],
        "resource-group": ["group", "rg", "resource_group", "grupo"],
        "subscription": ["sub", "subscription-id", "subscription_id"],
        "location": ["region", "ubicacion", "loc"]
    }
    
    if argumento in mapeo_variaciones:
        variaciones.extend(mapeo_variaciones[argumento])
    
    # Agregar variaciones con guiones y guiones bajos
    if "-" in argumento:
        variaciones.append(argumento.replace("-", "_"))
    if "_" in argumento:
        variaciones.append(argumento.replace("_", "-"))
    
    return list(set(variaciones))

def obtener_memoria_request(req):
    """
    Obtiene el contexto de memoria para una request
    """
    try:
        # Detectar session_id
        session_id = (
            req.params.get("session_id") or
            (req.get_json() or {}).get("session_id") or
            req.headers.get("X-Session-ID") or
            f"auto_{hash(str(req.headers.get('User-Agent', '')) + str(req.url))}"
        )
        
        # Simular consulta a memoria (en implementación real, consultar Cosmos DB)
        # Por ahora, devolver estructura básica
        return {
            "session_id": session_id,
            "tiene_historial": False,  # Cambiar a True cuando se implemente Cosmos DB
            "total_interacciones_sesion": 0,
            "interacciones_previas": []
        }
        
    except Exception as e:
        logging.warning(f"Error obteniendo memoria de request: {e}")
        return None

def agregar_memoria_a_respuesta(response_data, req):
    """
    Agrega información de memoria a la respuesta
    """
    try:
        if not isinstance(response_data, dict):
            return response_data
        
        # Obtener información de sesión
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
        
        # Agregar metadata de memoria si no existe
        if "metadata" not in response_data:
            response_data["metadata"] = {}
        
        response_data["metadata"]["memoria_sesion"] = {
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "memoria_consultada": True
        }
        
        return response_data
        
    except Exception as e:
        logging.warning(f"Error agregando memoria a respuesta: {e}")
        return response_data

def extraer_session_info(req):
    """
    Extrae información de sesión de la request
    """
    try:
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
        
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.warning(f"Error extrayendo session info: {e}")
        return {
            "session_id": "error",
            "agent_id": "error",
            "timestamp": datetime.now().isoformat()
        }

def obtener_prompt_memoria(req):
    """
    Obtiene el prompt de memoria para contexto
    """
    try:
        # En implementación real, consultar Cosmos DB para obtener contexto
        # Por ahora, devolver estructura básica
        return {
            "contexto_disponible": False,
            "interacciones_recientes": 0,
            "comandos_exitosos_recientes": []
        }
        
    except Exception as e:
        logging.warning(f"Error obteniendo prompt de memoria: {e}")
        return None