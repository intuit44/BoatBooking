#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba rápida de configuración Redis Enterprise (RedisJSON + TLS).
Ejecuta diagnósticos, muestra la configuración detectada y valida las operaciones
de caché básicas utilizadas por redis_buffer_service.
"""

import os
import sys
from services.redis_buffer_service import redis_buffer

# Asegurar salida UTF-8 donde sea posible para evitar UnicodeEncodeError en cp1252
try:  # pragma: no cover - best effort
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def test_configuration():
    print("=" * 60)
    print("Testing Redis Enterprise Configuration")
    print("=" * 60)

    print("\nConfiguración detectada:")
    print(f"  REDIS_HOST: {os.getenv('REDIS_HOST', 'No configurado')}")
    print(f"  REDIS_PORT: {os.getenv('REDIS_PORT', 'No configurado')}")
    redis_key = os.getenv("REDIS_KEY")
    print(f"  REDIS_KEY: {'***' + redis_key[-4:] if redis_key else 'No configurado'}")
    print(f"  REDIS_SSL: {os.getenv('REDIS_SSL', 'No configurado')}")

    print("\nProbando conexión...")
    result = redis_buffer.test_connection()

    if result.get("connected"):
        print("Conexion exitosa")
        print(f"   Redis versión: {result['info'].get('version', 'N/A')}")
        print(f"   RedisJSON disponible: {result.get('redisjson_available')}")
        print(f"   Memoria usada: {result['info'].get('memory', 'N/A')}")
        print(f"   Clientes conectados: {result['info'].get('clients', 'N/A')}")

        print("\nTest de caché de memoria:")
        test_session = "test_session"
        test_thread = "test_thread"
        test_data = {"test": True, "message": "Hola Redis Enterprise!"}

        redis_buffer.cache_memoria_contexto(test_session, test_data, test_thread)
        retrieved = redis_buffer.get_memoria_cache(test_session)

        if retrieved and retrieved.get("message") == "Hola Redis Enterprise!":
            print("  Cache memoria funciona")
        else:
            print("  Cache memoria falló")

        # Limpiar
        redis_buffer.delete(redis_buffer._format_key("memoria", test_session))
        redis_buffer.delete(redis_buffer._format_key("thread", test_thread))
    else:
        print(f"Error de conexión: {result.get('error', 'Desconocido')}")
        print("\nSugerencias:")
        print("  1. Verifica que REDIS_KEY termine con '=' si es requerido")
        print("  2. Host: managed-redis-copiloto.eastus2.redis.azure.net")
        print("  3. Puerto: 10000, TLS habilitado")
        print("  4. Revisa firewall/red")

    print("\nEstadísticas finales:")
    stats = redis_buffer.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_configuration()
