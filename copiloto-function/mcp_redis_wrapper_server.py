#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor MCP (FastMCP) que expone una herramienta cacheada vía Redis.
La herramienta llama al endpoint /api/redis-model-wrapper de la Function App,
de modo que el modelo solo se invoca en caso de cache miss.
"""
from services.redis_buffer_service import redis_buffer
from openai import AzureOpenAI
from mcp.server.fastmcp import FastMCP
import httpx
import json
import logging
import os
import time
from typing import Any, Optional, Tuple

# Cargar variables de entorno desde local.settings.json si existe


def load_local_settings():
    """Carga variables de entorno desde local.settings.json para desarrollo local"""
    try:
        local_settings_path = os.path.join(
            os.path.dirname(__file__), "local.settings.json")
        if os.path.exists(local_settings_path):
            with open(local_settings_path, 'r') as f:
                settings = json.load(f)
                values = settings.get('Values', {})
                for key, value in values.items():
                    if key not in os.environ:  # No sobrescribir variables ya definidas
                        os.environ[key] = value
                logging.info(
                    f"[MCP-Setup] ✅ Cargadas {len(values)} variables desde local.settings.json")
        else:
            logging.info(
                "[MCP-Setup] 📝 local.settings.json no encontrado, usando variables de entorno del sistema")
    except Exception as e:
        logging.error(f"[MCP-Setup] ❌ Error cargando local.settings.json: {e}")


# Cargar configuración local al importar el módulo
load_local_settings()


# Configuración HTTP del servidor MCP (por defecto HTTP en 0.0.0.0:8000)
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http").lower()

# Configuración
DEFAULT_ENDPOINT = (
    "https://copiloto-semantico-func-us2.azurewebsites.net/"
    "api/redis-model-wrapper?code=EQKFb6twoyqotvg_kMiBaaefWiOGNoVB4gwGFBOCCFLCAzFurK--Ng=="
)

ENDPOINT_URL = os.getenv("REDIS_MODEL_WRAPPER_URL", DEFAULT_ENDPOINT)

DEFAULT_SESSION = os.getenv("MCP_DEFAULT_SESSION", "mcp-session")
DEFAULT_AGENT = os.getenv("MCP_DEFAULT_AGENT", "mcp-agent")

# Configuración de IDs forzados para cache global
FORCED_SESSION_ID = os.getenv("FORCED_SESSION_ID", "agent-default")
FORCED_AGENT_ID = os.getenv("FORCED_AGENT_ID", "GlobalAgent")

# Configuración OpenAI
DEFAULT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o-mini"


def _get_openai_client():
    """Lazy loading del cliente OpenAI"""
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


# Ajustamos host/port en settings para el transporte HTTP; mantenemos
# streamable_http_path=/mcp para handshake.
mcp = FastMCP("redis-wrapper", host=MCP_HOST,
              port=MCP_PORT, streamable_http_path="/mcp")
logging.basicConfig(level=logging.INFO)


def _process_with_redis_cache(mensaje: str, session_id: str, agent_id: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Procesa mensaje con cache Redis directo - con logging detallado"""
    start = time.perf_counter()
    cache_hit = False
    origen = "model"
    cache_source = "miss"
    respuesta_texto = None

    # Generar hash del mensaje para logging
    msg_hash = redis_buffer.stable_hash(mensaje)
    logging.info(
        f"[MCP-RedisCache] 📥 Request: agent={agent_id}, session={session_id}, msg_hash={msg_hash[:8]}...")
    logging.info(
        f"[MCP-RedisCache] 📝 Message preview: {mensaje[:100]}{'...' if len(mensaje) > 100 else ''}")

    # Intentar obtener desde cache Redis
    if redis_buffer.is_enabled:
        logging.info(f"[MCP-RedisCache] 🔍 Buscando en Redis cache...")

        # Construir claves para logging
        session_key = redis_buffer.build_llm_session_key(
            agent_id, session_id, mensaje, model)
        global_key = redis_buffer.build_llm_global_key(
            agent_id, mensaje, model)

        logging.info(f"[MCP-RedisCache] 🔑 Session key: {session_key[:80]}...")
        logging.info(f"[MCP-RedisCache] 🔑 Global key: {global_key[:80]}...")

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
            logging.info(f"[MCP-RedisCache] ✅ CACHE HIT from {cache_source}!")
            logging.info(
                f"[MCP-RedisCache] 📤 Cached response length: {len(str(respuesta_texto))} chars")
        else:
            logging.info(
                f"[MCP-RedisCache] ❌ CACHE MISS - will call OpenAI model")
    else:
        logging.warning(f"[MCP-RedisCache] ⚠️ Redis cache disabled")

    # Cache miss: llamar al modelo
    if not cache_hit:
        try:
            logging.info(f"[MCP-RedisCache] 🤖 Calling OpenAI model: {model}")
            openai_client = _get_openai_client()
            completion = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": mensaje}],
            )
            respuesta_texto = completion.choices[0].message.content
            logging.info(
                f"[MCP-RedisCache] ✅ Model response received: {len(respuesta_texto or '')} chars")

            # Guardar en cache
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
                        f"[MCP-RedisCache] 💾 Response cached successfully")
                except Exception as cache_err:
                    logging.error(
                        f"[MCP-RedisCache] ❌ Cache write error: {cache_err}")

        except Exception as e:
            logging.error(f"[MCP-RedisCache] ❌ OpenAI model error: {e}")
            return {"ok": False, "error": f"Error llamando al modelo: {e}"}

    dur_ms = (time.perf_counter() - start) * 1000

    logging.info(
        f"[MCP-RedisCache] 📊 Summary: cache_hit={cache_hit}, duration={dur_ms:.0f}ms, source={cache_source}")

    return {
        "ok": True,
        "respuesta": respuesta_texto,
        "cache_hit": cache_hit,
        "origen": origen,
        "duration_ms": round(dur_ms, 2),
        "session_id": session_id,
        "agent_id": agent_id,
        "model": model,
        "cache_source": cache_source,
        "redis_enabled": redis_buffer.is_enabled,
        "msg_hash": msg_hash[:16]  # Para debugging
    }

# Mantener la función original como fallback


async def _post_wrapper(mensaje: str, session_id: str, agent_id: str) -> dict[str, Any]:
    """Fallback: usar endpoint HTTP si cache directo falla"""
    payload = {"mensaje": mensaje,
               "session_id": session_id, "agent_id": agent_id}
    headers = {
        "Session-ID": session_id,
        "Agent-ID": agent_id,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.post(ENDPOINT_URL, headers=headers, json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {"ok": False, "error": f"Respuesta no JSON: {resp.text}"}
        data.setdefault("status", resp.status_code)
        return data


@mcp.tool()
async def redis_cached_chat(
    mensaje: str,
    session_id: str = DEFAULT_SESSION,  # Foundry enviará un valor dinámico aquí
    agent_id: str = DEFAULT_AGENT,      # Foundry enviará un valor dinámico aquí
) -> str:
    """
    USAR PARA: Responder preguntas de usuarios usando cache inteligente.

    Procesa cualquier pregunta/mensaje del usuario con IA y cache Redis:
    - Cache HIT: respuesta instantánea desde Redis (más rápido)
    - Cache MISS: consulta al modelo OpenAI + guarda en cache
    - Incluye metadata: [cache_hit=true/false | origen=cache/openai]

    EJEMPLOS DE USO:
    - "¿Qué es un barco?" 
    - "Explica los tipos de embarcaciones"
    - "¿Cómo funciona el motor de un yate?"

    Args:
        mensaje: Pregunta o consulta del usuario
        session_id: ID de sesión (opcional, se usa cache global)
        agent_id: ID del agente (opcional, se usa cache global)

    Returns:
        Respuesta de IA + metadata de cache performance
    """
    logging.info(
        f"[MCP] Ejecutando redis_cached_chat - mensaje: '{mensaje[:100]}{'...' if len(mensaje) > 100 else ''}'")
    logging.info(
        f"[MCP] IDs recibidos - session_id: {session_id}, agent_id: {agent_id}")

    # IGNORAR los IDs que manda Foundry y usar los forzados para cache global
    cache_session_id = FORCED_SESSION_ID
    cache_agent_id = FORCED_AGENT_ID

    logging.info(
        f"[MCP] IDs aplicados - cache_session_id: {cache_session_id}, cache_agent_id: {cache_agent_id}")
    logging.info(
        f"[MCP] Caché forzada. Original: ({session_id}, {agent_id}) -> Forzado: ({cache_session_id}, {cache_agent_id})")

    try:
        # Usar cache directo de Redis en lugar de HTTP endpoint
        logging.info(
            f"[MCP] 🚀 Using direct Redis cache instead of HTTP endpoint")
        data = _process_with_redis_cache(
            mensaje, cache_session_id, cache_agent_id)

        # Log del resultado
        status = data.get('status', 'unknown')
        cache_hit = data.get('cache_hit', False)
        logging.info(
            f"[MCP] redis_cached_chat completado - status: {status}, cache_hit: {cache_hit}")

        if not data.get("ok"):
            error_msg = f"Error: {data.get('error', 'desconocido')} (status={data.get('status')})"
            logging.warning(f"[MCP] Respuesta con error: {error_msg}")
            return error_msg

        # Incluir señal de cache_hit/origen si está presente
        meta = []
        if "cache_hit" in data:
            meta.append(f"cache_hit={data['cache_hit']}")
        if "origen" in data:
            meta.append(f"origen={data['origen']}")

        respuesta = data.get('respuesta', '')
        logging.info(
            f"[MCP] Respuesta exitosa - longitud: {len(respuesta)} chars, meta: {meta}")

        meta_str = f" [{' | '.join(meta)}]" if meta else ""
        return f"{respuesta}{meta_str}"

    except Exception as exc:
        logging.error(f"[MCP] Error en redis_cached_chat: {exc}")
        return f"Error en MCP wrapper: {str(exc)}"


def main() -> None:
    """
    Ejecuta el servidor MCP.

    - STDIO (default): útil para Claude Desktop/local.
    - HTTP (streamable-http): establece MCP_TRANSPORT=http y opcional MCP_HOST/MCP_PORT.
    """
    if MCP_TRANSPORT == "http":
        logging.info(
            f"Iniciando MCP HTTP (streamable) en {MCP_HOST}:{MCP_PORT} path=/mcp")
        # FastMCP usa "streamable-http" como nombre de transporte HTTP
        mcp.run(transport="streamable-http")
    else:
        logging.info("Iniciando MCP en modo STDIO")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
