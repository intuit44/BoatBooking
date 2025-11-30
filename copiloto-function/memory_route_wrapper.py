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
import re
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from azure.storage.queue import QueueClient

from services.redis_buffer_service import redis_buffer

try:
    from semantic_intent_classifier import classify_user_intent, preprocess_text
except Exception:  # pragma: no cover
    classify_user_intent = None
    preprocess_text = None

# Importar router de agentes para optimización de modelos
try:
    from router_agent import route_by_semantic_intent, get_agent_for_message
except Exception:  # pragma: no cover
    route_by_semantic_intent = None
    get_agent_for_message = None

try:
    from skills.log_query_skill import (
        LogQuerySkill,
        extract_function_hint,
        analyze_logs_semantic,
        get_cached_analysis,
        cache_log_analysis,
    )
except Exception:  # pragma: no cover
    LogQuerySkill = None
    extract_function_hint = None
    analyze_logs_semantic = None
    get_cached_analysis = None
    cache_log_analysis = None

# Constantes globales de control de tamaño
MAX_MENSAJE_CHARS = 600
MAX_MENSAJES_THREAD = 20
MAX_RESUMEN_CHARS = 6000

THREADS_CONTAINER_NAME = os.getenv(
    "THREADS_CONTAINER_NAME", "boat-rental-project")
THREADS_BLOB_PREFIX = "threads/"
CUSTOM_EVENT_LOGGER = logging.getLogger("appinsights.customEvents")


def _emit_cache_custom_event(event_name: str, dimensions: Dict[str, Any]) -> None:
    """Envía métricas al canal customEvent de Application Insights."""
    if not dimensions:
        return
    try:
        payload = dict(dimensions)
        payload.setdefault("event_name", event_name)
        CUSTOM_EVENT_LOGGER.info(
            event_name,
            extra={"custom_dimensions": payload}
        )
    except Exception:
        logging.debug("No se pudo emitir customEvent de cache.", exc_info=True)


def _clean_thread_text(texto):
    """Normaliza texto eliminando emojis para almacenamiento de threads."""
    if not isinstance(texto, str):
        return ""
    texto = texto.strip()
    if not texto:
        return ""
    try:
        return re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto).strip()
    except re.error:
        return texto


def _resolver_intencion_logs(user_message: Optional[str], route_path: str = "") -> Optional[Dict[str, Any]]:
    """
    Maneja la intencion revisar_logs sin exponer endpoint dedicado.
    Retorna payload listo para HttpResponse o None si no aplica.
    """
    if not user_message or not classify_user_intent:
        return None

    intent = classify_user_intent(user_message)
    if intent.get("intent") != "revisar_logs":
        return None

    funcion = extract_function_hint(
        user_message) if extract_function_hint else None

    if get_cached_analysis:
        cached = get_cached_analysis(user_message, funcion)
        if cached:
            cached = dict(cached)
            cached["cached"] = True
            return {
                "exito": True,
                "respuesta_usuario": cached.get("mensaje") or "Analisis de logs recuperado de cache",
                "analisis": cached,
                "endpoint": "log_query_skill",
                "source": "cache",
            }

    if not LogQuerySkill:
        return {
            "exito": False,
            "error": "LogQuerySkill no disponible (dependencias faltantes)",
            "endpoint": "log_query_skill",
        }

    try:
        skill = LogQuerySkill()
        logs = skill.query_logs(funcion)
        analisis = analyze_logs_semantic(logs, funcion) if analyze_logs_semantic else {
            "exito": False, "error": "Analizador no disponible"}

        if analisis.get("exito") and cache_log_analysis:
            try:
                cache_log_analysis(user_message, funcion, analisis)
            except Exception:
                logging.debug(
                    "[logs-intent] No se pudo cachear analisis.", exc_info=True)

        respuesta = analisis.get("mensaje") or "Analisis de logs completado"
        return {
            "exito": analisis.get("exito", False),
            "respuesta_usuario": respuesta,
            "analisis": analisis,
            "endpoint": "log_query_skill",
            "source": "log_intent",
        }
    except Exception as exc:  # pragma: no cover
        logging.warning(f"[logs-intent] Error ejecutando LogQuerySkill: {exc}")
        return {
            "exito": False,
            "error": str(exc),
            "endpoint": "log_query_skill",
            "source": "log_intent",
        }


def _resolver_identificadores_thread(req: func.HttpRequest):
    """Obtiene thread_id, session_id y agent_id normalizados."""
    thread_id = req.headers.get("Thread-ID") or req.headers.get("X-Thread-ID")
    if not thread_id:
        try:
            thread_id = req.params.get("thread_id")
        except Exception:
            thread_id = None
    if not thread_id:
        try:
            body = req.get_json()
            if isinstance(body, dict):
                thread_id = body.get("thread_id") or (
                    (body.get("contexto") or {}).get("thread_id")
                    if isinstance(body.get("contexto"), dict) else None
                ) or (
                    (body.get("contexto_conversacion") or {}).get("thread_id")
                    if isinstance(body.get("contexto_conversacion"), dict) else None
                )
        except Exception:
            thread_id = None

    raw_thread_id = thread_id
    session_id = getattr(req, "_session_id", None)
    agent_id = getattr(req, "_agent_id", None)

    if not session_id or not agent_id:
        try:
            from memory_helpers import extraer_session_info

            info = extraer_session_info(req)
            session_id = session_id or info.get("session_id")
            agent_id = agent_id or info.get("agent_id")
        except Exception:
            session_id = session_id or None
            agent_id = agent_id or None

    if not session_id:
        if raw_thread_id:
            session_id = raw_thread_id
        elif agent_id:
            session_id = f"agent-{agent_id}"

    session_id = session_id or "fallback_session"

    if not thread_id and session_id and session_id.startswith("assistant-"):
        thread_id = session_id

    if not thread_id:
        thread_id = raw_thread_id or f"thread_fallback_session_{int(time.time())}"

    return thread_id, session_id, agent_id or "foundry_user"


def _hydrate_request_identificadores(req: func.HttpRequest):
    """Resuelve y adjunta session_id/agent_id al request para reutilización."""
    thread_id, session_id, agent_id = _resolver_identificadores_thread(req)
    try:
        setattr(req, "_session_id", session_id)
        setattr(req, "_agent_id", agent_id)
    except Exception:
        pass
    return thread_id, session_id, agent_id


def _append_message(messages, role, content):
    """Agrega mensaje evitando duplicados consecutivos y truncando a MAX_MENSAJE_CHARS."""
    if not content:
        return
    content_truncado = content[:MAX_MENSAJE_CHARS] if len(
        content) > MAX_MENSAJE_CHARS else content
    payload = {
        "role": role,
        "content": content_truncado,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    if messages and messages[-1].get("role") == role and messages[-1].get("content") == content_truncado:
        return
    messages.append(payload)


def _extraer_respuesta_desde_response(response_data: dict) -> str:
    """Intenta extraer texto de respuesta desde el payload del endpoint."""
    if not isinstance(response_data, dict):
        return ""
    for key in ("respuesta_usuario", "respuesta", "resultado", "mensaje", "texto_semantico", "output"):
        valor = response_data.get(key)
        if isinstance(valor, str) and valor.strip():
            return _clean_thread_text(valor)
    interacciones = response_data.get(
        "interacciones") if isinstance(response_data, dict) else None
    if isinstance(interacciones, list):
        for item in interacciones:
            texto = (item or {}).get("texto_semantico")
            if isinstance(texto, str) and texto.strip():
                return _clean_thread_text(texto)
    return ""


def guardar_thread_en_blob(req: func.HttpRequest, route_path: str, response_data: dict, respuesta_agente: str = ""):
    """
    Persiste el thread completo (mensajes + metadata) en Blob Storage para historiales reales.
    """
    try:
        from blob_service import get_blob_client
    except Exception:
        logging.debug(
            "Blob client no disponible; se omite guardado de thread.")
        return

    thread_id, session_id, agent_id = _resolver_identificadores_thread(req)
    user_message = _clean_thread_text(
        getattr(req, "_ultimo_mensaje_usuario", ""))
    assistant_message = _clean_thread_text(
        respuesta_agente) or _extraer_respuesta_desde_response(response_data or {})

    if not user_message and not assistant_message and not isinstance(response_data, dict):
        return

    try:
        client = get_blob_client()
        container = client.get_container_client(THREADS_CONTAINER_NAME)
        blob_name = f"{THREADS_BLOB_PREFIX}{thread_id}.json"
        blob_client = container.get_blob_client(blob_name)

        existing_data = None
        try:
            existing_bytes = blob_client.download_blob().readall()
            existing_data = json.loads(existing_bytes.decode("utf-8"))
        except Exception:
            existing_data = None

        mensajes_existentes = []
        if isinstance(existing_data, dict):
            mensajes_existentes = existing_data.get("mensajes") or []
            if not isinstance(mensajes_existentes, list):
                mensajes_existentes = []

        mensajes_totales = list(mensajes_existentes)
        _append_message(mensajes_totales, "usuario", user_message)
        _append_message(mensajes_totales, "asistente", assistant_message)

        if not mensajes_totales:
            return

        timestamp = datetime.utcnow().isoformat() + "Z"
        thread_payload = existing_data if isinstance(
            existing_data, dict) else {}
        thread_payload.update({
            "id": thread_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "endpoint": route_path,
            "timestamp": timestamp,
        })

        # Limitar mensajes a MAX_MENSAJES_THREAD
        thread_payload["mensajes"] = mensajes_totales[-MAX_MENSAJES_THREAD:]

        # Limpiar response_data antes de guardar (eliminar campos inútiles)
        if isinstance(response_data, dict):
            response_clean = {}
            for k, v in response_data.items():
                if k in ("texto_semantico", "respuesta_usuario", "metadata", "interacciones"):
                    continue
                if v and not (isinstance(v, str) and not v.strip()):
                    response_clean[k] = v
            if response_clean:
                thread_payload["response_data"] = response_clean

        metadata = thread_payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata.update({
            "user_agent": req.headers.get("User-Agent", ""),
            "source": req.headers.get("X-Source") or req.headers.get("Source") or metadata.get("source") or "foundry_ui",
            "ultima_actualizacion": timestamp,
            "wrapper_aplicado": True
        })
        thread_payload["metadata"] = metadata

        body_bytes = json.dumps(thread_payload, ensure_ascii=False,
                                indent=2).encode("utf-8")
        blob_client.upload_blob(body_bytes, overwrite=True)
        logging.info(
            f"[THREAD_STORE] Thread {thread_id} actualizado ({len(thread_payload['mensajes'])} mensajes).")
        try:
            redis_buffer.cache_thread_snapshot(thread_id, thread_payload)
        except Exception:
            logging.debug(
                f"[THREAD_STORE] No se pudo cachear thread {thread_id} en Redis.", exc_info=True)
    except Exception as exc:
        logging.warning(f"Error guardando thread en blob: {exc}")


def recuperar_contexto_conversacional(session_id: str, endpoint_actual: str) -> str:
    """
    Recupera el contexto conversacional desde la última invocación de endpoint.
    Retorna el bloque de conversación entre la última acción y esta.
    """
    try:
        from services.memory_service import memory_service

        # Obtener historial de la sesión
        interacciones = memory_service.get_session_history(
            session_id, limit=50)

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
            # Orden cronológico
            return " | ".join(reversed(contexto_acumulado))

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
                source_name = route_path.strip(
                    "/").replace("-", "_") or func_ref.__name__

                def wrapper(req: func.HttpRequest) -> func.HttpResponse:
                    """Lectura y escritura de memoria automática."""
                    print(
                        f"\n>>> WRAPPER EJECUTANDOSE para: {source_name} <<<\n", flush=True)
                    logging.warning(
                        f"🚨 Wrapper ACTIVADO en endpoint: {source_name}")
                    from services.memory_service import memory_service

                    # 0️⃣ CAPTURA COMPLETA DE ENTRADA DEL USUARIO
                    try:
                        body = req.get_json() if req.method in [
                            "POST", "PUT", "PATCH"] else {}
                        # Priorizar 'input' (Foundry real) sobre 'mensaje' (legacy)
                        user_message_raw = body.get("input") or body.get("mensaje") or body.get(
                            "query") or body.get("prompt")
                        user_message = user_message_raw.strip(
                        ) if isinstance(user_message_raw, str) else None

                        # 🤖 ROUTING SEMÁNTICO - Determinar agente y modelo óptimo
                        routing_result = None
                        if user_message and route_by_semantic_intent:
                            try:
                                _, session_id, _ = _hydrate_request_identificadores(
                                    req)
                                routing_result = route_by_semantic_intent(
                                    user_message, session_id=session_id
                                )

                                # Agregar información de routing al request para uso posterior
                                setattr(req, "_routing_result", routing_result)
                                setattr(req, "_selected_model",
                                        routing_result.get("model"))
                                setattr(req, "_selected_agent",
                                        routing_result.get("agent_id"))

                                logging.info(
                                    f"🤖 [Router] '{user_message[:50]}...' → Agent: {routing_result.get('agent_id')} → Model: {routing_result.get('model')}")
                            except Exception as e:
                                logging.warning(
                                    f"⚠️ Error en routing semántico: {e}")
                                routing_result = None

                        if user_message:
                            try:
                                setattr(
                                    req, "_ultimo_mensaje_usuario", user_message)
                            except Exception:
                                pass

                        # 🔄 INYECCIÓN AUTOMÁTICA DE CONTINUIDAD CONVERSACIONAL
                        conversational_context = None
                        if user_message and len(user_message) > 5:
                            try:
                                from conversational_continuity_middleware import inject_conversational_context, build_context_enriched_prompt

                                _, session_id, agent_id = _hydrate_request_identificadores(
                                    req)
                                agente_asignado = routing_result.get(
                                    "agent_id") if routing_result else agent_id

                                # Inyectar contexto conversacional automáticamente
                                conversational_context = inject_conversational_context(
                                    user_message=user_message,
                                    session_id=session_id,
                                    agent_id=agente_asignado
                                )

                                # Si hay contexto significativo, enriquecer el prompt del usuario
                                if conversational_context.get("has_context", False):
                                    enriched_prompt = build_context_enriched_prompt(
                                        original_prompt=user_message,
                                        user_message=user_message,
                                        session_id=session_id,
                                        agent_id=agente_asignado
                                    )

                                    # IMPORTANTE: Reemplazar el input/mensaje del usuario con el prompt enriquecido
                                    if "input" in body:
                                        body["input"] = enriched_prompt
                                    elif "mensaje" in body:
                                        body["mensaje"] = enriched_prompt
                                    elif "query" in body:
                                        body["query"] = enriched_prompt
                                    elif "prompt" in body:
                                        body["prompt"] = enriched_prompt

                                    # Actualizar el request con el body modificado
                                    setattr(req, "_json_body", body)
                                    setattr(
                                        req, "_conversational_context_injected", True)
                                    setattr(req, "_original_message",
                                            user_message)
                                    setattr(req, "_enriched_message",
                                            enriched_prompt)

                                    # Override del método get_json para devolver el body enriquecido
                                    original_get_json = req.get_json

                                    def get_enriched_json():
                                        return body

                                    req.get_json = get_enriched_json

                                    logging.info(
                                        f"🔄 [ConversationalContinuity] Contexto inyectado automáticamente para sesión {session_id[:8]}...")
                                else:
                                    logging.debug(
                                        f"🔄 [ConversationalContinuity] Sin contexto suficiente para sesión {session_id[:8]}...")

                            except Exception as e:
                                logging.warning(
                                    f"⚠️ Error en inyección de continuidad conversacional: {e}")
                                conversational_context = None

                        # Resolver intencion revisar_logs sin depender de /api/logs
                        if user_message and len(user_message) > 3:
                            intent_logs = _resolver_intencion_logs(
                                user_message, route_path)
                            if intent_logs:
                                return func.HttpResponse(
                                    json.dumps(
                                        intent_logs, ensure_ascii=False),
                                    mimetype="application/json",
                                    status_code=200 if intent_logs.get(
                                        "exito") else 500
                                )

                        if user_message and len(user_message) > 3:
                            # CAPTURA AUTOMÁTICA DE THREAD
                            _, session_id, agent_id = _hydrate_request_identificadores(
                                req)

                            # Crear evento completo con información de routing
                            routing_metadata = routing_result.get(
                                "routing_metadata", {}) if routing_result else {}
                            modelo_asignado = routing_result.get(
                                "model") if routing_result else None
                            agente_asignado = routing_result.get(
                                "agent_id") if routing_result else agent_id

                            evento = {
                                "id": f"{session_id}_user_input_{int(datetime.utcnow().timestamp())}",
                                "session_id": session_id,
                                "agent_id": agente_asignado,
                                "endpoint": route_path or "input-ui",
                                "event_type": "user_input",
                                "texto_semantico": user_message.strip(),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "exito": True,
                                "tipo": "user_input",
                                "model_usado": modelo_asignado,  # 🎯 MODELO ASIGNADO
                                "routing_metadata": routing_metadata,  # 🎯 METADATA DE ROUTING
                                "data": {
                                    "origen": "foundry_ui",
                                    "tipo": "user_input",
                                    "intent": routing_metadata.get("intent"),
                                    "confidence": routing_metadata.get("confidence"),
                                    "model": modelo_asignado
                                }
                            }

                            # Guardar en Cosmos + AI Search (flujo completo automático)
                            ok_cosmos = memory_service._log_cosmos(evento)
                            if ok_cosmos:
                                logging.info(
                                    f"✅ Guardado e indexado: {evento['id']} ({len(user_message)} chars)")
                            else:
                                logging.warning(
                                    "⚠️ No se pudo guardar el input del usuario.")
                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando input del usuario: {e}")

                    # 1️⃣ CONSULTAR MEMORIA COMPLETA: Cosmos DB + Conversación Rica
                    memoria_previa = {}
                    try:
                        from cosmos_memory_direct import consultar_memoria_cosmos_directo

                        # CAPTURA AUTOMÁTICA DE THREAD
                        thread_id_cache, session_id, agent_id = _hydrate_request_identificadores(
                            req)

                        cache_dimensions = {
                            "cache_scope": "memoria_contexto",
                            "route": source_name,
                            "session_id": session_id,
                            "thread_id": thread_id_cache or "",
                            "redis_enabled": redis_buffer.is_enabled
                        }
                        memoria_previa = None
                        redis_lookup_ms = 0.0
                        if redis_buffer.is_enabled:
                            start_lookup = time.perf_counter()
                            memoria_previa = redis_buffer.get_memoria_cache(
                                session_id)
                            redis_lookup_ms = (
                                time.perf_counter() - start_lookup) * 1000

                        if memoria_previa:
                            cache_dimensions.update({
                                "hit": True,
                                "latency_ms": round(redis_lookup_ms, 2),
                                "source": "redis"
                            })
                            _emit_cache_custom_event(
                                "redis_buffer_lookup", cache_dimensions)
                        else:
                            cosmos_lookup = time.perf_counter()
                            memoria_previa = consultar_memoria_cosmos_directo(
                                req)
                            cosmos_latency_ms = (
                                time.perf_counter() - cosmos_lookup) * 1000
                            redis_buffer.cache_memoria_contexto(
                                session_id, memoria_previa, thread_id=thread_id_cache)
                            cache_dimensions.update({
                                "hit": False,
                                "latency_ms": round(cosmos_latency_ms, 2),
                                "source": "cosmos"
                            })
                            _emit_cache_custom_event(
                                "redis_buffer_lookup", cache_dimensions)

                        if memoria_previa and memoria_previa.get("tiene_historial"):
                            total = memoria_previa.get(
                                "total_interacciones", 0)
                            logging.info(
                                f"🧠 [{source_name}] Memoria COMPLETA: {total} interacciones, sesión={session_id}, agente={agent_id}")
                            logging.info(
                                f"📝 Resumen: {memoria_previa.get('resumen_conversacion', '')[:200]}...")
                        else:
                            memoria_previa = {
                                "tiene_historial": False, "endpoint": route_path, "session_id": session_id}
                            logging.info(
                                f"🧠 [{source_name}] Sin memoria previa para sesión {session_id}")

                        setattr(req, "_memoria_contexto", memoria_previa)
                    except Exception as e:
                        logging.warning(
                            f"⚠️ [{source_name}] Error consultando memoria completa: {e}")
                        import traceback
                        logging.warning(traceback.format_exc())
                        # Fallback: intentar con memory_service local
                        try:
                            session_id = req.headers.get(
                                "Session-ID") or "global"
                            historial = memory_service.get_session_history(
                                session_id, limit=100)
                            memoria_previa = {
                                "tiene_historial": len(historial) > 0,
                                "interacciones_recientes": historial,
                                "total_interacciones": len(historial),
                                "session_id": session_id
                            }
                            setattr(req, "_memoria_contexto", memoria_previa)
                            logging.info(
                                f"🧠 [{source_name}] Fallback local: {len(historial)} interacciones")
                        except:
                            setattr(req, "_memoria_contexto", {
                                    "tiene_historial": False})

                    # 1.5️⃣ BÚSQUEDA VECTORIAL EN AI SEARCH POR ENDPOINT
                    docs_vectoriales = []
                    try:
                        from endpoints_search_memory import buscar_memoria_endpoint

                        # Buscar por endpoint + contenido del request
                        query_busqueda = f"{route_path}"
                        try:
                            body = req.get_json() or {}
                            if body.get("mensaje"):
                                query_busqueda += f" {body['mensaje']}"
                            elif body.get("query"):
                                query_busqueda += f" {body['query']}"
                        except:
                            pass

                        memoria_payload = {
                            "query": query_busqueda,
                            "top": 20  # Más resultados
                        }

                        search_material = f"{route_path}|{getattr(req, '_session_id', '')}|{query_busqueda}"
                        search_hash = redis_buffer.stable_hash(search_material)
                        search_metrics = {
                            "cache_scope": "search_vectorial",
                            "route": route_path,
                            "session_id": getattr(req, "_session_id", ""),
                            "query_hash": search_hash,
                            "redis_enabled": redis_buffer.is_enabled
                        }
                        cached_docs = None
                        search_latency_ms = 0.0
                        if redis_buffer.is_enabled:
                            start_lookup = time.perf_counter()
                            cached_docs = redis_buffer.get_cached_payload(
                                "search", search_hash)
                            search_latency_ms = (
                                time.perf_counter() - start_lookup) * 1000

                        if cached_docs:
                            docs_vectoriales = cached_docs
                            search_metrics.update({
                                "hit": True,
                                "latency_ms": round(search_latency_ms, 2),
                                "source": "redis",
                                "docs": len(docs_vectoriales)
                            })
                            _emit_cache_custom_event(
                                "redis_buffer_search", search_metrics)
                        else:
                            resultado_lookup = time.perf_counter()
                            resultado_vectorial = buscar_memoria_endpoint(
                                memoria_payload)
                            consulta_latency = (
                                time.perf_counter() - resultado_lookup) * 1000
                            if resultado_vectorial.get("exito") and resultado_vectorial.get("documentos"):
                                docs_vectoriales = resultado_vectorial["documentos"]
                                redis_buffer.cache_response(
                                    "search", search_hash, docs_vectoriales)
                                logging.info(
                                    f"🔍 [{source_name}] AI Search: {len(docs_vectoriales)} docs vectoriales para endpoint {route_path}")

                                # Inyectar en memoria_previa
                                if memoria_previa:
                                    memoria_previa["docs_vectoriales"] = docs_vectoriales
                                    memoria_previa["fuente_datos"] = "Endpoint+AISearch"

                            search_metrics.update({
                                "hit": False,
                                "latency_ms": round(consulta_latency, 2),
                                "source": "search_service",
                                "docs": len(docs_vectoriales)
                            })
                            _emit_cache_custom_event(
                                "redis_buffer_search", search_metrics)
                    except Exception as e:
                        logging.warning(
                            f"⚠️ [{source_name}] Error en búsqueda vectorial: {e}")

                    # 2️⃣ EJECUTAR ENDPOINT ORIGINAL
                    try:
                        response = func_ref(req)
                        if response is None:
                            logging.error(
                                f"❌ [{source_name}] Endpoint devolvió None - esto no debería ocurrir")
                            return func.HttpResponse(
                                json.dumps(
                                    {"ok": False, "error": "Endpoint devolvió None"}, ensure_ascii=False),
                                mimetype="application/json",
                                status_code=500
                            )
                    except Exception as endpoint_error:
                        logging.error(
                            f"❌ [{source_name}] Excepción en endpoint: {endpoint_error}")
                        import traceback
                        logging.error(f"Traceback: {traceback.format_exc()}")
                        return func.HttpResponse(
                            json.dumps({
                                "ok": False,
                                "error": f"Error en endpoint: {str(endpoint_error)}",
                                "tipo_error": type(endpoint_error).__name__
                            }, ensure_ascii=False),
                            mimetype="application/json",
                            status_code=500
                        )

                    # Guardar contexto caliente después de la ejecución
                    try:
                        session_cache = getattr(req, "_session_id", None)
                        thread_cache, _, _ = _resolver_identificadores_thread(
                            req)
                        memoria_contexto = getattr(
                            req, "_memoria_contexto", None)
                        if session_cache and memoria_contexto:
                            redis_buffer.cache_memoria_contexto(
                                session_cache, memoria_contexto, thread_id=thread_cache)
                    except Exception:
                        logging.debug(
                            "No se pudo refrescar la caché de memoria post-ejecución.", exc_info=True)

                    # 3️⃣ INYECTAR METADATA SIN PERDER CONTENIDO
                    response_data_for_semantic = None
                    try:
                        if isinstance(response, func.HttpResponse) and response.get_body():
                            body = response.get_body()
                            response_data = json.loads(body.decode("utf-8"))
                            response_data_for_semantic = response_data.copy(
                            ) if isinstance(response_data, dict) else None
                            logging.info(
                                f"[BLOQUE 3] Capturado response_data_for_semantic: {bool(response_data_for_semantic)}")

                            if isinstance(response_data, dict):
                                # Inyectar metadata SIN tocar campos principales
                                if "metadata" not in response_data:
                                    response_data["metadata"] = {}

                                response_data["metadata"]["wrapper_aplicado"] = True

                                # Proteger accesos en caso de que memoria_previa sea None
                                mp = memoria_previa or {}
                                if mp.get("tiene_historial"):
                                    response_data["metadata"]["memoria_aplicada"] = True
                                    response_data["metadata"]["interacciones_previas"] = mp.get(
                                        "total_interacciones", 0)
                                    response_data["metadata"]["docs_vectoriales"] = len(
                                        mp.get("docs_vectoriales", []))
                                    logging.info(
                                        f"🧠 [{source_name}] Metadata inyectada: {mp.get('total_interacciones', 0)} interacciones")

                                # Recrear HttpResponse preservando TODO
                                new_body = json.dumps(
                                    response_data, ensure_ascii=False)
                                response = func.HttpResponse(
                                    new_body,
                                    status_code=response.status_code,
                                    mimetype="application/json; charset=utf-8"
                                )
                                logging.info(
                                    f"📊 [{source_name}] Response recreado: {len(new_body)} bytes, respuesta_usuario={'respuesta_usuario' in response_data}")
                    except Exception as e:
                        logging.error(
                            f"❌ [{source_name}] Error inyectando metadata: {e}")
                        import traceback
                        logging.error(traceback.format_exc())

                    # 4️⃣ CAPTURA AUTOMÁTICA DE CONVERSACIÓN RICA COMPLETA (solo si hay contexto real)
                    try:
                        # CAPTURA AUTOMÁTICA DE THREAD
                        _, session_id, _ = _hydrate_request_identificadores(
                            req)

                        resumen_completo = (memoria_previa.get(
                            "resumen_conversacion", "") if memoria_previa else "")
                        total_interacciones = (memoria_previa.get(
                            "total_interacciones", 0) if memoria_previa else 0)
                        ultimo_tema = (memoria_previa.get(
                            "ultimo_tema", "") if memoria_previa else "")

                        # Determinar si la ejecución fue "activa" (backend/agent real)
                        ejecucion_activa = False
                        try:
                            if isinstance(response, func.HttpResponse):
                                # Considerar ejecución activa si la respuesta es 2xx/3xx y contiene cuerpo útil
                                status_ok = 200 <= (
                                    getattr(response, "status_code", 500) or 500) < 400
                                body_bytes = response.get_body() or b""
                                body_text = body_bytes.decode(
                                    "utf-8", errors="ignore") if body_bytes else ""
                                parsed = {}
                                try:
                                    parsed = json.loads(
                                        body_text) if body_text else {}
                                except:
                                    parsed = {}

                                tiene_valor_semantico = False
                                if isinstance(parsed, dict):
                                    for key in ("respuesta_usuario", "respuesta", "texto_semantico", "resultado", "output", "mensaje"):
                                        val = parsed.get(key)
                                        if isinstance(val, str) and len(val.strip()) > 20:
                                            tiene_valor_semantico = True
                                            break
                                    # también considerar casos con éxito explícito y mensaje corto pero significativo
                                    if not tiene_valor_semantico and (parsed.get("exito") or parsed.get("success")) and parsed.get("mensaje"):
                                        tiene_valor_semantico = len(
                                            str(parsed.get("mensaje")).strip()) > 20

                                ejecucion_activa = status_ok and (
                                    body_text.strip() != "") and tiene_valor_semantico
                        except Exception:
                            ejecucion_activa = False

                        # Excluir procesos automáticos / triviales
                        source_lower = source_name.lower() if source_name else ""
                        es_proceso_automatico = any(term in source_lower for term in (
                            "timer", "cron", "supervisor", "foundry", "scheduler"))

                        # Condiciones para crear snapshot:
                        # - existe resumen con contenido real y suficiente longitud
                        # - hay al menos 2 interacciones previas (no snapshots por primera interacción)
                        # - la ejecución actual parece ser activa (backend/agente con output semántico)
                        # - no es un proceso/cron automático
                        if (
                            resumen_completo
                            and len(resumen_completo.strip()) > 100
                            and total_interacciones >= 2
                            and ejecucion_activa
                            and not es_proceso_automatico
                        ):
                            try:
                                memory_service.registrar_llamada(
                                    source="conversation_snapshot",
                                    endpoint=route_path,
                                    method="AUTO",
                                    params={
                                        "session_id": session_id,
                                        "trigger": route_path,
                                        "agent_id": req.headers.get("Agent-ID", "unknown"),
                                        # Indicar que este snapshot es global/semántico (no ligado exclusivamente a session_id)
                                        "snapshot_scope": "global_semantic"
                                    },
                                    response_data={
                                        "texto_semantico": f"Conversacion consolidada: {resumen_completo[:1500]}",
                                        "tipo": "conversation_snapshot",
                                        "ultimo_tema": ultimo_tema,
                                        "total_interacciones": total_interacciones,
                                    },
                                    success=True,
                                )
                                logging.info(
                                    f"📸 Snapshot cognitivo creado ({total_interacciones} interacciones, {len(resumen_completo)} chars)")
                            except Exception as e:
                                logging.warning(
                                    f"⚠️ Error guardando snapshot cognitivo: {e}")
                        else:
                            logging.info(
                                "⏭️ Snapshot omitido (sin contenido semántico, insuficiente historial o ejecución no relevante)")

                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando snapshot cognitivo: {e}")

                    # ------------------------------------------------------------------
                    # BLOQUE 5 eliminado intencionalmente para evitar doble registro de
                    # embeddings. Solo se conserva el Bloque 6 que utiliza
                    # response_data_for_semantic con metadatos completos.
                    # ------------------------------------------------------------------

                    # 5.5️⃣ SINCRONIZAR THREAD DE FOUNDRY CON MEMORIA
                    try:
                        from thread_memory_hook import sync_thread_to_memory
                        response_data = sync_thread_to_memory(
                            req, response_data_for_semantic or {})
                    except Exception as e:
                        logging.warning(f"⚠️ Error sincronizando thread: {e}")

                    # 6️⃣ CAPTURA DE RESPUESTA COMPLETA FOUNDRY UI
                    assistant_thread_text = None
                    try:
                        # CAPTURA AUTOMÁTICA DE THREAD
                        _, session_id, agent_id = _hydrate_request_identificadores(
                            req)

                        logging.info(f"[BLOQUE 6] Iniciando para {route_path}")

                        logging.info(
                            f"[BLOQUE 6] response_data_for_semantic disponible: {bool(response_data_for_semantic)}")
                        if response_data_for_semantic and isinstance(response_data_for_semantic, dict):
                            logging.info(
                                f"[BLOQUE 6] Usando response_data capturado, keys: {list(response_data_for_semantic.keys())[:5]}")
                            try:
                                from registrar_respuesta_semantica import registrar_respuesta_semantica

                                respuesta_texto = (
                                    response_data_for_semantic.get("respuesta_usuario") or
                                    response_data_for_semantic.get("respuesta") or
                                    response_data_for_semantic.get("resultado") or
                                    response_data_for_semantic.get("mensaje")
                                )

                                logging.info(
                                    f"[BLOQUE 6] respuesta_texto encontrado: {bool(respuesta_texto)}, len={len(str(respuesta_texto)) if respuesta_texto else 0}")
                                if respuesta_texto and isinstance(respuesta_texto, str):
                                    texto_limpio = _clean_thread_text(
                                        respuesta_texto)
                                    texto_limpio = texto_limpio.replace(
                                        "endpoint", "consulta").replace("**", "")
                                    logging.info(
                                        f"[BLOQUE 6] texto_limpio len={len(texto_limpio.strip())}")

                                    if texto_limpio.strip():
                                        assistant_thread_text = texto_limpio.strip()

                                    if len(texto_limpio.strip()) > 20:
                                        logging.info(
                                            f"[BLOQUE 6] Llamando registrar_respuesta_semantica...")

                                        # 🤖 Obtener información de routing si está disponible
                                        routing_result = getattr(
                                            req, '_routing_result', None)
                                        modelo_usado = getattr(
                                            req, '_selected_model', None)
                                        agente_usado = getattr(
                                            req, '_selected_agent', None) or agent_id

                                        # Registrar con información de modelo para auditoría
                                        registrar_respuesta_semantica(
                                            texto_limpio, session_id, agente_usado, route_path,
                                            model_usado=modelo_usado,
                                            routing_metadata=routing_result.get(
                                                'routing_metadata', {}) if routing_result else {}
                                        )

                                        logging.info(
                                            f"[Foundry] Respuesta capturada: {len(texto_limpio)} chars, Model: {modelo_usado}, Agent: {agente_usado}")

                                elif response_data_for_semantic.get("interacciones"):
                                    interacciones = response_data_for_semantic.get(
                                        "interacciones", [])
                                    resumen_partes = []
                                    for i in interacciones[:5]:
                                        texto = i.get("texto_semantico", "")
                                        texto_limpio = _clean_thread_text(
                                            texto)
                                        texto_limpio = texto_limpio.replace(
                                            "endpoint", "consulta").replace("**", "")
                                        if len(texto_limpio.strip()) > 20:
                                            resumen_partes.append(
                                                texto_limpio.strip()[:200])
                                    if resumen_partes:
                                        texto_sintetizado = " | ".join(
                                            resumen_partes)
                                        assistant_thread_text = texto_sintetizado.strip()
                                        registrar_respuesta_semantica(
                                            texto_sintetizado, session_id, agent_id, route_path)
                                        logging.info(
                                            f"[Foundry] Sintetizado: {len(texto_sintetizado)} chars")
                            except Exception as e:
                                logging.error(f"[BLOQUE 6] Error: {e}")
                                import traceback
                                logging.error(traceback.format_exc())
                        else:
                            logging.info(
                                "⏭️ No se pudo leer cuerpo de respuesta Foundry UI (no es HttpResponse).")
                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error capturando respuesta Foundry UI: {e}")

                    try:
                        guardar_thread_en_blob(
                            req,
                            route_path,
                            response_data_for_semantic or {},
                            assistant_thread_text or ""
                        )
                    except Exception as e:
                        logging.warning(
                            f"⚠️ Error guardando snapshot de thread: {e}")

                    return response

                if "historial" not in route_path.lower():
                    logging.info(
                        f"✅ Memoria automática aplicada a endpoint: {route_path}")
                else:
                    logging.info(
                        f"⏭️ Endpoint de historial: wrapper aplicado SIN registro")
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
