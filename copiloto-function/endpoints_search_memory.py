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
    """
    try:
        from services.azure_search_client import AzureSearchService
        
        # Validar payload
        query = req_body.get("query")
        if not query:
            return {"exito": False, "error": "Campo 'query' requerido"}
        
        agent_id = req_body.get("agent_id")
        session_id = req_body.get("session_id")
        top = req_body.get("top", 10)
        tipo = req_body.get("tipo")
        
        # Construir filtros
        filters = []
        if agent_id:
            filters.append(f"agent_id eq '{agent_id}'")
        if session_id:
            filters.append(f"session_id eq '{session_id}'")
        if tipo:
            filters.append(f"tipo eq '{tipo}'")
        
        filter_str = " and ".join(filters) if filters else None
        
        # Ejecutar búsqueda
        search_service = AzureSearchService()
        resultado = search_service.search(
            query=query,
            top=top,
            filters=filter_str
        )
        
        # Agregar metadata
        if resultado.get("exito"):
            resultado["metadata"] = {
                "query_original": query,
                "filtros_aplicados": {
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "tipo": tipo
                },
                "tiempo_busqueda": datetime.utcnow().isoformat()
            }
        
        logging.info(f"🔍 Búsqueda semántica: '{query}' → {resultado.get('total', 0)} resultados")
        return resultado
        
    except Exception as e:
        logging.error(f"Error en buscar_memoria: {e}")
        return {"exito": False, "error": str(e)}

def indexar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/indexar-memoria
    Indexa documentos en Azure AI Search
    """
    try:
        from services.azure_search_client import AzureSearchService
        
        # Validar payload
        documentos = req_body.get("documentos")
        if not documentos or not isinstance(documentos, list):
            return {"exito": False, "error": "Campo 'documentos' requerido (array)"}
        
        # Validar campos requeridos
        for doc in documentos:
            if not doc.get("id"):
                return {"exito": False, "error": "Cada documento requiere campo 'id'"}
            if not doc.get("agent_id"):
                return {"exito": False, "error": "Cada documento requiere campo 'agent_id'"}
            if not doc.get("texto_semantico"):
                return {"exito": False, "error": "Cada documento requiere campo 'texto_semantico'"}
        
        # Indexar documentos
        search_service = AzureSearchService()
        resultado = search_service.indexar_documentos(documentos)
        
        if resultado.get("exito"):
            logging.info(f"📊 Indexados {len(documentos)} documentos en Azure Search")
        
        return resultado
        
    except Exception as e:
        logging.error(f"Error en indexar_memoria: {e}")
        return {"exito": False, "error": str(e)}
