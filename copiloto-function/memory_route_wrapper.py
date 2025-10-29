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

                    # 1️⃣ CONSULTAR MEMORIA COSMOS DIRECTAMENTE
                    memoria_previa = {}
                    try:
                        from cosmos_memory_direct import consultar_memoria_cosmos_directo
                        memoria = consultar_memoria_cosmos_directo(req)
                        
                        if memoria and memoria.get("tiene_historial"):
                            memoria_previa = memoria
                            logging.info(f"🧠 [{source_name}] Memoria cargada: {memoria['total_interacciones']} interacciones con texto_semantico")
                        else:
                            memoria_previa = {"tiene_historial": False, "nueva_sesion": True}
                            logging.info(f"🧠 [{source_name}] Sin memoria previa")
                            
                        setattr(req, "_memoria_contexto", memoria_previa)
                    except Exception as e:
                        logging.warning(f"⚠️ [{source_name}] Error consultando memoria: {e}")
                        setattr(req, "_memoria_contexto", {"tiene_historial": False})

                    # 2️⃣ EJECUTAR ENDPOINT ORIGINAL
                    response = func_ref(req)
                    
                    # 3️⃣ INYECTAR CONTEXTO DE MEMORIA EN RESPUESTA
                    try:
                        if isinstance(response, func.HttpResponse):
                            body = response.get_body()
                            if body:
                                response_data = json.loads(body.decode("utf-8"))
                                
                                if isinstance(response_data, dict):
                                    # SIEMPRE inyectar metadata del wrapper
                                    if "metadata" not in response_data:
                                        response_data["metadata"] = {}
                                    response_data["metadata"]["wrapper_aplicado"] = True
                                    
                                    # Si hay memoria, inyectar contexto
                                    if memoria_previa.get("tiene_historial"):
                                        response_data["contexto_conversacion"] = {
                                            "mensaje": f"Continuando conversación con {memoria_previa['total_interacciones']} interacciones previas",
                                            "ultimas_consultas": memoria_previa.get("resumen_conversacion", ""),
                                            "session_id": memoria_previa["session_id"],
                                            "ultima_actividad": memoria_previa.get("ultima_actividad")
                                        }
                                        response_data["metadata"]["memoria_aplicada"] = True
                                        response_data["metadata"]["interacciones_previas"] = memoria_previa["total_interacciones"]
                                        logging.info(f"🧠 [{source_name}] Contexto inyectado: {memoria_previa['total_interacciones']} interacciones")
                                    else:
                                        response_data["metadata"]["nueva_sesion"] = True
                                        response_data["metadata"]["memoria_aplicada"] = False
                                    
                                    # Crear nueva respuesta
                                    new_body = json.dumps(response_data, ensure_ascii=False)
                                    response = func.HttpResponse(
                                        new_body,
                                        mimetype="application/json",
                                        status_code=response.status_code,
                                        headers={k: v for k, v in response.headers.items()} if response.headers else {}
                                    )
                    except Exception as e:
                        logging.warning(f"⚠️ [{source_name}] Error procesando respuesta: {e}")

                    # 4️⃣ REGISTRO DE NUEVA INTERACCIÓN EN COSMOS
                    # ❌ EXCLUIR historial-interacciones para evitar recursión infinita
                    es_endpoint_historial = (
                        "historial" in route_path.lower() or 
                        "historial" in source_name.lower() or
                        route_path.endswith("/historial-interacciones")
                    )
                    
                    if not es_endpoint_historial:
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

                            # Generar texto_semantico para la respuesta (limitado para evitar anidación)
                            texto_semantico = f"Interacción en '{route_path}' ejecutada por {agent_id}. Éxito: ✅. Endpoint: {source_name}."
                            if isinstance(output_data, dict):
                                # Limpiar campos verbosos antes de guardar
                                output_data_limpio = {
                                    k: v for k, v in output_data.items() 
                                    if k not in ["interacciones", "mensaje", "respuesta_usuario", "mensaje_original"]
                                }
                                # TRUNCAR texto_semantico si es muy largo (máximo 500 caracteres)
                                if "texto_semantico" in output_data:
                                    texto_original = str(output_data["texto_semantico"])
                                    if len(texto_original) > 500:
                                        output_data_limpio["texto_semantico"] = texto_original[:500] + "..."
                                        logging.info(f"🔪 texto_semantico truncado de {len(texto_original)} a 500 caracteres")
                                    else:
                                        output_data_limpio["texto_semantico"] = texto_original
                                else:
                                    output_data_limpio["texto_semantico"] = texto_semantico
                                output_data = output_data_limpio
                            
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
                    else:
                        logging.info(f"⏭️ [{source_name}] Endpoint de historial excluido del registro")

                    return response

                if "historial" not in route_path.lower():
                    logging.info(f"✅ Memoria automática aplicada a endpoint: {route_path}")
                else:
                    logging.info(f"⏭️ Endpoint de historial: wrapper aplicado SIN registro")
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
