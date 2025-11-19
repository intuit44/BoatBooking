# -*- coding: utf-8 -*-
"""
Script rápido para validar RedisBufferService en local/Azure.
Carga automáticamente las variables de local.settings.json (Values) si están
disponibles para que REDIS_HOST/REDIS_KEY/etc. se apliquen antes de crear
la instancia del servicio.
"""
from pathlib import Path
import json
import os
import time


def _bootstrap_settings() -> None:
    """Carga local.settings.json (Values) a os.environ si existe."""
    local_settings = Path(__file__).with_name("local.settings.json")
    if not local_settings.exists():
        return

    try:
        data = json.loads(local_settings.read_text(encoding="utf-8"))
        values = data.get("Values", {})
        for key, value in values.items():
            if key and isinstance(key, str) and value is not None:
                # Respetar valores existentes del entorno
                os.environ.setdefault(key, str(value))
    except Exception as exc:
        print(f"[test_redis] No se pudieron cargar local.settings.json: {exc}")


_bootstrap_settings()

from services.redis_buffer_service import RedisBufferService  # noqa: E402

buffer = RedisBufferService()
print(f"[test_redis] RedisBuffer habilitado: {buffer.is_enabled}")
if not buffer.is_enabled:
    print("[test_redis] RedisBuffer no está habilitado; revisa credenciales/conexión.")
    raise SystemExit(1)

buffer._json_set("test:key", {"status": "ok",
                 "timestamp": time.time()}, ttl=60)
result = buffer._json_get("test:key")
print(result)
