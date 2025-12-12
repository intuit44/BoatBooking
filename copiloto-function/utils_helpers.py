#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares mínimas para el sistema
"""

import os
import uuid
import azure.functions as func
from datetime import datetime
from typing import Dict, Any, Optional, List
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

def get_run_id(req: Optional[func.HttpRequest] = None) -> str:
    """Genera un ID único para la request"""
    return uuid.uuid4().hex[:8]


def preview_text(text: Any, limit: int = 1000) -> str:
    if text is None:
        return ""
    s = str(text)
    return s if len(s) <= limit else s[:limit] + "..."


def format_timestamp_humano(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "sin fecha"
    try:
        ts = timestamp.replace("Z", "+00:00") if timestamp.endswith("Z") else timestamp
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return timestamp


def humanizar_endpoint(endpoint: Optional[str]) -> str:
    if not endpoint:
        return "actividad desconocida"
    limpio = endpoint.strip("/").replace("_", " ").replace("-", " ").strip()
    return limpio or "actividad desconocida"


def build_event(endpoint: str,
                descripcion: str,
                estado: str = "informativo",
                sugerencia: str = "",
                criticidad: str = "informativa",
                datos: Optional[Dict[str, Any]] = None,
                timestamp: Optional[str] = None) -> Dict[str, Any]:
    return {
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "descripcion": descripcion,
        "estado": estado,
        "sugerencia": sugerencia,
        "criticidad": criticidad,
        "datos": datos or {}
    }


def build_structured_payload(endpoint: str,
                             events: List[Dict[str, Any]],
                             narrativa_base: str = "",
                             resumen_automatico: str = "",
                             extras: Optional[Dict[str, Any]] = None,
                             contexto_inteligente: Optional[Dict[str, Any]] = None,
                             exito: Optional[bool] = None) -> Dict[str, Any]:
    eventos = events or []
    if exito is None:
        exito = not any(e.get("estado") == "error" for e in eventos)
    texto_semantico = "\n".join(
        filter(None, [e.get("descripcion", "") for e in eventos])
    )
    payload: Dict[str, Any] = {
        "exito": exito,
        "endpoint": endpoint,
        "eventos": eventos,
        "narrativa_base": narrativa_base,
        "resumen_automatico": resumen_automatico,
        "respuesta_usuario": "",
        "texto_semantico": texto_semantico,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if extras:
        payload["detalles_operacion"] = extras
    if contexto_inteligente:
        payload["contexto_inteligente"] = contexto_inteligente
    return payload


def api_ok(endpoint: str, method: str, status: int, message: str, details: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Respuesta exitosa estándar estructurada (mantiene compatibilidad legacy)."""
    legacy = {
        "ok": True,
        "status": status,
        "message": message,
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        legacy["data"] = details
    if run_id:
        legacy["run_id"] = run_id
    evento = build_event(
        endpoint=endpoint,
        descripcion=message,
        estado="exito",
        sugerencia="",
        criticidad="informativa",
        datos=details or {}
    )
    payload = build_structured_payload(endpoint, [evento], extras={"legacy": legacy}, exito=True)
    payload.update(legacy)
    payload["legacy"] = legacy
    return payload


def api_err(endpoint: str, method: str, status: int, code: str, reason: str, missing_params: Any = None, run_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Respuesta de error estándar estructurada (mantiene compatibilidad legacy)."""
    legacy = {
        "ok": False,
        "status": status,
        "error_code": code,
        "message": reason,
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    if missing_params:
        legacy["missing_params"] = missing_params
    if run_id:
        legacy["run_id"] = run_id
    if details:
        legacy["details"] = details
    datos = details.copy() if details else {}
    if missing_params:
        datos["missing_params"] = missing_params
    evento = build_event(
        endpoint=endpoint,
        descripcion=reason,
        estado="error",
        sugerencia="",
        criticidad="alta",
        datos=datos
    )
    payload = build_structured_payload(endpoint, [evento], extras={"legacy": legacy}, exito=False)
    payload.update(legacy)
    payload["legacy"] = legacy
    return payload
