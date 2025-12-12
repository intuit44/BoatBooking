"""
Endpoint: redis-model-wrapper
Propósito: actuar como proxy cacheado (Redis) delante del modelo Azure OpenAI.

Flujo:
- Lee mensaje/prompt y session_id/agent_id (headers o body).
- Busca en Redis (bucket llm) usando hash de session+mensaje.
- HIT: responde desde cache.
- MISS: invoca modelo, guarda en Redis y responde.
"""
import json
import logging
import os
import time
import azure.functions as func
from openai import AzureOpenAI
from function_app import app
from services.redis_buffer_service import redis_buffer
from azure.storage.queue import QueueClient

# Cliente OpenAI (lazy loading para evitar errores en import time)


def _get_openai_client():
    """Lazy loading del cliente OpenAI para evitar errores durante import"""
    azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

    if not azure_openai_key or not azure_openai_endpoint:
        raise ValueError(
            "AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT environment variables must be set")

    return AzureOpenAI(
        api_key=azure_openai_key,
        api_version="2024-02-01",
        azure_endpoint=azure_openai_endpoint,
    )


DEFAULT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv(
    "OPENAI_CHAT_MODEL") or "gpt-4o-mini"


def _extraer_texto(body):
    for key in ("mensaje", "prompt", "query", "texto"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


@app.function_name(name="redis_model_wrapper_http")
@app.route(route="redis-model-wrapper", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def redis_model_wrapper_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            body = req.get_json() or {}
        except Exception:
            body = {}

        raw_session = (
            req.headers.get("Session-ID")
            or req.headers.get("X-Session-ID")
            or body.get("session_id")
        )
        agent_id = (
            req.headers.get("Agent-ID")
            or req.headers.get("X-Agent-ID")
            or body.get("agent_id")
            or "foundry_user"
        )
        mensaje = _extraer_texto(body)
        model = body.get("model") or DEFAULT_MODEL

        # Si no viene session_id, generamos una sesión estable derivada del prompt + agente
        # para evitar caer siempre en "agent-default".
        if raw_session and str(raw_session).strip():
            session_id = str(raw_session).strip()
        else:
            session_hash = redis_buffer.stable_hash(f"{agent_id}|{mensaje}")
            session_id = f"auto-{session_hash}"
            logging.info(
                f"[RedisWrapper] Auto-generated session_id: {session_id} (hash: {session_hash[:8]})"
            )

        if not mensaje:
            return func.HttpResponse(
                json.dumps(
                    {"ok": False, "error": "Falta 'mensaje'/'prompt' en el body"}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        # ⭐ NUEVO: Logging detallado al inicio
        logging.info(
            f"[RedisWrapper] 📥 Request: agent={agent_id}, session={session_id}, msg_len={len(mensaje)}")

        bucket = "llm"

        start = time.perf_counter()
        cache_hit = False
        origen = "model"
        ttl_restante = None
        respuesta_texto = None
        cache_source = "miss"

        # ⭐ NUEVO: Logging de cache hits/misses detallado
        if redis_buffer.is_enabled:
            cached, cache_source = redis_buffer.get_llm_cached_response(
                agent_id=agent_id,
                session_id=session_id,
                message=mensaje,
                model=model,
                use_global_cache=True,
            )
            if cached:
                cache_hit = True
                origen = f"redis_{cache_source}"
                respuesta_texto = cached.get(
                    "respuesta") if isinstance(cached, dict) else cached
                logging.info(
                    f"[RedisWrapper] ✅ Cache HIT from {cache_source}: session_id={session_id}"
                )
            else:
                logging.info(
                    f"[RedisWrapper] ⚠️ CACHE MISS: agent={agent_id}, session={session_id}, model={model}")

        # MISS: invocar modelo
        if not cache_hit:
            try:
                logging.info(f"[RedisWrapper] 🤖 Calling model: {model}")
                openai_client = _get_openai_client()
                completion = openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": mensaje}],
                )
                respuesta_texto = completion.choices[0].message.content

                if redis_buffer.is_enabled:
                    try:
                        redis_buffer.cache_llm_response(
                            agent_id=agent_id,
                            session_id=session_id,
                            message=mensaje,
                            model=model,
                            response_data={
                                "respuesta": respuesta_texto,
                                "session_id": session_id,
                                "agent_id": agent_id,
                                "model": model,
                            },
                            use_global_cache=True,
                        )
                        logging.info(
                            f"[RedisWrapper] 💾 Cache write successful: session={session_id}")
                    except Exception as cache_err:
                        logging.error(
                            f"[RedisWrapper] ❌ Cache write error: {cache_err}")

            except Exception as e:
                logging.error(
                    f"[redis-model-wrapper] Error invocando modelo: {e}")
                return func.HttpResponse(
                    json.dumps(
                        {"ok": False, "error": f"Error llamando al modelo: {e}"}, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=500,
                )

        dur_ms = (time.perf_counter() - start) * 1000
        result = {
            "ok": True,
            "respuesta": respuesta_texto,
            "cache_hit": cache_hit,
            "origen": origen,
            "duration_ms": round(dur_ms, 2),
            "session_id": session_id,
            "agent_id": agent_id,
            "model": model,
            "cache_source": cache_source,
            "is_auto_session": session_id.startswith("auto-"),
            "redis_enabled": redis_buffer.is_enabled,
            "cache_strategy": "dual_session_global"
        }

        # ⭐ NUEVO: Logging de respuesta final
        logging.info(
            f"[RedisWrapper] 📤 Response: cache_hit={cache_hit}, duration={dur_ms:.0f}ms, auto_session={session_id.startswith('auto-')}")

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False), mimetype="application/json", status_code=200
        )
    except Exception as exc:
        logging.error(f"[redis-model-wrapper] Error inesperado: {exc}")
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500,
        )
