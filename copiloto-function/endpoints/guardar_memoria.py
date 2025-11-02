"""
Endpoint: /api/guardar-memoria
Permite al agente guardar contenido intencionalmente en memoria vectorial
"""
import logging
import json
import os
import sys
from datetime import datetime
import azure.functions as func

# Importar el app principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from function_app import app
from services.memory_service import memory_service

@app.function_name(name="guardar_memoria")
@app.route(route="guardar-memoria", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def guardar_memoria_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para guardar contenido explícitamente en memoria
    El agente decide QUÉ es importante, no heurísticas automáticas
    """
    
    try:
        body = req.get_json()
        
        # Validar parámetros requeridos
        contenido = body.get("contenido")
        if not contenido:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'contenido' requerido",
                    "ejemplo": {
                        "contenido": "Resumen de la conversación...",
                        "tipo": "resumen_conversacion",
                        "session_id": "assistant",
                        "metadata": {"importancia": "alta"}
                    }
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        # Extraer parámetros opcionales
        tipo = body.get("tipo", "memoria_manual")
        session_id = body.get("session_id") or req.headers.get("Session-ID") or "unknown"
        agent_id = body.get("agent_id") or req.headers.get("Agent-ID")
        metadata = body.get("metadata", {})
        
        # Registrar en memoria usando el servicio existente
        # ✅ texto_semantico va dentro de response_data, no como parámetro separado
        memory_service.registrar_llamada(
            source="guardar_memoria",
            endpoint="/api/guardar-memoria",
            method="POST",
            params={
                "tipo": tipo,
                "session_id": session_id,
                "agent_id": agent_id,
                "metadata": metadata
            },
            response_data={
                "texto_semantico": contenido,  # ✅ El contenido se guarda como texto semántico
                "contenido_guardado": True,
                "longitud": len(contenido)
            },
            success=True
        )
        
        logging.info(f"🧠 Memoria guardada: {len(contenido)} chars, tipo={tipo}, session={session_id}")
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "mensaje": "Contenido guardado en memoria vectorial",
                "detalles": {
                    "longitud": len(contenido),
                    "tipo": tipo,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": "Body JSON inválido"
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error en guardar-memoria: {e}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e)
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
