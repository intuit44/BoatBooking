#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor MCP (FastMCP) que expone una herramienta cacheada vía Redis.
La herramienta llama al endpoint /api/redis-model-wrapper de la Function App,
de modo que el modelo solo se invoca en caso de cache miss.
"""
import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

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


# Ajustamos host/port en settings para el transporte HTTP; mantenemos
# streamable_http_path=/mcp para handshake.
mcp = FastMCP("redis-wrapper", host=MCP_HOST,
              port=MCP_PORT, streamable_http_path="/mcp")
logging.basicConfig(level=logging.INFO)


async def _post_wrapper(mensaje: str, session_id: str, agent_id: str) -> dict[str, Any]:
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
    Procesa consultas de chat utilizando Redis como cache para optimizar respuestas del modelo.
    Implementa cache dual (sesión + global) para maximizar reutilización y reducir latencia.

    Este endpoint maneja la lógica completa de chat con inteligencia artificial,
    incluyendo detección de intención, routing semántico y cache inteligente.

    Args:
        mensaje: Consulta o mensaje del usuario a procesar
        session_id: Identificador de sesión (se aplica FORCED_SESSION_ID para cache global)
        agent_id: Identificador del agente (se aplica FORCED_AGENT_ID para cache global)

    Returns:
        Respuesta JSON con el contenido generado por el modelo y metadata de cache
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
        f"Caché forzada. Original: ({session_id}, {agent_id}) -> Forzado: ({cache_session_id}, {cache_agent_id})")

    try:
        data = await _post_wrapper(mensaje, cache_session_id, cache_agent_id)

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
