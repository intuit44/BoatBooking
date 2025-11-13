"""
Endpoint: /api/agent-output
Recibe salidas "autónomas" del agente en Foundry y las registra en memoria.

Payload esperado (application/json):
{
  "thread_id": "thread_..." (o "session_id"),
  "agent_id": "AgentXYZ" (opcional),
  "texto": "respuesta del agente",  // requerido
  "metadata": { ... }                // opcional
}

Respuestas:
- 200 exito True cuando se registra
- 400 si falta texto o identificadores
"""

import json
import logging
import azure.functions as func
from function_app import app

try:
    # Reutiliza pipeline de salida de agente
    from thread_memory_hook import registrar_output_agente
except Exception:
    registrar_output_agente = None  # Fallback más abajo


@app.function_name(name="agent_output")
@app.route(route="agent-output", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def agent_output_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            body = req.get_json()
        except Exception:
            body = None

        if not isinstance(body, dict):
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Body inválido o ausente",
                    "hint": "Envíe JSON con texto y thread_id",
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        # Normalización de campos
        session_id = body.get("thread_id") or body.get("session_id")
        agent_id = body.get("agent_id") or req.headers.get("Agent-ID") or req.headers.get("X-Agent-ID") or "foundry_user"
        texto = body.get("texto") or body.get("respuesta") or body.get("mensaje")
        metadata = body.get("metadata") or {}

        if not texto or not isinstance(texto, str) or len(texto.strip()) < 2:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Campo 'texto' requerido",
                    "hint": "Incluya el texto de salida del agente",
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        if not session_id or not isinstance(session_id, str):
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Falta 'thread_id' (o 'session_id')",
                    "hint": "Proporcione el ID de thread de Foundry",
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        # Registrar usando el hook (pipeline unificado)
        try:
            if callable(registrar_output_agente):
                registrar_output_agente(agent_id=agent_id, session_id=session_id, output_text=texto, metadata=metadata)
                ok = True
            else:
                # Fallback directo al memory_service si el hook no está disponible
                from services.memory_service import memory_service
                memory_service.registrar_llamada(
                    source="agent_output",
                    endpoint="agent_output",
                    method="POST",
                    params={"session_id": session_id, "agent_id": agent_id},
                    response_data={"texto_semantico": texto, "metadata": metadata},
                    success=True,
                )
                ok = True
        except Exception as e:
            logging.error(f"Error registrando salida de agente: {e}")
            ok = False

        status = 200 if ok else 500
        return func.HttpResponse(
            json.dumps({
                "exito": ok,
                "mensaje": "Salida registrada" if ok else "Fallo al registrar salida",
                "session_id": session_id,
                "agent_id": agent_id,
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=status,
        )

    except Exception as e:
        logging.error(f"/api/agent-output error: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )

