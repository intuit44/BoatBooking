# -*- coding: utf-8 -*-
"""
Memory Route Wrapper - Envoltura automática para Azure Functions
Aplica lectura y escritura de memoria semántica sin modificar los endpoints originales.
"""
import os
import logging
import azure.functions as func
import json
import time
from typing import Callable
from datetime import datetime
from azure.storage.queue import QueueClient

def recuperar_contexto_conversacional(session_id: str, endpoint_actual: str) -> str:
    """
    Recupera el contexto conversacional desde la última invocación de endpoint.
    Retorna el bloque de conversación entre la última acción y esta.
    """
    try:
        from services.memory_service import memory_service
        
        # Obtener historial de la sesión
        interacciones = memory_service.get_session_history(session_id, limit=50)
        
        if not interacciones:
            return ""
        
        # Buscar la última invocación de endpoint (excluyendo context_snapshot)
        contexto_acumulado = []
        
        for interaccion in interacciones:
            source = interaccion.get("data", {}).get("source", "")
            
            # Si encontramos otra invocación de endpoint, detenemos
            if source != "context_snapshot" and source != "guardar_memoria":
                break
            
            # Acumular texto semántico
            texto = interaccion.get("texto_semantico", "")
            if texto and len(texto) > 20:
                contexto_acumulado.append(texto)
        
        # Retornar contexto concatenado
        if contexto_acumulado:
            return " | ".join(reversed(contexto_acumulado))  # Orden cronológico
        
        return ""
    
    except Exception as e:
        logging.warning(f"⚠️ Error recuperando contexto: {e}")
        return ""

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

                    # 1.5️⃣ BÚSQUEDA VECTORIAL EN AI SEARCH (LECTURA)
                    docs_vectoriales = []
                    try:
                        from endpoints_search_memory import buscar_memoria_endpoint
                        
                        # Extraer query del usuario
                        query_usuario = ""
                        try:
                            body = req.get_json() or {}
                            query_usuario = body.get("mensaje") or body.get("query") or body.get("consulta") or ""
                        except:
                            query_usuario = req.params.get("q") or req.params.get("mensaje") or ""
                        
                        if query_usuario and len(query_usuario) > 3:
                            session_id = req.headers.get("Session-ID") or req.params.get("session_id")
                            
                            memoria_payload = {
                                "query": query_usuario,
                                "session_id": session_id,
                                "top": 5
                            }
                            
                            resultado_vectorial = buscar_memoria_endpoint(memoria_payload)
                            
                            if resultado_vectorial.get("exito") and resultado_vectorial.get("documentos"):
                                docs_vectoriales = resultado_vectorial["documentos"]
                                logging.info(f"🔍 [{source_name}] AI Search: {len(docs_vectoriales)} docs vectoriales encontrados")
                                
                                # Inyectar en memoria_previa
                                if memoria_previa:
                                    memoria_previa["docs_vectoriales"] = docs_vectoriales
                                    memoria_previa["fuente_datos"] = "Cosmos+AISearch"
                    except Exception as e:
                        logging.warning(f"⚠️ [{source_name}] Error en búsqueda vectorial: {e}")

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

                    # 4️⃣ CAPTURA AUTOMÁTICA DE CONTEXTO CONVERSACIONAL
                    # 📸 Guardar snapshot del contexto previo a la invocación
                    try:
                        session_id = (
                            req.headers.get("Session-ID")
                            or req.params.get("session_id")
                            or "constant-session-id"
                        )
                        
                        # Recuperar contexto conversacional desde la última invocación
                        contexto_previo = recuperar_contexto_conversacional(session_id, route_path)
                        
                        if contexto_previo and len(contexto_previo) > 100:
                            # Guardar snapshot de contexto
                            memory_service.registrar_llamada(
                                source="context_snapshot",
                                endpoint=route_path,
                                method="AUTO",
                                params={"session_id": session_id, "trigger": route_path},
                                response_data={
                                    "texto_semantico": f"📸 Contexto previo a {route_path}: {contexto_previo[:4096]}",
                                    "tipo": "context_snapshot",
                                    "longitud": len(contexto_previo)
                                },
                                success=True
                            )
                            logging.info(f"📸 Context snapshot guardado: {len(contexto_previo)} chars")
                    except Exception as e:
                        logging.warning(f"⚠️ Error capturando contexto: {e}")
                    
                    # 5️⃣ REGISTRO DE NUEVA INTERACCIÓN EN COSMOS
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

                            # 🧠 EXTRACCIÓN COGNITIVA AGNÓSTICA - Prioriza voz del agente
                            texto_semantico = None
                            origen_semantico = "fallback"
                            
                            if isinstance(output_data, dict):
                                # 1️⃣ VOZ DEL AGENTE (máxima prioridad cognitiva)
                                for campo in ["respuesta_usuario", "respuesta", "resultado", "output"]:
                                    if output_data.get(campo):
                                        valor = str(output_data[campo]).strip()
                                        if len(valor) > 20:  # Mínimo semántico
                                            texto_semantico = f"💬 {valor[:2000]}"
                                            origen_semantico = "voz_agente"
                                            break
                                
                                # 2️⃣ RESUMEN TÉCNICO/SEMÁNTICO (generado por endpoint)
                                if not texto_semantico and output_data.get("texto_semantico"):
                                    valor = str(output_data["texto_semantico"]).strip()
                                    if len(valor) > 20:
                                        texto_semantico = valor[:2000]
                                        origen_semantico = "endpoint_semantico"
                                
                                # 3️⃣ MENSAJE INFORMATIVO (feedback del sistema)
                                if not texto_semantico and output_data.get("mensaje"):
                                    valor = str(output_data["mensaje"]).strip()
                                    if len(valor) > 20 and "CONSULTA DE HISTORIAL" not in valor:
                                        texto_semantico = f"📝 {valor[:2000]}"
                                        origen_semantico = "mensaje_sistema"
                                
                                # 4️⃣ CONTENIDO PROCESADO (agnóstico - cualquier endpoint)
                                if not texto_semantico and output_data.get("contenido"):
                                    contenido = str(output_data["contenido"]).strip()
                                    if len(contenido) > 50:
                                        resumen = contenido[:300] + "..." if len(contenido) > 300 else contenido
                                        ruta = output_data.get("ruta", output_data.get("archivo", "datos"))
                                        texto_semantico = f"📄 Procesado '{ruta}' ({len(contenido)} chars): {resumen}"
                                        origen_semantico = "contenido_procesado"
                                
                                # 5️⃣ FALLBACK TÉCNICO (última opción)
                                if not texto_semantico:
                                    if output_data.get("exito") or output_data.get("success"):
                                        estado = "exitoso"
                                    elif output_data.get("error"):
                                        estado = f"error: {str(output_data['error'])[:100]}"
                                    else:
                                        estado = "completado"
                                    texto_semantico = f"⚙️ Operación técnica {estado}"
                                    origen_semantico = "fallback_tecnico"
                            
                            # Validación final
                            if not texto_semantico or len(texto_semantico.strip()) < 10:
                                texto_semantico = f"⚙️ Interacción técnica en {route_path}"
                                origen_semantico = "fallback_minimo"
                            
                            # Limpiar campos verbosos
                            output_data_limpio = {
                                k: v for k, v in output_data.items() 
                                if k not in ["interacciones", "contenido", "mensaje_original"]
                            } if isinstance(output_data, dict) else output_data
                            
                            if isinstance(output_data_limpio, dict):
                                output_data_limpio["texto_semantico"] = texto_semantico
                                output_data = output_data_limpio
                            
                            logging.info(f"🧠 Semántica capturada [{origen_semantico}]: {texto_semantico[:100]}...")
                            
                            # Solo guardar si hay valor semántico real
                            if origen_semantico not in ["fallback_minimo"] or len(texto_semantico) > 30:
                                memory_service.registrar_llamada(
                                    source=source_name,
                                    endpoint=route_path,
                                    method=req.method,
                                    params={"session_id": session_id, "agent_id": agent_id},
                                    response_data=output_data,
                                    success=True
                                )
                                logging.info(f"💾 [{source_name}] Memoria cognitiva guardada ✅")
                                
                                # 🔥 Enviar a cola para indexación semántica
                                try:
                                    conn_str = os.environ.get("AzureWebJobsStorage")
                                    if not conn_str:
                                        logging.warning("⚠️ AzureWebJobsStorage no configurado: se omite envío a cola de indexación")
                                    else:
                                        queue_client = QueueClient.from_connection_string(
                                            conn_str,
                                            "memory-indexing-queue"
                                        )
                                        evento = {
                                            "id": f"{session_id}_{int(time.time())}",
                                            "agent_id": agent_id,
                                            "session_id": session_id,
                                            "endpoint": route_path,
                                            "timestamp": datetime.now().isoformat(),
                                            "event_type": "endpoint_call",
                                            "texto_semantico": texto_semantico,
                                            "data": {"success": True}
                                        }
                                        queue_client.send_message(json.dumps(evento))
                                        logging.info(f"📤 Enviado a cola de indexación")
                                except Exception as e:
                                    logging.warning(f"⚠️ Error enviando a cola: {e}")
                            else:
                                logging.info(f"🚫 [{source_name}] Descartado: sin valor semántico suficiente")

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
