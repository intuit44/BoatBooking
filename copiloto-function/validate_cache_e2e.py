#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida uso de Redis en un flujo end-to-end llamando al endpoint de chat/agente.
Ejecuta dos llamadas con el mismo Session-ID y mide latencias/HIT esperados.

Uso desde Foundry (ejecutar-cli):
  python validate_cache_e2e.py

Config:
  ENDPOINT_URL : URL completa del endpoint de chat (https://.../api/tu-endpoint)
  SESSION_ID   : Session-ID fijo para la prueba (default: test_foundry_e2e)
  AGENT_ID     : Agent-ID a usar (default: GlobalAgent)
  PAYLOAD_FILE : Ruta a un JSON con el body; si no, usa {"mensaje": "¿Qué hora es?"}
"""

import json
import os
import time
from typing import Any, Dict

import requests


def _load_payload() -> Dict[str, Any]:
    pf = os.getenv("PAYLOAD_FILE")
    if pf and os.path.exists(pf):
        with open(pf, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mensaje": "¿Qué hora es?"}


def _call_endpoint(url: str, session_id: str, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Session-ID": session_id,
        "Agent-ID": agent_id,
    }
    t0 = time.perf_counter()
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    dur_ms = (time.perf_counter() - t0) * 1000
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    return {
        "status": resp.status_code,
        "duration_ms": round(dur_ms, 2),
        "data": data,
    }


def main() -> None:
    # URL por defecto con code ya incluido; puedes sobrescribir con ENDPOINT_URL si lo prefieres
    url = os.getenv("ENDPOINT_URL") or "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar_cli_http?code=EQKFb6twoyqotvg_kMiBaaefWiOGNoVB4gwGFBOCCFLCAzFurK--Ng=="

    session_id = os.getenv("SESSION_ID", "test_foundry_e2e")
    agent_id = os.getenv("AGENT_ID", "GlobalAgent")
    payload = _load_payload()

    print(f"== Validación E2E Redis + Agente ==")
    print(f"Endpoint: {url}")
    print(f"Session-ID: {session_id} | Agent-ID: {agent_id}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

    print("\nLlamada 1 (esperado MISS + WRITE)...")
    r1 = _call_endpoint(url, session_id, agent_id, payload)
    print(json.dumps(r1, ensure_ascii=False, indent=2))

    print("\nLlamada 2 (esperado HIT + menor latencia)...")
    r2 = _call_endpoint(url, session_id, agent_id, payload)
    print(json.dumps(r2, ensure_ascii=False, indent=2))

    print("\nResumen:")
    print(f"Duración 1: {r1['duration_ms']} ms")
    print(f"Duración 2: {r2['duration_ms']} ms")
    print("TIP: Revisa logs de la Function para ver [RedisBuffer] cache HIT/MISS con esta Session-ID.")


if __name__ == "__main__":
    main()
