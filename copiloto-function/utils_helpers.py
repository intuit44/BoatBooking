#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares mínimas para el sistema
"""

import os
import uuid
import azure.functions as func
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

def is_running_in_azure() -> bool:
    """Detecta si está corriendo en Azure"""
    return bool(
        os.environ.get("WEBSITE_INSTANCE_ID") or
        os.environ.get("WEBSITE_SITE_NAME") or
        os.environ.get("WEBSITE_RESOURCE_GROUP")
    )

# Variables globales
IS_AZURE = is_running_in_azure()
PROJECT_ROOT = Path("/home/site/wwwroot" if IS_AZURE else os.getcwd())
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "boat-rental-project")

def get_blob_client():
    """Obtiene cliente de Blob Storage"""
    try:
        from azure.storage.blob import BlobServiceClient
        from azure.identity import DefaultAzureCredential
        
        connection_string = os.environ.get("AzureWebJobsStorage")
        if connection_string:
            return BlobServiceClient.from_connection_string(connection_string)
        
        account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
        if account_url:
            return BlobServiceClient(account_url, credential=DefaultAzureCredential())
        
        return None
    except Exception:
        return None

def get_run_id(req: func.HttpRequest = None) -> str:
    """Genera un ID único para la request"""
    return uuid.uuid4().hex[:8]

def api_ok(endpoint: str, method: str, status: int, message: str, details: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Respuesta exitosa estándar"""
    result = {
        "ok": True,
        "status": status,
        "message": message,
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        result["data"] = details
    if run_id:
        result["run_id"] = run_id
    return result

def api_err(endpoint: str, method: str, status: int, code: str, reason: str, missing_params: Any = None, run_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Respuesta de error estándar"""
    result = {
        "ok": False,
        "status": status,
        "error_code": code,
        "message": reason,
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    if missing_params:
        result["missing_params"] = missing_params
    if run_id:
        result["run_id"] = run_id
    if details:
        result["details"] = details
    return result