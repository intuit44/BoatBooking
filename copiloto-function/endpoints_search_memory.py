# -*- coding: utf-8 -*-
"""
Endpoints de Búsqueda Semántica - Azure AI Search con Managed Identity
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

def buscar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/buscar-memoria
    Busca en memoria semántica usando Azure AI Search
    🔥 BÚSQUEDA UNIVERSAL: NO filtra por agent_id para encontrar todos los documentos relevantes
    """
    try:
        from services.azure_search_client import AzureSearchService

        # Validar payload
        query = req_body.get("query")
        if not query:
            return {"exito": False, "error": "Campo 'query' requerido"}

        session_id = req_body.get("session_id")
        agent_id = req_body.get("agent_id")
        top = int(req_body.get("top", 10))
        tipo = req_body.get("tipo")

        # Valores considerados genéricos que NO deben filtrar
        GENERIC_SESSIONS = {"assistant", "test_session", "unknown", None, ""}

        # Construir filtros: se aplica session_id solo si NO es genérica.
        # IMPORTANTE: Nunca filtrar por agent_id — búsqueda universal.
        filters = []
        if session_id and session_id not in GENERIC_SESSIONS:
            # Escapar comillas simples si existen
            safe_sid = str(session_id).replace("'", "''")
            filters.append(f"session_id eq '{safe_sid}'")

        if tipo:
            safe_tipo = str(tipo).replace("'", "''")
            filters.append(f"tipo eq '{safe_tipo}'")

        filter_str = " and ".join(filters) if filters else None

        # Ejecutar búsqueda (UNIVERSAL: sin filtro por agent_id)
        search_service = AzureSearchService()
        resultado = search_service.search(
            query=query,
            top=top,
            filters=filter_str
        )

        # Agregar metadata explicativa
        if resultado.get("exito"):
            resultado["metadata"] = {
                "query_original": query,
                "filtros_aplicados": {
                    "session_id": session_id if session_id and session_id not in GENERIC_SESSIONS else "UNIVERSAL",
                    "tipo": tipo,
                    "agent_id": "UNIVERSAL (sin filtro)"
                },
                "busqueda_universal": True,
                "modo": "universal_search",
                "filtros_odata": filter_str,
                "tiempo_busqueda": datetime.utcnow().isoformat()
            }

        logging.info(f"🔍 Búsqueda UNIVERSAL: '{query}' → {resultado.get('total', 0)} resultados; filtros: {filter_str or 'NINGUNO (universal)'}")
        return resultado

    except Exception as e:
        logging.error(f"Error en buscar_memoria: {e}")
        return {"exito": False, "error": str(e)}

def indexar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/indexar-memoria
    Indexa documentos en Azure AI Search CON EMBEDDINGS REALES
    """
    try:
        from services.azure_search_client import AzureSearchService
        from embedding_generator import generar_embedding
        
        # Validar payload
        documentos = req_body.get("documentos")
        if not documentos or not isinstance(documentos, list):
            return {"exito": False, "error": "Campo 'documentos' requerido (array)"}
        
        # Validar, normalizar y GENERAR EMBEDDINGS
        documentos_con_vectores = []
        for doc in documentos:
            if not doc.get("id"):
                return {"exito": False, "error": "Cada documento requiere campo 'id'"}
            if not doc.get("agent_id"):
                return {"exito": False, "error": "Cada documento requiere campo 'agent_id'"}
            if not doc.get("texto_semantico"):
                return {"exito": False, "error": "Cada documento requiere campo 'texto_semantico'"}
            
            # 🔥 GENERAR EMBEDDING REAL
            texto = doc["texto_semantico"]
            vector = generar_embedding(texto)
            
            if not vector:
                logging.warning(f"⚠️ No se pudo generar embedding para doc {doc['id']}, omitiendo")
                continue
            
            # Agregar vector al documento
            doc["vector"] = vector
            
            # Normalizar timestamp a formato Edm.DateTimeOffset (YYYY-MM-DDTHH:MM:SS.sssZ)
            if "timestamp" in doc:
                ts = doc["timestamp"]
                if isinstance(ts, str):
                    # Remover microsegundos excesivos y agregar Z
                    if '.' in ts:
                        base, micro = ts.split('.')
                        micro = micro[:3]  # Solo 3 dígitos de milisegundos
                        doc["timestamp"] = f"{base}.{micro}Z"
                    elif not ts.endswith('Z'):
                        doc["timestamp"] = f"{ts}Z"
            
            documentos_con_vectores.append(doc)
        
        if not documentos_con_vectores:
            return {"exito": False, "error": "No se pudieron generar embeddings para ningún documento"}
        
        # Indexar documentos CON VECTORES
        search_service = AzureSearchService()
        resultado = search_service.indexar_documentos(documentos_con_vectores)
        
        if resultado.get("exito"):
            logging.info(f"✅ Indexados {len(documentos_con_vectores)} documentos CON EMBEDDINGS en Azure Search")
        
        return resultado
        
    except Exception as e:
        logging.error(f"Error en indexar_memoria: {e}")
        return {"exito": False, "error": str(e)}
