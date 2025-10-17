# -*- coding: utf-8 -*-
"""
Memory Route Wrapper - Envoltura automática para Azure Functions
Aplica lectura y escritura de memoria semántica sin modificar los endpoints originales.
"""

import logging
import azure.functions as func
import json
import time
from typing import Callable


def memory_route(app: func.FunctionApp) -> Callable:
    """Fábrica que envuelve app.route para aplicar memoria automáticamente."""
    original_route = app.route

    def route_with_memory(*args, **kwargs) -> Callable:
        def decorator(func_ref: Callable) -> Callable:
            try:
                route_path = kwargs.get("route", "")
                source_name = route_path.strip("/").replace("-", "_") or func_ref.__name__

                def wrapper(req: func.HttpRequest) -> func.HttpResponse:
                    """Lectura y escritura de memoria automática."""
                    logging.warning(f"🚨 Wrapper ACTIVADO en endpoint: {source_name}")
                    from services.memory_service import memory_service

                    # 1️⃣ LEER MEMORIA PREVIA
                    try:
                        session_id = (
                            req.headers.get("Session-ID")
                            or req.params.get("session_id")
                            or "constant-session-id"
                        )
                        interacciones = memory_service.get_session_history(session_id)
                        memoria_previa = {
                            "tiene_historial": len(interacciones) > 0,
                            "interacciones_recientes": interacciones,
                            "total_interacciones": len(interacciones),
                            "session_id": session_id,
                        }
                        setattr(req, "_memoria_contexto", memoria_previa)

                        if memoria_previa["tiene_historial"]:
                            logging.info(f"🧠 [{source_name}] Contexto cargado: {len(interacciones)} interacciones")
                        else:
                            logging.info(f"🧠 [{source_name}] Sin memoria previa")
                    except Exception as e:
                        logging.warning(f"⚠️ [{source_name}] No se pudo cargar memoria: {e}")
                        setattr(req, "_memoria_contexto", {})

                    # 2️⃣ EJECUTAR ENDPOINT ORIGINAL
                    response = func_ref(req)

                    # === Registro de nueva interacción en Cosmos ===
                    try:
                        from services.memory_service import memory_service
                        session_id = (
                            req.headers.get("Session-ID")
                            or req.params.get("session_id")
                            or "constant-session-id"
                        )
                        agent_id = (
                            req.headers.get("Agent-ID")
                            or req.params.get("agent_id")
                            or "unknown_agent"
                        )

                        # Procesar el cuerpo de respuesta si existe
                        if isinstance(response, func.HttpResponse):
                            body = response.get_body()
                            output_data = json.loads(body.decode("utf-8")) if body else {"status": response.status_code}
                        else:
                            output_data = {"raw_response": True}

                        memory_service.registrar_llamada(
                            source=source_name,
                            endpoint=route_path,
                            method=req.method,
                            params={"session_id": session_id, "agent_id": agent_id},
                            response_data=output_data,
                            success=True
                        )

                        logging.info(f"💾 [{source_name}] Interacción registrada en Cosmos ✅ - sesión {session_id}")
                    except Exception as e:
                        logging.warning(f"⚠️ [{source_name}] Error registrando llamada: {e}")

                    return response

                logging.info(f"✅ Memoria automática aplicada a endpoint: {route_path}")
                return original_route(*args, **kwargs)(wrapper)

            except Exception as e:
                logging.error(f"💥 Error crítico en wrapper: {e}")
                return original_route(*args, **kwargs)(func_ref)

        return decorator

    return route_with_memory


def apply_memory_wrapper(app: func.FunctionApp) -> None:
    """Aplica el wrapper de memoria a una instancia de FunctionApp."""
    try:
        if not hasattr(app, "route") or not callable(app.route):
            logging.error("❌ app.route no existe o no es callable")
            return

        app.route = memory_route(app)
        logging.info("🧠 Memory wrapper aplicado exitosamente a app.route")

    except Exception as e:
        logging.error(f"💥 Error aplicando memory wrapper: {e}")
        logging.warning("La aplicación continuará sin memoria automática")


def wrap_function_app_with_memory(app: func.FunctionApp) -> func.FunctionApp:
    """Envuelve una FunctionApp con memoria automática y la retorna."""
    apply_memory_wrapper(app)
    logging.info("🚀 FunctionApp envuelta con sistema de memoria automática")
    return app
