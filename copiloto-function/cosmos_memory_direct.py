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
        database_name = os.environ.get("COSMOSDB_DATABASE", "copiloto-db")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "interacciones")
        
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
    
    # 1. Desde parámetros de query
    session_id = req.params.get("session_id")
    if session_id:
        return session_id
    
    # 2. Desde body JSON
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            session_id = body.get("session_id")
            if session_id:
                return session_id
    except:
        pass
    
    # 3. Desde headers
    session_id = req.headers.get("X-Session-ID")
    if session_id:
        return session_id
    
    # 4. Generar uno temporal basado en IP + timestamp (fallback)
    try:
        client_ip = req.headers.get("X-Forwarded-For", "unknown").split(",")[0]
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"temp_{client_ip}_{timestamp}"
    except:
        return f"temp_session_{datetime.now().strftime('%Y%m%d_%H')}"

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
    """
    try:
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
            
            # Agregar metadata de memoria
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"]["memoria_aplicada"] = True
            response_data["metadata"]["interacciones_previas"] = memoria["total_interacciones"]
            
            logging.info(f"✅ Memoria aplicada: {memoria['total_interacciones']} interacciones encontradas")
        
        else:
            # Incluso sin historial, marcar que se consultó
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"]["memoria_consultada"] = True
            response_data["metadata"]["nueva_sesion"] = True
            
            logging.info("ℹ️ Sin historial previo - nueva sesión")
        
        return response_data
        
    except Exception as e:
        logging.error(f"Error aplicando memoria Cosmos directo: {e}")
        return response_data