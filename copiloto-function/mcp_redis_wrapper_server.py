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
    session_id: str = DEFAULT_SESSION,
    agent_id: str = DEFAULT_AGENT,
) -> str:
    """
    Genera una respuesta pasando primero por Redis.

    Args:
        mensaje: Texto del usuario.
        session_id: Identificador de sesión para cache (opcional).
        agent_id: Identificador de agente (opcional).
    """
    data = await _post_wrapper(mensaje, session_id, agent_id)
    if not data.get("ok"):
        return f"Error: {data.get('error', 'desconocido')} (status={data.get('status')})"
    # Incluir señal de cache_hit/origen si está presente
    meta = []
    if "cache_hit" in data:
        meta.append(f"cache_hit={data['cache_hit']}")
    if "origen" in data:
        meta.append(f"origen={data['origen']}")
    meta_str = f" [{' | '.join(meta)}]" if meta else ""
    return f"{data.get('respuesta', '')}{meta_str}"


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
