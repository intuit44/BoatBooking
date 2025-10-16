"""
Consulta directa a Cosmos DB para memoria semántica
Reemplaza las funciones que no consultan realmente la base de datos
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import azure.functions as func

def consultar_memoria_cosmos_directo(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Consulta DIRECTAMENTE Cosmos DB para obtener historial de interacciones
    """
    try:
        from azure.cosmos import CosmosClient
        
        # Configuración de Cosmos DB
        endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")
        
        if not key:
            logging.warning("COSMOSDB_KEY no configurada")
            return None
        
        # Extraer session_id del request
        session_id = extraer_session_id_request(req)
        if not session_id:
            logging.info("No se encontró session_id en el request")
            return None
        
        # Conectar a Cosmos DB
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Consultar últimas interacciones de esta sesión
        query = """
        SELECT TOP 10 * FROM c 
        WHERE c.session_id = @session_id 
        ORDER BY c._ts DESC
        """
        
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@session_id", "value": session_id}],
            enable_cross_partition_query=True
        ))
        
        if items:
            # Procesar interacciones encontradas
            interacciones_formateadas = []
            
            for item in items:
                interaccion = {
                    "timestamp": item.get("timestamp", ""),
                    "endpoint": item.get("endpoint", "unknown"),
                    "consulta": item.get("consulta", "")[:100],  # Primeros 100 chars
                    "exito": item.get("exito", True),
                    "respuesta_resumen": item.get("respuesta", "")[:150]  # Primeros 150 chars
                }
                interacciones_formateadas.append(interaccion)
            
            # Generar resumen para el agente
            resumen_conversacion = generar_resumen_conversacion(interacciones_formateadas)
            
            return {
                "tiene_historial": True,
                "session_id": session_id,
                "total_interacciones": len(items),
                "interacciones_recientes": interacciones_formateadas,
                "resumen_conversacion": resumen_conversacion,
                "ultima_actividad": items[0].get("timestamp") if items else None,
                "contexto_recuperado": True
            }
        else:
            return {
                "tiene_historial": False,
                "session_id": session_id,
                "nueva_sesion": True
            }
            
    except Exception as e:
        logging.error(f"Error consultando Cosmos DB directamente: {e}")
        return None

def extraer_session_id_request(req: func.HttpRequest) -> Optional[str]:
    """Extrae session_id de múltiples fuentes en el request"""
    
    # 1. Desde headers (prioridad alta)
    session_id = (
        req.headers.get("Session-ID") or
        req.headers.get("X-Session-ID") or
        req.headers.get("x-session-id")
    )
    if session_id:
        logging.info(f"🔍 Session ID desde headers: {session_id}")
        return session_id
    
    # 2. Desde parámetros de query
    session_id = req.params.get("session_id")
    if session_id:
        logging.info(f"🔍 Session ID desde params: {session_id}")
        return session_id
    
    # 3. Desde body JSON
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            session_id = body.get("session_id")
            if session_id:
                logging.info(f"🔍 Session ID desde body: {session_id}")
                return session_id
    except:
        pass
    
    # 4. Generar uno temporal basado en User-Agent + IP (fallback CONSISTENTE)
    try:
        user_agent = req.headers.get("User-Agent", "default")
        client_ip = req.headers.get("X-Forwarded-For", "localhost").split(",")[0]
        session_id = f"auto_{abs(hash(user_agent + client_ip))}"
        logging.info(f"🔍 Session ID generado automáticamente: {session_id}")
        return session_id
    except:
        fallback_id = f"temp_session_{datetime.now().strftime('%Y%m%d_%H')}"
        logging.info(f"🔍 Session ID fallback: {fallback_id}")
        return fallback_id

def generar_resumen_conversacion(interacciones: List[Dict]) -> str:
    """Genera un resumen legible de la conversación para el agente"""
    
    if not interacciones:
        return "Sin historial de conversación"
    
    # Tomar las últimas 5 interacciones
    ultimas = interacciones[:5]
    
    resumen_items = []
    
    for i, interaccion in enumerate(ultimas):
        timestamp = interaccion.get("timestamp", "")
        consulta = interaccion.get("consulta", "")
        endpoint = interaccion.get("endpoint", "")
        
        # Formatear timestamp
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                tiempo = dt.strftime("%H:%M")
            else:
                tiempo = "??:??"
        except:
            tiempo = "??:??"
        
        # Crear resumen de la interacción
        if consulta:
            resumen_items.append(f"{i+1}. [{tiempo}] {consulta[:80]}...")
        else:
            resumen_items.append(f"{i+1}. [{tiempo}] Consulta en {endpoint}")
    
    return "\\n".join(resumen_items)

def aplicar_memoria_cosmos_directo(req: func.HttpRequest, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica memoria consultando directamente Cosmos DB y enriquece la respuesta
    INCLUYE detección automática de endpoint para evitar "unknown"
    """
    try:
        # 🎯 DETECTAR ENDPOINT AUTOMÁTICAMENTE
        endpoint_detectado = "unknown"
        try:
            from endpoint_detector import aplicar_deteccion_endpoint_automatica
            endpoint_detectado = aplicar_deteccion_endpoint_automatica(req)
            logging.info(f"🎯 Endpoint auto-detectado para memoria: {endpoint_detectado}")
        except Exception as e:
            logging.warning(f"⚠️ Error en detección automática de endpoint: {e}")
        
        # Consultar memoria directamente
        memoria = consultar_memoria_cosmos_directo(req)
        
        if memoria and memoria.get("tiene_historial"):
            # Asegurar que response_data es mutable
            if not isinstance(response_data, dict):
                response_data = {"data": response_data}
            
            # Agregar contexto de conversación al inicio
            if "contexto_conversacion" not in response_data:
                response_data["contexto_conversacion"] = {
                    "mensaje": f"Continuando conversación con {memoria['total_interacciones']} interacciones previas",
                    "ultimas_consultas": memoria["resumen_conversacion"],
                    "session_id": memoria["session_id"],
                    "ultima_actividad": memoria["ultima_actividad"]
                }
            
            # Agregar metadata de memoria CON endpoint detectado
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"]["memoria_aplicada"] = True
            response_data["metadata"]["interacciones_previas"] = memoria["total_interacciones"]
            response_data["metadata"]["endpoint_detectado"] = endpoint_detectado
            
            logging.info(f"✅ Memoria aplicada: {memoria['total_interacciones']} interacciones encontradas")
        
        else:
            # Incluso sin historial, marcar que se consultó CON endpoint detectado
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"]["memoria_consultada"] = True
            response_data["metadata"]["nueva_sesion"] = True
            response_data["metadata"]["endpoint_detectado"] = endpoint_detectado
            
            logging.info("ℹ️ Sin historial previo - nueva sesión")
        
        # 💾 REGISTRAR INTERACCIÓN ACTUAL CON ENDPOINT CORRECTO
        try:
            registrar_interaccion_cosmos_directo(req, endpoint_detectado, response_data)
        except Exception as e:
            logging.warning(f"⚠️ Error registrando interacción actual: {e}")
        
        return response_data
        
    except Exception as e:
        logging.error(f"Error aplicando memoria Cosmos directo: {e}")
        return response_data

def registrar_redireccion_cosmos(req: func.HttpRequest, endpoint_original: str, fue_redirigido: bool, respuesta_redirigida: Any) -> bool:
    """
    Registra cada redirección semántica en Cosmos DB para análisis
    """
    try:
        from azure.cosmos import CosmosClient
        
        # Configuración de Cosmos DB
        endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = "redirections"  # Contenedor específico para redirecciones
        
        if not key:
            return False
        
        # Extraer información del request
        session_id = extraer_session_id_request(req)
        input_usuario = extraer_input_usuario_simple(req)
        
        # Conectar a Cosmos DB
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Crear documento de redirección con ID único
        timestamp_unico = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        documento = {
            "id": f"redirect_{session_id}_{timestamp_unico}",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint_original": endpoint_original,
            "fue_redirigido": fue_redirigido,
            "input_usuario": input_usuario[:200],  # Limitar tamaño
            "tipo": "redireccion_semantica",
            "_ts": int(datetime.now().timestamp())
        }
        
        # Usar upsert para evitar conflictos
        container.upsert_item(documento)
        logging.info(f"📊 Redirección registrada en Cosmos: {endpoint_original} -> redirigido={fue_redirigido}")
        return True
        
    except Exception as e:
        logging.warning(f"⚠️ Error registrando redirección en Cosmos: {e}")
        return False

def extraer_input_usuario_simple(req: func.HttpRequest) -> str:
    """Extrae input del usuario de forma simple"""
    try:
        # Parámetros
        for key in ['consulta', 'query', 'mensaje', 'q']:
            if key in req.params:
                return str(req.params[key])
        
        # Body
        try:
            body = req.get_json()
            if body:
                for key in ['consulta', 'query', 'mensaje', 'prompt']:
                    if key in body:
                        return str(body[key])
        except:
            pass
        
        return "input_no_detectado"
    except:
        return "error_extrayendo_input"

def registrar_interaccion_cosmos_directo(req: func.HttpRequest, endpoint: str, response_data: Dict[str, Any]) -> bool:
    """
    Registra la interacción actual directamente en Cosmos DB con el endpoint correcto
    """
    try:
        from azure.cosmos import CosmosClient
        
        # Configuración de Cosmos DB
        cosmos_endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")
        
        if not key:
            return False
        
        # Extraer información del request
        session_id = extraer_session_id_request(req)
        agent_id = extraer_agent_id_request(req)
        input_usuario = extraer_input_usuario_simple(req)
        
        # Conectar a Cosmos DB
        client = CosmosClient(cosmos_endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Crear documento de interacción con ID único
        timestamp_unico = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        documento = {
            "id": f"interaction_{session_id}_{timestamp_unico}",
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,  # 🎯 ENDPOINT CORRECTO DETECTADO AUTOMÁTICAMENTE
            "consulta": input_usuario[:500],  # Limitar tamaño
            "respuesta": str(response_data).replace('"', "'")[:500],  # Respuesta resumida
            "exito": response_data.get("exito", True) if isinstance(response_data, dict) else True,
            "method": getattr(req, 'method', 'GET'),
            "tipo": "interaccion_usuario",
            "_ts": int(datetime.now().timestamp())
        }
        
        # Usar upsert para evitar conflictos
        container.upsert_item(documento)
        logging.info(f"💾 Interacción registrada en Cosmos: {endpoint} (session: {session_id[:8]}...)")
        return True
        
    except Exception as e:
        logging.warning(f"⚠️ Error registrando interacción en Cosmos: {e}")
        return False

def extraer_agent_id_request(req: func.HttpRequest) -> str:
    """Extrae agent_id del request"""
    try:
        # Headers
        agent_id = (
            req.headers.get("Agent-ID") or
            req.headers.get("X-Agent-ID") or
            req.headers.get("x-agent-id")
        )
        if agent_id:
            return agent_id
        
        # Parámetros
        agent_id = req.params.get("agent_id")
        if agent_id:
            return agent_id
        
        # Body
        try:
            body = req.get_json()
            if body and isinstance(body, dict):
                agent_id = body.get("agent_id")
                if agent_id:
                    return agent_id
        except:
            pass
        
        return "unknown_agent"
    except:
        return "error_agent"