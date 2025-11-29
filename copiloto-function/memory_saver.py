"""
Memory Saver - Guarda automáticamente interacciones en Cosmos DB
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import azure.functions as func
import json
import uuid


def guardar_interaccion_cosmos(req: func.HttpRequest, response_data: Dict[str, Any], endpoint: str) -> None:
    """
    Guarda automáticamente la interacción en Cosmos DB colección 'memory'
    EXCLUYE endpoints meta-operacionales para evitar bucles de introspección
    """
    try:
        # 🚫 FILTRO 1: NO guardar endpoints meta-operacionales (REFORZADO)
        ENDPOINTS_EXCLUIDOS = {
            'historial-interacciones', '/api/historial-interacciones',
            'historial_interacciones',  # Versión con guión bajo
            'health', '/api/health',
            'verificar-sistema', 'verificar-cosmos', 'verificar-app-insights',
            '/api/verificar-sistema', '/api/verificar-cosmos', '/api/verificar-app-insights'
        }

        endpoint_normalizado = endpoint.strip('/').lower().replace('_', '-')
        if any(excluido in endpoint_normalizado for excluido in ENDPOINTS_EXCLUIDOS):
            logging.info(f"⏭️ Endpoint meta-operacional excluido: {endpoint}")
            return

        # 🚫 FILTRO 1.5: Verificación adicional por nombre de función
        if 'historial' in endpoint_normalizado:
            logging.info(
                f"⏭️ Endpoint de historial excluido por patrón: {endpoint}")
            return

        # 🚫 FILTRO 2: NO guardar contenido basura en texto_semantico
        texto_semantico = response_data.get(
            'texto_semantico', '') or response_data.get('mensaje', '')
        PATRONES_BASURA = [
            '🔍 CONSULTA DE HISTORIAL',
            'Se encontraron',
            'interacciones recientes',
            '✅ Éxito',
            'Consulta completada',
            'RESULTADO:',
            'Sin resumen de conversación'
        ]

        if any(patron in texto_semantico for patron in PATRONES_BASURA):
            logging.info(
                f"⏭️ Contenido basura excluido: {texto_semantico[:50]}...")
            return

        # 🚫 FILTRO 3: Texto muy corto o vacío
        if len(texto_semantico.strip()) < 5:
            logging.info(f"⏭️ Texto muy corto excluido: {texto_semantico}")
            return

        from azure.cosmos import CosmosClient

        # Configuración de Cosmos DB
        endpoint_url = os.environ.get(
            "COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = "memory"  # Colección específica para interacciones

        if not key:
            logging.warning(
                "COSMOSDB_KEY no configurada - no se guardará interacción")
            return

        # Extraer información del request
        session_id = extraer_session_id_para_guardar(req)
        agent_id = extraer_agent_id_para_guardar(req)

        # Extraer consulta del usuario
        consulta_usuario = extraer_consulta_usuario(req)

        # Preparar documento para Cosmos DB con ID único
        timestamp_unico = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        documento = {
            "id": f"{session_id}_interaccion_{timestamp_unico}",
            "session_id": session_id,
            "agent_id": agent_id,
            "tipo": "interaccion",
            "endpoint": endpoint,
            "consulta": consulta_usuario,
            # Limitar tamaño
            "respuesta": json.dumps(response_data, ensure_ascii=False)[:1000],
            "exito": response_data.get("exito", True),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "_ts": int(datetime.utcnow().timestamp())
        }

        # Conectar y guardar
        client = CosmosClient(endpoint_url, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Usar upsert para evitar conflictos
        container.upsert_item(documento)

        logging.info(
            f"✅ Interacción guardada en Cosmos DB: {session_id} -> {endpoint}")

    except Exception as e:
        logging.error(f"❌ Error guardando interacción en Cosmos DB: {e}")


def extraer_session_id_para_guardar(req: func.HttpRequest) -> str:
    """Extrae o genera session_id para guardar"""

    # 1. PRIORIDAD: Desde headers (Session-ID)
    session_id = req.headers.get(
        "Session-ID") or req.headers.get("X-Session-ID")
    if session_id:
        return session_id

    # 2. Desde parámetros
    session_id = req.params.get("Session-ID") or req.params.get("session_id")
    if session_id:
        return session_id

    # 3. Desde body
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            session_id = body.get("session_id")
            if session_id:
                return session_id
    except:
        pass

    # 4. FORZAR session_id constante
    return "constant-session-id"


def extraer_agent_id_para_guardar(req: func.HttpRequest) -> str:
    """Extrae o genera agent_id para guardar"""

    # 1. PRIORIDAD: Desde headers (Agent-ID)
    agent_id = req.headers.get("Agent-ID") or req.headers.get("X-Agent-ID")
    if agent_id:
        return agent_id

    # 2. Desde parámetros
    agent_id = req.params.get("Agent-ID") or req.params.get("agent_id")
    if agent_id:
        return agent_id

    # 3. Desde body
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            agent_id = body.get("agent_id")
            if agent_id:
                return agent_id
    except:
        pass

    # 4. Desde User-Agent
    user_agent = req.headers.get("User-Agent", "")
    if "azure-agents" in user_agent:
        return "foundry_agent"
    elif "copiloto" in user_agent.lower():
        return "copiloto_agent"

    return "unknown_agent"


def extraer_consulta_usuario(req: func.HttpRequest) -> str:
    """Extrae la consulta/mensaje del usuario del request"""

    # 1. Desde parámetros de query
    consulta = req.params.get("consulta") or req.params.get(
        "query") or req.params.get("mensaje")
    if consulta:
        return consulta[:500]  # Limitar tamaño

    # 2. Desde body JSON
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            consulta = (body.get("consulta") or
                        body.get("query") or
                        body.get("mensaje") or
                        body.get("prompt") or
                        body.get("ruta") or  # Para endpoints de archivos
                        body.get("comando"))  # Para endpoints de ejecución
            if consulta:
                return str(consulta)[:500]
    except:
        pass

    # 3. Fallback: información del endpoint
    return f"Consulta en {req.url}"


def aplicar_guardado_automatico(req: func.HttpRequest, response_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """
    Aplica guardado automático de la interacción y enriquece la respuesta
    """
    try:
        # Guardar interacción en background
        guardar_interaccion_cosmos(req, response_data, endpoint)

        # Agregar metadata de guardado
        if "metadata" not in response_data:
            response_data["metadata"] = {}

        response_data["metadata"]["interaccion_guardada"] = True
        response_data["metadata"]["timestamp_guardado"] = datetime.utcnow(
        ).isoformat() + "Z"

    except Exception as e:
        logging.error(f"Error en guardado automático: {e}")
        # No fallar la respuesta por error de guardado
        if "metadata" not in response_data:
            response_data["metadata"] = {}
        response_data["metadata"]["error_guardado"] = str(e)

    return response_data
