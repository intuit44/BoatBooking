#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida uso efectivo de Redis como caché desde dentro del runtime (Foundry/Function).
No expone endpoints; se ejecuta con python validate_cache_usage.py vía ejecutar-cli.
"""

import json
import time
from typing import Any, Dict

from services.redis_buffer_service import redis_buffer


def _p(msg: str) -> None:
    print(msg, flush=True)


def _ttl(key: str) -> int:
    try:
        client = redis_buffer._client  # type: ignore[attr-defined]
        return int(client.ttl(key)) if client else -1
    except Exception:
        return -1


def validar_cache(session_id: str, payload: Dict[str, Any]) -> None:
    _p("=== VALIDACIÓN DE CACHE ===")
    _p(f"Session-ID: {session_id}")

    # Limpia claves previas para un baseline limpio
    redis_buffer.delete(redis_buffer._format_key("memoria", session_id))  # type: ignore[attr-defined]
    redis_buffer.delete(redis_buffer._format_key("thread", session_id))   # type: ignore[attr-defined]

    # Primera escritura (MISS -> WRITE)
    t0 = time.perf_counter()
    write_ok = redis_buffer.cache_memoria_contexto(session_id, payload, thread_id=session_id)
    t1 = time.perf_counter()
    _p(f"Primera escritura ok={write_ok} dur_ms={round((t1-t0)*1000,2)} ttl={_ttl('memoria:'+session_id)}")

    # Primera lectura (debería ser HIT inmediato)
    t0 = time.perf_counter()
    datos1 = redis_buffer.get_memoria_cache(session_id)
    t1 = time.perf_counter()
    _p(f"Primera lectura hit={datos1 is not None} dur_ms={round((t1-t0)*1000,2)} ttl={_ttl('memoria:'+session_id)}")

    # Segunda lectura (medir latencia reducida)
    t0 = time.perf_counter()
    datos2 = redis_buffer.get_memoria_cache(session_id)
    t1 = time.perf_counter()
    _p(f"Segunda lectura hit={datos2 is not None} dur_ms={round((t1-t0)*1000,2)} ttl={_ttl('memoria:'+session_id)}")

    # Comparar payloads
    _p(f"Igual payload guardado/recuperado: {datos2 == payload}")

    # Snapshot de stats básicos
    stats = redis_buffer.get_cache_stats()
    _p("Stats:")
    _p(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if not redis_buffer.is_enabled:
        _p("⚠️ Redis no está habilitado en este entorno.")
    else:
        validar_cache(
            session_id="test_foundry_validation",
            payload={"mensaje": "¿Qué hora es?", "valido": True, "fuente": "self-check"}
        )
