#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Admin endpoints para Azure Functions
-----------------------------------------
Registran rutas ligeras para comandos Redis (allowlist), diagnóstico, auditoría
e introspección de comandos permitidos. Reutiliza el redis_cli_service global.
"""

import json
import logging
import azure.functions as func
from typing import Any

from services.redis_cli_service import get_redis_cli_service

logger = logging.getLogger(__name__)

redis_cli_service = get_redis_cli_service()


def register_redis_admin_routes(app: Any) -> None:
    """Registra endpoints Redis Admin en la FunctionApp dada."""

    @app.function_name(name="redis_admin_command")
    @app.route(route="redis-admin/command", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
    def redis_admin_command(req: func.HttpRequest) -> func.HttpResponse:
        """Ejecuta comando Redis con allowlist y confirmación para comandos peligrosos."""
        try:
            body = req.get_json() or {}
        except ValueError:
            body = {}

        command = (body.get("command") or "").strip()
        agent_id = body.get("agent_id") or "unknown"
        confirm = bool(body.get("confirm", False))

        if not command:
            return func.HttpResponse(
                json.dumps({"success": False, "error": 'Parámetro "command" requerido'}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
            )

        result = redis_cli_service.execute_command(command, agent_id, confirm)
        status = 200 if result.get("success") else (400 if result.get("confirmation_required") else 500)

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            status_code=status,
            mimetype="application/json",
        )

    @app.function_name(name="redis_admin_diagnostic")
    @app.route(route="redis-admin/diagnostic", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
    def redis_admin_diagnostic(req: func.HttpRequest) -> func.HttpResponse:
        """Diagnóstico completo de Redis (ping, RedisJSON, memoria, config, stats)."""
        diagnostic = redis_cli_service.run_diagnostic()
        status = 200 if diagnostic.get("overall") != "FAILED" else 500
        return func.HttpResponse(
            json.dumps({"success": diagnostic.get("overall") != "FAILED", "diagnostic": diagnostic}, ensure_ascii=False),
            status_code=status,
            mimetype="application/json",
        )

    @app.function_name(name="redis_admin_audit")
    @app.route(route="redis-admin/audit", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
    def redis_admin_audit(req: func.HttpRequest) -> func.HttpResponse:
        """Devuelve el log de auditoría de comandos ejecutados."""
        try:
            limit = int(req.params.get("limit", 50))
        except Exception:
            limit = 50

        audit_log = redis_cli_service.get_audit_log(limit)
        return func.HttpResponse(
            json.dumps({"success": True, "audit_log": audit_log, "count": len(audit_log)}, ensure_ascii=False),
            mimetype="application/json",
        )

    @app.function_name(name="redis_admin_commands")
    @app.route(route="redis-admin/commands", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
    def redis_admin_commands(req: func.HttpRequest) -> func.HttpResponse:
        """Lista comandos permitidos (allowlist) para UI o agentes Foundry."""
        commands = redis_cli_service.get_allowed_commands()
        return func.HttpResponse(
            json.dumps({"success": True, "commands": commands, "count": len(commands)}, ensure_ascii=False),
            mimetype="application/json",
        )
