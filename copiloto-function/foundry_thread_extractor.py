# -*- coding: utf-8 -*-
"""
Extractor de Thread-ID desde Azure AI Foundry API
Captura threads automáticamente cuando Foundry no los envía en headers
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def obtener_thread_desde_foundry(agent_id: str = None, timeout: int = 2) -> Optional[str]:
    """
    Consulta Azure AI Foundry para obtener el thread activo más reciente
    CON TIMEOUT para evitar bloqueos
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Foundry API timeout")
    
    try:
        # Solo en Windows, skip timeout (signal no funciona igual)
        if os.name == 'nt':
            logging.debug("Skipping Foundry API call en Windows local")
            return None
        
        # Configurar timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "https://AgenteOpenAi.services.ai.azure.com/api/projects/AgenteOpenAi-project")
        
        client = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=endpoint
        )
        
        threads = list(client.agents.threads.list(limit=1))
        
        signal.alarm(0)  # Cancelar timeout
        
        if threads:
            thread_id = threads[0].id
            logging.info(f"Thread capturado desde Foundry API: {thread_id}")
            return thread_id
            
    except TimeoutError:
        logging.warning("Foundry API timeout - usando fallback")
    except Exception as e:
        logging.warning(f"No se pudo obtener thread desde Foundry: {e}")
    finally:
        try:
            signal.alarm(0)  # Asegurar cancelación
        except:
            pass
    
    return None

def extraer_thread_de_contexto(req_body: Dict[str, Any]) -> Optional[str]:
    """
    Extrae thread_id del contexto de la conversación en el payload
    """
    try:
        # Buscar en diferentes ubicaciones del payload
        if isinstance(req_body, dict):
            # Foundry puede enviar contexto en diferentes formatos
            if "context" in req_body:
                ctx = req_body["context"]
                if isinstance(ctx, dict):
                    return ctx.get("thread_id") or ctx.get("conversation_id")
            
            # Buscar en metadata
            if "metadata" in req_body:
                meta = req_body["metadata"]
                if isinstance(meta, dict):
                    return meta.get("thread_id")
            
            # Buscar directamente en root
            return req_body.get("thread_id") or req_body.get("conversation_id")
            
    except Exception as e:
        logging.warning(f"Error extrayendo thread de contexto: {e}")
    
    return None
