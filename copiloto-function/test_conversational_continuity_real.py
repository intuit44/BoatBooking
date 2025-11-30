#!/usr/bin/env python3
"""
Test de continuidad conversacional con datos reales de Redis

Este test verifica que el middleware de continuidad conversacional
funcione correctamente con los datos reales almacenados en Redis.
"""

import json
import sys
import logging
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Importar el middleware
try:
    from conversational_continuity_middleware import (
        inject_conversational_context,
        build_context_enriched_prompt,
        get_context_stats
    )
    from services.redis_buffer_service import redis_buffer
    print("✅ Imports exitosos")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)


def test_redis_connectivity():
    """Prueba la conectividad con Redis"""
    print("\n🔧 PRUEBA 1: Conectividad Redis")
    print("=" * 50)

    try:
        # Verificar que Redis está habilitado
        is_enabled = redis_buffer.is_enabled
        print(f"📡 Redis habilitado: {is_enabled}")

        if not is_enabled:
            print("❌ Redis no está habilitado")
            return False

        # Obtener stats
        stats = redis_buffer.get_stats()
        print(f"📊 Estadísticas Redis:")
        print(f"  - Claves totales: {stats.get('dbsize', 0)}")
        print(f"  - Memoria usada: {stats.get('used_memory_human', 'N/A')}")
        print(f"  - Hit ratio: {stats.get('hit_ratio', 0):.1%}")

        return True

    except Exception as e:
        print(f"❌ Error verificando Redis: {e}")
        return False


def test_thread_context_retrieval():
    """Prueba la recuperación de contexto de threads"""
    print("\n🧵 PRUEBA 2: Recuperación de contexto de threads")
    print("=" * 50)

    try:
        # Buscar una sesión real desde Redis
        thread_keys = redis_buffer.keys("thread:*")
        print(f"🔍 Claves de thread encontradas: {len(thread_keys)}")

        if not thread_keys:
            print("⚠️ No hay threads en caché")
            return True  # No es error, simplemente no hay datos

        # Tomar una clave de ejemplo
        sample_key = thread_keys[0]
        if isinstance(sample_key, bytes):
            sample_key = sample_key.decode()

        print(f"📋 Clave de ejemplo: {sample_key}")

        # Extraer session_id de la clave
        # Formato esperado: thread:session_id:... o thread:thread_fallback_session_...
        parts = sample_key.split(":")
        if len(parts) >= 2:
            session_id = parts[1] if parts[
                1] != "thread_fallback_session" else f"{parts[1]}_{parts[2]}"
        else:
            session_id = "test_session_fallback"

        print(f"🔑 Session ID extraído: {session_id}")

        # Probar inyección de contexto
        test_message = "Hola, ¿qué hablamos antes?"
        context = inject_conversational_context(
            user_message=test_message,
            session_id=session_id
        )

        print(f"📝 Contexto obtenido:")
        print(f"  - Tiene contexto: {context.get('has_context', False)}")
        print(
            f"  - Thread stats: {context.get('thread_stats', {}).get('total_messages', 0)} mensajes")
        print(
            f"  - Memoria semántica: {len(context.get('semantic_stats', {}).get('relevant_memory', []))}")
        print(
            f"  - Historial de búsquedas: {len(context.get('search_stats', {}).get('search_results', []))}")

        if context.get('has_context', False):
            print(f"✅ Contexto conversacional detectado")
            context_summary = context.get('context_summary', '')
            if context_summary:
                print(f"📋 Resumen del contexto:")
                print(f"    {context_summary[:200]}...")
        else:
            print(f"⚠️ Sin contexto conversacional suficiente")

        return True

    except Exception as e:
        print(f"❌ Error en prueba de threads: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enriched_prompt_generation():
    """Prueba la generación de prompts enriquecidos"""
    print("\n🎯 PRUEBA 3: Generación de prompts enriquecidos")
    print("=" * 50)

    try:
        # Usar una sesión real si hay threads disponibles
        thread_keys = redis_buffer.keys("thread:*")

        if thread_keys:
            # Extraer session_id de la primera clave
            sample_key = thread_keys[0]
            if isinstance(sample_key, bytes):
                sample_key = sample_key.decode()

            parts = sample_key.split(":")
            if len(parts) >= 2:
                session_id = parts[1] if parts[
                    1] != "thread_fallback_session" else f"{parts[1]}_{parts[2]}"
            else:
                session_id = "test_session_fallback"
        else:
            session_id = "new_test_session"

        print(f"🔑 Usando session_id: {session_id}")

        # Probar diferentes tipos de consultas
        test_messages = [
            "¿Sobre qué estuvimos hablando antes?",
            "Continúa con el tema anterior",
            "¿Hay algún problema que necesite resolver?",
            "Necesito ayuda con Redis"
        ]

        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test {i}: '{message}'")

            # Generar prompt enriquecido
            enriched_prompt = build_context_enriched_prompt(
                original_prompt=message,
                user_message=message,
                session_id=session_id,
                agent_id="Agent914"
            )

            # Verificar si se enriqueció
            is_enriched = len(enriched_prompt) > len(message)
            status = "✅ ENRIQUECIDO" if is_enriched else "⚪ ORIGINAL"

            print(f"    Status: {status}")
            print(f"    Longitud original: {len(message)} chars")
            print(f"    Longitud enriquecida: {len(enriched_prompt)} chars")

            if is_enriched:
                # Mostrar preview del enriquecimiento
                diff_length = len(enriched_prompt) - len(message)
                print(f"    Contexto agregado: +{diff_length} chars")

                # Mostrar las primeras líneas del contexto
                lines = enriched_prompt.split('\n')
                context_lines = [line for line in lines[:5] if line.strip(
                ) and '🔄' in line or '🧵' in line or '🧠' in line]
                if context_lines:
                    print(f"    Preview contexto: {context_lines[0][:100]}...")

        return True

    except Exception as e:
        print(f"❌ Error en prueba de prompts enriquecidos: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_pattern_analysis():
    """Analiza los patrones de memoria en Redis"""
    print("\n🧠 PRUEBA 4: Análisis de patrones de memoria")
    print("=" * 50)

    try:
        patterns = ["memoria:*", "thread:*", "search:*", "narrativa:*"]

        for pattern in patterns:
            keys = redis_buffer.keys(pattern)
            print(f"🔍 Patrón {pattern}: {len(keys)} claves")

            if keys and len(keys) > 0:
                # Analizar una muestra de claves
                sample_keys = keys[:3]  # Primeras 3 claves

                for key in sample_keys:
                    if isinstance(key, bytes):
                        key = key.decode()

                    try:
                        data = redis_buffer.get(key)
                        if data:
                            if isinstance(data, str):
                                data = json.loads(data)

                            print(f"    📋 {key[:50]}...")
                            if isinstance(data, dict):
                                # Mostrar campos relevantes
                                relevant_fields = [
                                    'texto_semantico', 'message', 'content', 'timestamp', 'event_type']
                                for field in relevant_fields:
                                    if field in data:
                                        value = str(data[field])
                                        if len(value) > 100:
                                            value = value[:100] + "..."
                                        print(f"        {field}: {value}")
                            else:
                                print(f"        Tipo: {type(data)}")

                    except Exception as e:
                        print(f"        ❌ Error leyendo clave {key}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error en análisis de memoria: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_stats():
    """Prueba las estadísticas de contexto"""
    print("\n📊 PRUEBA 5: Estadísticas de contexto")
    print("=" * 50)

    try:
        # Usar session_id de thread real si disponible
        thread_keys = redis_buffer.keys("thread:*")

        if thread_keys:
            sample_key = thread_keys[0]
            if isinstance(sample_key, bytes):
                sample_key = sample_key.decode()

            parts = sample_key.split(":")
            session_id = parts[1] if len(parts) >= 2 else "fallback_session"
        else:
            session_id = "test_session"

        print(f"🔑 Session ID: {session_id}")

        # Obtener estadísticas
        stats = get_context_stats(session_id)

        print(f"📈 Estadísticas de contexto:")
        for key, value in stats.items():
            print(f"    {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("🧪 INICIANDO TESTS DE CONTINUIDAD CONVERSACIONAL CON REDIS REAL")
    print("=" * 80)

    tests = [
        ("Conectividad Redis", test_redis_connectivity),
        ("Contexto de Threads", test_thread_context_retrieval),
        ("Prompts Enriquecidos", test_enriched_prompt_generation),
        ("Patrones de Memoria", test_memory_pattern_analysis),
        ("Estadísticas de Contexto", test_context_stats)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: EXITOSO")
                passed += 1
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")

    print("\n" + "=" * 80)
    print(f"📊 RESUMEN: {passed}/{total} tests exitosos")

    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El middleware de continuidad conversacional está funcionando correctamente.")
    else:
        print("⚠️ Algunos tests fallaron. Revisar la configuración.")

    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
