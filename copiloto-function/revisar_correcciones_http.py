#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Función revisar_correcciones_http que faltaba para el sistema de redirección
"""

import json
import logging
from datetime import datetime
import azure.functions as func

def revisar_correcciones_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    REDIRECCIÓN AUTOMÁTICA A /api/copiloto CON MEMORIA
    """
    logging.info("🔄 /api/revisar-correcciones -> Redirigiendo a /api/copiloto con memoria")
    
    try:
        # REDIRECCIÓN REAL usando requests para llamar al endpoint
        import requests
        import os
        
        # Determinar URL base
        base_url = "http://localhost:7071"  # Local por defecto
        if os.environ.get("WEBSITE_SITE_NAME"):  # Azure
            base_url = f"https://{os.environ.get('WEBSITE_SITE_NAME')}.azurewebsites.net"
        
        # Preservar headers originales
        headers = {
            "Content-Type": "application/json",
            "Session-ID": req.headers.get("Session-ID", ""),
            "Agent-ID": req.headers.get("Agent-ID", "")
        }
        
        # Parámetros para copiloto
        params = {"mensaje": "revisar correcciones pendientes"}
        
        # Hacer request HTTP al endpoint copiloto
        response = requests.get(
            f"{base_url}/api/copiloto",
            params=params,
            headers=headers,
            timeout=30
        )
        
        # Retornar la respuesta del copiloto
        return func.HttpResponse(
            response.text,
            mimetype="application/json",
            status_code=response.status_code
        )
        
    except Exception as e:
        logging.error(f"Error en redirección: {e}")
        
        # Fallback con información útil
        response = {
            "tipo": "correcciones_disponibles",
            "mensaje": "Para ver correcciones, usa /api/copiloto con memoria integrada",
            "correcciones_ejemplo": [
                {
                    "id": "fix_001",
                    "tipo": "timeout_cosmos",
                    "descripcion": "Aumentar timeout de Cosmos DB a 30s",
                    "estado": "pendiente"
                },
                {
                    "id": "fix_002", 
                    "tipo": "headers_session",
                    "descripcion": "Enviar Session-ID y Agent-ID consistentemente",
                    "estado": "aplicada"
                }
            ],
            "endpoint_recomendado": "/api/copiloto",
            "timestamp": datetime.now().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )