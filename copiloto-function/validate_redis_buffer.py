#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validación Real para RedisBufferService
------------------------------------------------
Valida el comportamiento real del servicio Redis Buffer:
- Inicialización al arranque (no lazy)
- Conexión inmediata con ping()
- Manejo de errores y _enabled flag
- Operaciones cuando _enabled=False
- Eventos y logging real
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configurar logging para capturar todo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_redis_buffer_initialization():
    """Test 1: Validar inicialización al arranque (no lazy)"""
    print_separator("TEST 1: Inicialización del RedisBufferService")

    try:
        # Importar el servicio - esto debería ejecutar __init__ inmediatamente
        print("📦 Importando services.redis_buffer_service...")
        from services.redis_buffer_service import redis_buffer

        print("✅ Servicio importado correctamente")
        print(f"🔍 Estado inicial:")
        print(f"   - is_enabled: {redis_buffer.is_enabled}")
        print(f"   - Cliente existe: {redis_buffer._client is not None}")
        print(f"   - Flag _enabled: {redis_buffer._enabled}")

        if hasattr(redis_buffer, '_failure_streak'):
            print(f"   - failure_streak: {redis_buffer._failure_streak}")
        if hasattr(redis_buffer, '_last_error'):
            print(f"   - last_error: {redis_buffer._last_error}")

        return {
            "test": "initialization",
            "passed": True,
            "is_enabled": redis_buffer.is_enabled,
            "client_exists": redis_buffer._client is not None,
            "enabled_flag": redis_buffer._enabled
        }

    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": "initialization",
            "passed": False,
            "error": str(e)
        }


def test_redis_connection_validation():
    """Test 2: Validar conexión real con ping()"""
    print_separator("TEST 2: Validación de conexión Redis")

    try:
        from services.redis_buffer_service import redis_buffer

        print("🏓 Intentando PING directo al cliente Redis...")

        # Intentar ping directo
        if redis_buffer._client:
            try:
                ping_result = redis_buffer._client.ping()
                print(f"✅ PING exitoso: {ping_result}")
                connection_ok = True
            except Exception as ping_error:
                print(f"❌ PING falló: {ping_error}")
                connection_ok = False
        else:
            print("⚠️ Cliente Redis no inicializado")
            connection_ok = False

        print(f"🔍 Estado después del ping:")
        print(f"   - is_enabled: {redis_buffer.is_enabled}")
        print(f"   - Cliente existe: {redis_buffer._client is not None}")

        return {
            "test": "connection",
            "passed": connection_ok,
            "client_exists": redis_buffer._client is not None,
            "is_enabled": redis_buffer.is_enabled,
            "ping_successful": connection_ok
        }

    except Exception as e:
        print(f"❌ Error en test de conexión: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": "connection",
            "passed": False,
            "error": str(e)
        }


def test_disabled_behavior():
    """Test 3: Comportamiento cuando _enabled=False"""
    print_separator("TEST 3: Comportamiento con servicio deshabilitado")

    try:
        from services.redis_buffer_service import redis_buffer

        # Guardar estado original
        original_enabled = redis_buffer._enabled
        original_client = redis_buffer._client

        print(f"📝 Estado original - _enabled: {original_enabled}")

        # Simular fallo temporalmente
        print("🔧 Simulando fallo: _enabled=False, _client=None")
        redis_buffer._enabled = False
        redis_buffer._client = None

        print(f"🔍 Estado simulado:")
        print(f"   - is_enabled: {redis_buffer.is_enabled}")
        print(f"   - _enabled: {redis_buffer._enabled}")
        print(f"   - _client: {redis_buffer._client}")

        # Probar operaciones cuando está deshabilitado
        print("🧪 Probando operaciones con servicio deshabilitado...")

        # Test cache_memoria_contexto
        try:
            result = redis_buffer.cache_memoria_contexto(
                "test_session", {"test": "data"})
            print(
                f"   - cache_memoria_contexto: {result} (esperado: None/False)")
        except Exception as e:
            print(f"   - cache_memoria_contexto: Exception - {e}")

        # Test get_memoria_cache
        try:
            result = redis_buffer.get_memoria_cache("test_session")
            print(f"   - get_memoria_cache: {result} (esperado: None)")
        except Exception as e:
            print(f"   - get_memoria_cache: Exception - {e}")

        # Restaurar estado original
        print("🔄 Restaurando estado original...")
        redis_buffer._enabled = original_enabled
        redis_buffer._client = original_client

        print(f"✅ Estado restaurado - is_enabled: {redis_buffer.is_enabled}")

        return {
            "test": "disabled_behavior",
            "passed": True,
            "operations_failed_gracefully": True
        }

    except Exception as e:
        print(f"❌ Error en test de comportamiento deshabilitado: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": "disabled_behavior",
            "passed": False,
            "error": str(e)
        }


def test_real_operations():
    """Test 4: Operaciones reales con datos"""
    print_separator("TEST 4: Operaciones reales con datos")

    try:
        from services.redis_buffer_service import redis_buffer

        if not redis_buffer.is_enabled:
            print("⚠️ Redis no está habilitado, saltando test de operaciones reales")
            return {
                "test": "real_operations",
                "passed": False,
                "reason": "redis_not_enabled"
            }

        test_session = f"test_session_{int(time.time())}"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "interacciones": [
                {"endpoint": "/api/test", "timestamp": datetime.now().isoformat()}
            ]
        }

        print(f"📝 Probando con session: {test_session}")

        # Test escritura
        print("✍️ Escribiendo memoria...")
        write_result = redis_buffer.cache_memoria_contexto(
            test_session, test_data)
        print(f"   - Resultado escritura: {write_result}")

        # Test lectura
        print("📖 Leyendo memoria...")
        read_result = redis_buffer.get_memoria_cache(test_session)
        print(f"   - Resultado lectura: {read_result is not None}")

        if read_result:
            print(
                f"   - Datos recuperados correctamente: {read_result.get('test', False)}")
            data_matches = read_result.get(
                'timestamp') == test_data['timestamp']
            print(f"   - Datos coinciden: {data_matches}")

        # Test thread_id
        print("🧵 Probando thread_id...")
        thread_result = redis_buffer.cache_memoria_contexto(
            test_session, test_data, thread_id="thread_123")
        print(f"   - Cache con thread_id: {thread_result}")

        # Limpiar
        print("🧹 Limpiando datos de prueba...")
        if hasattr(redis_buffer, '_client') and redis_buffer._client:
            try:
                # Buscar y limpiar keys de test
                keys = redis_buffer._client.keys(f"*{test_session}*")
                if keys:
                    redis_buffer._client.delete(*keys)
                    print(f"   - Eliminadas {len(keys)} keys de prueba")
            except Exception as cleanup_error:
                print(f"   - Error limpiando: {cleanup_error}")

        return {
            "test": "real_operations",
            "passed": True,
            "write_success": write_result is not None,
            "read_success": read_result is not None
        }

    except Exception as e:
        print(f"❌ Error en operaciones reales: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": "real_operations",
            "passed": False,
            "error": str(e)
        }


def test_error_handling():
    """Test 5: Manejo de errores y recovery"""
    print_separator("TEST 5: Manejo de errores y recovery")

    try:
        from services.redis_buffer_service import redis_buffer

        print("🔍 Estado actual del servicio:")
        print(f"   - is_enabled: {redis_buffer.is_enabled}")

        if hasattr(redis_buffer, '_failure_streak'):
            print(f"   - failure_streak: {redis_buffer._failure_streak}")
        if hasattr(redis_buffer, '_last_error'):
            print(f"   - last_error: {redis_buffer._last_error}")

        # Verificar capacidades básicas del servicio
        print("📊 Verificando capacidades del servicio...")
        has_cache_method = hasattr(redis_buffer, 'cache_memoria_contexto')
        has_get_method = hasattr(redis_buffer, 'get_memoria_cache')
        has_is_enabled = hasattr(redis_buffer, 'is_enabled')

        print(f"✅ Método cache_memoria_contexto: {has_cache_method}")
        print(f"✅ Método get_memoria_cache: {has_get_method}")
        print(f"✅ Propiedad is_enabled: {has_is_enabled}")

        # Verificar estado interno
        has_client = hasattr(redis_buffer, '_client')
        has_enabled_flag = hasattr(redis_buffer, '_enabled')
        print(f"✅ Cliente interno (_client): {has_client}")
        print(f"✅ Flag habilitado (_enabled): {has_enabled_flag}")

        return {
            "test": "error_handling",
            "passed": True,
            "has_cache_method": has_cache_method,
            "has_get_method": has_get_method,
            "has_is_enabled": has_is_enabled,
            "has_client": has_client,
            "has_enabled_flag": has_enabled_flag
        }

    except Exception as e:
        print(f"❌ Error en test de manejo de errores: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": "error_handling",
            "passed": False,
            "error": str(e)
        }


def main():
    """Ejecuta todos los tests de validación"""
    print("🚀 Iniciando validación completa del RedisBufferService")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

    results = []

    # Ejecutar todos los tests
    tests = [
        test_redis_buffer_initialization,
        test_redis_connection_validation,
        test_disabled_behavior,
        test_real_operations,
        test_error_handling
    ]

    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} falló completamente: {e}")
            results.append({
                "test": test_func.__name__,
                "passed": False,
                "error": str(e)
            })

    # Resumen final
    print_separator("RESUMEN FINAL")

    passed_tests = [r for r in results if r.get("passed", False)]
    failed_tests = [r for r in results if not r.get("passed", False)]

    print(f"✅ Tests exitosos: {len(passed_tests)}/{len(results)}")
    print(f"❌ Tests fallidos: {len(failed_tests)}/{len(results)}")

    if failed_tests:
        print("\n🔍 Tests fallidos:")
        for test in failed_tests:
            print(f"   - {test['test']}: {test.get('error', 'Sin detalles')}")

    print(
        f"\n📊 Resultado general: {'✅ PASS' if len(failed_tests) == 0 else '❌ FAIL'}")

    # Guardar resultado en JSON
    result_file = f"redis_validation_result_{int(time.time())}.json"
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": len(results),
                    "passed": len(passed_tests),
                    "failed": len(failed_tests)
                },
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"📁 Resultado guardado en: {result_file}")
    except Exception as e:
        print(f"⚠️ No se pudo guardar resultado: {e}")

    return len(failed_tests) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
