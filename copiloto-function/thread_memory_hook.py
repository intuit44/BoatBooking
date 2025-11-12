"""
Hook automático para sincronizar threads de Foundry con memoria
Se activa en cada invocación de endpoint
"""
import logging
from datetime import datetime
from typing import Optional

# Cache para evitar lecturas duplicadas en la misma request
_thread_cache = {}
_last_sync = {}


def sync_thread_to_memory(req, response_data: dict) -> dict:
    """
    Hook que se ejecuta DESPUÉS de cada endpoint
    Captura thread_id del header y sincroniza mensajes
    """
    try:
        # 1. Extraer thread_id del header
        thread_id = req.headers.get(
            "Thread-ID") or req.headers.get("X-Thread-ID")

        if not thread_id:
            return response_data  # Sin thread, no hacer nada

        # 2. Verificar si ya sincronizamos este thread en esta request
        request_id = id(req)
        cache_key = f"{thread_id}_{request_id}"

        if cache_key in _thread_cache:
            logging.debug(
                f"Thread {thread_id} ya sincronizado en esta request")
            return response_data

        # 3. Verificar última sincronización (evitar spam)
        now = datetime.now()
        last = _last_sync.get(thread_id)
        if last and (now - last).seconds < 5:  # Cooldown de 5 segundos
            logging.debug(f"Thread {thread_id} sincronizado hace menos de 5s")
            return response_data

        # 4. El wrapper ya captura los mensajes (Bloque 0 y 6)
        # Este hook solo marca el thread como procesado
        logging.info(f"✅ Thread {thread_id} procesado (mensajes capturados por wrapper)")

        # 5. Actualizar cache
        _thread_cache[cache_key] = True
        _last_sync[thread_id] = now

        # Limpiar cache viejo (mantener solo últimos 100)
        if len(_thread_cache) > 100:
            _thread_cache.clear()

        return response_data

    except Exception as e:
        logging.error(f"Error en sync_thread_to_memory: {e}")
        return response_data  # Nunca fallar el endpoint


def get_thread_messages(thread_id: str) -> list:
    """Obtiene mensajes del thread desde Foundry usando REST API directa"""
    try:
        import requests
        from azure.identity import ClientSecretCredential
        import os

        endpoint = os.getenv("AZURE_AI_ENDPOINT")
        if not endpoint:
            logging.warning("AZURE_AI_ENDPOINT no configurado")
            return []

        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        
        if not (client_id and client_secret and tenant_id):
            logging.warning("⚠️ Credenciales no configuradas")
            return []

        # Obtener token
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Llamar REST API directamente
        url = f"{endpoint}/threads/{thread_id}/messages"
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.error(f"❌ API REST falló: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        messages = data.get("data", [])

        # Extraer contenido de mensajes
        result = []
        for msg in messages:
            content_items = msg.get("content", [])
            text_parts = []
            for item in content_items:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", {}).get("value", ""))
            
            if text_parts:
                result.append({
                    "role": msg.get("role", "unknown"),
                    "content": " ".join(text_parts),
                    "created_at": msg.get("created_at")
                })
        
        return result
        
    except Exception as e:
        logging.error(f"Error obteniendo mensajes: {e}")
        return []


def registrar_output_agente(agent_id: str, session_id: str, output_text: str, metadata: dict):
    """Registra output del agente en memoria"""
    try:
        from services.memory_service import memory_service

        memory_service.registrar_llamada(
            source="agent_output_hook",
            endpoint="agent_output",
            method="AUTO",
            params={
                "session_id": session_id,
                "agent_id": agent_id
            },
            response_data={
                "texto_semantico": output_text,
                "metadata": metadata
            },
            success=True
        )

    except Exception as e:
        logging.error(f"Error registrando output del agente: {e}")
