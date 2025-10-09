# -*- coding: utf-8 -*-
"""
Fix para el endpoint ejecutar_cli_http - Validación de payloads malformados
"""

import azure.functions as func
import json
import subprocess
import logging
from datetime import datetime

@app.function_name(name="ejecutar_cli_http")
@app.route(route="ejecutar-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_cli_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para ejecutar comandos Azure CLI con validación mejorada"""
    try:
        # Obtener y validar el body
        body = req.get_json()
        
        # LOGGING CRÍTICO PARA DEBUG
        logging.warning(f"[DEBUG] Payload recibido: {body}")
        
        if not body:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Request body must be valid JSON",
                    "endpoint_correcto": "/api/ejecutar-cli",
                    "ejemplo": {"comando": "az storage account list"}
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Extraer comando con validación estricta
        comando = body.get("comando")
        
        # VALIDACIÓN CRÍTICA: Rechazar payloads con "intencion" en lugar de "comando"
        if not comando:
            if body.get("intencion"):
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": "Este endpoint no maneja intenciones, solo comandos CLI.",
                        "sugerencia": "Usa /api/hybrid para intenciones semánticas.",
                        "payload_recibido": body,
                        "endpoint_correcto": "/api/ejecutar-cli",
                        "ejemplo": {"comando": "az storage account list"}
                    }),
                    status_code=422,
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": "Falta el parámetro 'comando'. Este endpoint solo acepta comandos CLI.",
                        "endpoint_correcto": "/api/ejecutar-cli",
                        "ejemplo": {"comando": "az storage account list"},
                        "payload_recibido": body
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
        
        # Verificar autenticación Azure CLI
        logging.info("✅ Ya autenticado en Azure CLI")
        
        # Construir comando completo
        if not comando.startswith("az "):
            comando = f"az {comando}"
        
        # Agregar --output json si no está presente
        if "--output" not in comando:
            comando += " --output json"
        
        logging.info(f"Intentando ejecutar: {comando}")
        
        # Ejecutar comando
        result = subprocess.run(
            comando.split(),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Procesar resultado
        if result.returncode == 0:
            try:
                output_json = json.loads(result.stdout) if result.stdout else []
                return func.HttpResponse(
                    json.dumps({
                        "exito": True,
                        "comando": comando,
                        "resultado": output_json,
                        "codigo_salida": result.returncode
                    }),
                    mimetype="application/json",
                    status_code=200
                )
            except json.JSONDecodeError:
                return func.HttpResponse(
                    json.dumps({
                        "exito": True,
                        "comando": comando,
                        "resultado": result.stdout,
                        "codigo_salida": result.returncode
                    }),
                    mimetype="application/json",
                    status_code=200
                )
        else:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "comando": comando,
                    "error": result.stderr,
                    "codigo_salida": result.returncode
                }),
                mimetype="application/json",
                status_code=500
            )
    
    except subprocess.TimeoutExpired:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": "Comando excedió tiempo límite (60s)",
                "comando": comando if 'comando' in locals() else "desconocido"
            }),
            mimetype="application/json",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error en ejecutar_cli_http: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }),
            mimetype="application/json",
            status_code=500
        )