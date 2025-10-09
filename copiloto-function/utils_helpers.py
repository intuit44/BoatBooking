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

def is_running_in_azure() -> bool:
    """Detecta si está corriendo en Azure"""
    return bool(
        os.environ.get("WEBSITE_INSTANCE_ID") or
        os.environ.get("WEBSITE_SITE_NAME") or
        os.environ.get("WEBSITE_RESOURCE_GROUP")
    )

def get_run_id(req: func.HttpRequest) -> str:
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