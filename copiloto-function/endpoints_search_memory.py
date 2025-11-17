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
    🔥 SESSION WIDENING: Cascada de búsqueda (sesión → agente → universal)
    🔧 DETECCIÓN TÉCNICA: Búsqueda literal para UUIDs e IDs
    """
    try:
        from services.azure_search_client import get_search_service
        from semantic_query_builder import detectar_query_tecnica, buscar_literal_cosmos
        from services.cosmos_store import CosmosMemoryStore

        # Validar payload
        query = req_body.get("query")
        if not query:
            return {"exito": False, "error": "Campo 'query' requerido"}

        session_id = req_body.get("session_id")
        agent_id = req_body.get("agent_id")
        top = int(req_body.get("top", 10))
        tipo = req_body.get("tipo")

        GENERIC_SESSIONS = {"assistant", "test_session", "unknown", None, ""}
        
        # 🔧 DETECTAR SI ES QUERY TÉCNICA (UUID, Client ID, etc.)
        query_tecnica = detectar_query_tecnica(query)
        
        if query_tecnica:
            # Usar búsqueda LITERAL en Cosmos DB
            logging.info(f"🔧 Query técnica detectada: {query_tecnica['tipo']} → búsqueda literal")
            try:
                cosmos_store = CosmosMemoryStore()
                if not cosmos_store.enabled or not cosmos_store.container:
                    raise Exception("Cosmos DB no disponible")
                
                documentos = buscar_literal_cosmos(
                    query_tecnica=query_tecnica,
                    cosmos_container=cosmos_store.container,
                    session_id=session_id,
                    agent_id=agent_id
                )
                
                return {
                    "exito": True,
                    "total": len(documentos),
                    "documentos": documentos[:top],
                    "metadata": {
                        "query_original": query,
                        "modo_busqueda": "literal_cosmos",
                        "query_tecnica": query_tecnica,
                        "session_widening_activo": True,
                        "tiempo_busqueda": datetime.utcnow().isoformat()
                    }
                }
            except Exception as cosmos_err:
                logging.warning(f"⚠️ Búsqueda literal falló: {cosmos_err}, fallback a vectorial")
                # Continuar con búsqueda vectorial como fallback
        
        # Búsqueda VECTORIAL normal (Azure AI Search)
        search_service = get_search_service()
        
        # 🔄 CASCADA DE BÚSQUEDA
        resultado = None
        modo_usado = None
        filtros_usados = None

        # NIVEL 1: Búsqueda en sesión específica
        if session_id and session_id not in GENERIC_SESSIONS:
            filters = []
            safe_sid = str(session_id).replace("'", "''")
            filters.append(f"session_id eq '{safe_sid}'")
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo eq '{safe_tipo}'")
            
            filter_str = " and ".join(filters)
            resultado = search_service.search(query=query, top=top, filters=filter_str)
            
            if resultado.get("exito") and resultado.get("total", 0) > 0:
                modo_usado = "session_specific"
                filtros_usados = filter_str
                logging.info(f"✅ Nivel 1: Encontrados {resultado['total']} en sesión {session_id}")
            else:
                logging.info(f"⚠️ Nivel 1: 0 resultados en sesión {session_id}, escalando...")
                resultado = None

        # NIVEL 2: Búsqueda por agent_id (todas las sesiones)
        if not resultado and agent_id and agent_id not in GENERIC_SESSIONS:
            filters = []
            safe_aid = str(agent_id).replace("'", "''")
            filters.append(f"agent_id eq '{safe_aid}'")
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo eq '{safe_tipo}'")
            
            filter_str = " and ".join(filters)
            resultado = search_service.search(query=query, top=top, filters=filter_str)
            
            if resultado.get("exito") and resultado.get("total", 0) > 0:
                modo_usado = "agent_wide"
                filtros_usados = filter_str
                logging.info(f"✅ Nivel 2: Encontrados {resultado['total']} para agent_id {agent_id}")
            else:
                logging.info(f"⚠️ Nivel 2: 0 resultados para agent_id {agent_id}, escalando...")
                resultado = None

        # NIVEL 3: Búsqueda universal (sin filtros de sesión/agente)
        if not resultado:
            filters = []
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo eq '{safe_tipo}'")
            
            filter_str = " and ".join(filters) if filters else None
            resultado = search_service.search(query=query, top=top, filters=filter_str)
            modo_usado = "universal"
            filtros_usados = filter_str or "NINGUNO"
            logging.info(f"✅ Nivel 3: Búsqueda universal → {resultado.get('total', 0)} resultados")

        # Agregar metadata explicativa
        if resultado and resultado.get("exito"):
            resultado["metadata"] = {
                "query_original": query,
                "filtros_aplicados": {
                    "session_id": session_id if session_id and session_id not in GENERIC_SESSIONS else "no aplicado",
                    "tipo": tipo,
                    "agent_id": agent_id if agent_id and agent_id not in GENERIC_SESSIONS else "no aplicado"
                },
                "modo_busqueda": modo_usado,
                "session_widening_activo": True,
                "filtros_odata": filtros_usados,
                "tiempo_busqueda": datetime.utcnow().isoformat()
            }

        if resultado:
            logging.info(f"🔍 Búsqueda '{query}' → {resultado.get('total', 0)} resultados [modo: {modo_usado}]")
        return resultado or {"exito": False, "error": "No se pudo completar la búsqueda"}

    except Exception as e:
        logging.error(f"Error en buscar_memoria: {e}")
        return {"exito": False, "error": str(e)}


def indexar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/indexar-memoria
    Indexa documentos en Azure AI Search CON EMBEDDINGS REALES
    """
    try:
        from services.azure_search_client import get_search_service
        from embedding_generator import generar_embedding
        from services.memory_service import MemoryService

        memory_service = MemoryService()

        # Validar payload
        documentos = req_body.get("documentos")
        if not documentos or not isinstance(documentos, list):
            return {"exito": False, "error": "Campo 'documentos' requerido (array)"}

        documentos_con_vectores = []
        duplicados = 0
        indexados = 0

        for doc in documentos:
            if not doc.get("id"):
                logging.warning("Documento omitido: falta 'id'")
                continue
            if not doc.get("agent_id"):
                logging.warning(
                    f"Documento {doc.get('id')} omitido: falta 'agent_id'")
                continue
            if not doc.get("texto_semantico"):
                logging.warning(
                    f"Documento {doc.get('id')} omitido: falta 'texto_semantico'")
                continue

            texto = doc["texto_semantico"]

            try:
                if memory_service.evento_ya_existe(texto):
                    duplicados += 1
                    logging.info(
                        f"⏭️ Duplicado detectado: {doc['id']} — omitido")
                    continue
            except Exception as mem_err:
                logging.warning(
                    f"Error verificando duplicado en {doc['id']}: {mem_err} — se continúa")

            vector = generar_embedding(texto)
            if not vector:
                logging.warning(
                    f"⚠️ No se pudo generar embedding para {doc['id']}, omitido")
                continue

            doc["vector"] = vector

            if "timestamp" in doc:
                ts = doc["timestamp"]
                if isinstance(ts, str):
                    if '.' in ts:
                        base, micro = ts.split('.')
                        micro = micro[:3]
                        doc["timestamp"] = f"{base}.{micro}Z"
                    elif not ts.endswith('Z'):
                        doc["timestamp"] = f"{ts}Z"

            documentos_con_vectores.append(doc)

        if not documentos_con_vectores:
            return {
                "exito": True,
                "indexados": 0,
                "duplicados": duplicados,
                "mensaje": "Todos los documentos eran duplicados o inválidos"
            }

        search_service = get_search_service()
        resultado = search_service.indexar_documentos(documentos_con_vectores)

        indexados = len(documentos_con_vectores)

        if resultado.get("exito"):
            logging.info(
                f"✅ Indexados {indexados} documentos CON EMBEDDINGS en Azure Search")

        return {
            "exito": resultado.get("exito", False),
            "indexados": indexados,
            "duplicados": duplicados,
            "error": resultado.get("error") if not resultado.get("exito") else None
        }

    except Exception as e:
        logging.error(f"Error en indexar_memoria: {e}")
        return {"exito": False, "error": str(e)}
