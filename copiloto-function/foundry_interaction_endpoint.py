"""
Endpoint: /api/foundry-interaction
Endpoint principal para interacciones con Foundry que utiliza el router de agentes
para optimización automática de modelos según la intención detectada.
"""

import json
import logging
import azure.functions as func
from typing import Dict, Any, Optional
from datetime import datetime
import os
import requests

# Importaciones necesarias
from router_agent import route_by_semantic_intent
from services.memory_service import memory_service


def create_foundry_interaction_endpoint(app: func.FunctionApp):
    """Registra el endpoint de interacción con Foundry"""

    @app.function_name(name="foundry_interaction")
    @app.route(route="foundry-interaction", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def foundry_interaction_http(req: func.HttpRequest) -> func.HttpResponse:
        """
        Endpoint principal para interacciones con Foundry con optimización de modelos.

        Flujo:
        1. Recibe input del usuario
        2. Usa router_agent para determinar intención → agente → modelo
        3. Hace llamada a Foundry con el modelo optimizado
        4. Registra todo en memoria para auditoría
        """
        try:
            # 1. Extraer datos del request
            body = req.get_json() or {}
            user_input = body.get("input") or body.get(
                "message") or body.get("query")

            if not user_input:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "error": "Campo 'input', 'message' o 'query' requerido"
                    }),
                    mimetype="application/json",
                    status_code=400
                )

            # 2. Obtener identificadores de sesión
            session_id = (
                req.headers.get("Session-ID") or
                req.headers.get("X-Session-ID") or
                body.get("session_id") or
                body.get("thread_id") or
                "default_session"
            )

            # 3. 🤖 ROUTING SEMÁNTICO - Determinar agente y modelo óptimo
            logging.info(
                f"🤖 [FoundryInteraction] Iniciando routing para: '{user_input[:50]}...'")

            routing_result = route_by_semantic_intent(
                user_message=user_input,
                session_id=session_id,
                context={"endpoint": "foundry-interaction"}
            )

            selected_model = routing_result.get("model", "gpt-4o-2024-11-20")
            selected_agent = routing_result.get("agent_id", "Agent914")
            intent = routing_result.get("routing_metadata", {}).get(
                "intent", "conversacion_general")
            confidence = routing_result.get(
                "routing_metadata", {}).get("confidence", 0.0)

            logging.info(
                f"🎯 [FoundryInteraction] Intent: {intent} → Agent: {selected_agent} → Model: {selected_model}")

            # 4. Preparar payload para Foundry
            foundry_endpoint = routing_result.get(
                "endpoint", os.getenv("AI_FOUNDRY_ENDPOINT"))
            project_id = routing_result.get(
                "project_id", os.getenv("AI_PROJECT_ID_MAIN"))

            foundry_payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                "model": selected_model,  # 🎯 MODELO OPTIMIZADO
                "agent_id": selected_agent,
                "project_id": project_id,
                "session_id": session_id,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            # 5. Registrar input del usuario en memoria CON MODELO
            try:
                memory_service.registrar_llamada(
                    source="foundry_interaction",
                    endpoint="/api/foundry-interaction",
                    method="POST",
                    params={
                        "session_id": session_id,
                        "user_input": user_input,
                        "selected_agent": selected_agent,
                        "selected_model": selected_model,  # 🎯 MODELO REGISTRADO
                        "intent": intent,
                        "confidence": confidence,
                        "routing_metadata": routing_result.get("routing_metadata", {})
                    },
                    response_data={"processing": True},
                    success=True
                )
                logging.info(
                    f"💾 [FoundryInteraction] Input registrado en memoria con modelo: {selected_model}")
            except Exception as e:
                logging.warning(f"⚠️ Error registrando input en memoria: {e}")

            # 6. Simular llamada a Foundry (reemplazar con llamada real)
            # TODO: Reemplazar con llamada HTTP real a Foundry
            simulated_response = {
                "response": f"Respuesta simulada del {selected_agent} usando {selected_model} para intent '{intent}': {user_input}",
                "model_used": selected_model,
                "agent_used": selected_agent,
                "intent_detected": intent,
                "confidence": confidence,
                "processing_time": "1.2s"
            }

            # 7. Registrar respuesta en memoria para auditoría
            try:
                memory_service.registrar_llamada(
                    source="foundry_response",
                    endpoint="/api/foundry-interaction",
                    method="POST",
                    params={
                        "session_id": session_id,
                        "selected_agent": selected_agent,
                        "selected_model": selected_model,
                        "intent": intent
                    },
                    response_data={
                        "texto_semantico": simulated_response["response"],
                        "model_usado": selected_model,  # 🎯 AUDITORÍA DE MODELO
                        "agent_usado": selected_agent,
                        "intent_detectado": intent,
                        "confidence": confidence
                    },
                    success=True
                )
                logging.info(
                    f"✅ [FoundryInteraction] Respuesta registrada con auditoría de modelo")
            except Exception as e:
                logging.warning(
                    f"⚠️ Error registrando respuesta en memoria: {e}")

            # 8. Preparar respuesta final
            response_data = {
                "success": True,
                "response": simulated_response["response"],
                "routing_info": {
                    "intent": intent,
                    "confidence": confidence,
                    "selected_agent": selected_agent,
                    "selected_model": selected_model,  # 🎯 MODELO VISIBLE EN RESPUESTA
                    "routing_timestamp": routing_result.get("routing_metadata", {}).get("routing_timestamp")
                },
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

            logging.info(
                f"🎉 [FoundryInteraction] Completado exitosamente - Model: {selected_model}, Agent: {selected_agent}")

            return func.HttpResponse(
                json.dumps(response_data, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        except Exception as e:
            error_msg = f"Error en foundry-interaction: {str(e)}"
            logging.error(error_msg)

            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                }),
                mimetype="application/json",
                status_code=500
            )

# Función para hacer llamada HTTP real a Foundry (para uso futuro)


def call_foundry_api(endpoint: str, payload: Dict[str, Any], model: str) -> Dict[str, Any]:
    """
    Hace llamada HTTP real a Foundry con el modelo especificado.

    Args:
        endpoint: URL del endpoint de Foundry
        payload: Payload para enviar a Foundry
        model: Modelo a utilizar

    Returns:
        Respuesta de Foundry
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('FOUNDRY_API_KEY', '')}",
            "X-Model": model  # 🎯 HEADER CON MODELO
        }

        response = requests.post(
            f"{endpoint}/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        logging.error(f"❌ Error calling Foundry API: {e}")
        return {
            "error": str(e),
            "model_requested": model
        }
