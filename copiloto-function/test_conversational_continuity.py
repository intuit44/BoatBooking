#!/usr/bin/env python3
"""
Test de Continuidad Conversacional Automática

Valida que el middleware de continuidad conversacional:
✅ Inyecte automáticamente contexto desde Redis
✅ Enriquezca prompts con historial de conversación
✅ Proporcione continuidad sin herramientas explícitas
✅ Funcione transparentemente con los agentes existentes

🎯 Objetivo: Demostrar continuidad real en las respuestas de los agentes
"""

import json
import sys
import os
import time
import logging
from datetime import datetime, timezone, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(__file__))


def test_conversational_continuity():
    """Prueba principal de continuidad conversacional"""
    try:
        # 1. ⚙️ IMPORTAR MÓDULOS NECESARIOS
        from conversational_continuity_middleware import inject_conversational_context, build_context_enriched_prompt, get_context_stats
        from services.redis_buffer_service import redis_buffer

        print("🚀 Iniciando test de continuidad conversacional...")

        # 2. ✅ VERIFICAR CONEXIÓN A REDIS
        if not redis_buffer.is_enabled:
            print("❌ Redis no está habilitado - test cancelado")
            return False

        try:
            redis_info = redis_buffer.ping()
            print(f"✅ Redis conectado: {redis_info}")
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            return False

        # 3. 🔍 EXAMINAR CLAVES EXISTENTES
        print("\n📊 Estado actual de Redis:")

        # Contar claves por patrón
        thread_keys = redis_buffer.keys("thread:*")
        memory_keys = redis_buffer.keys("memoria:*")
        search_keys = redis_buffer.keys("search:*")

        print(f"   • Thread keys: {len(thread_keys)}")
        print(f"   • Memory keys: {len(memory_keys)}")
        print(f"   • Search keys: {len(search_keys)}")

        if len(thread_keys) == 0:
            print("⚠️ No hay threads en Redis - creando datos de prueba...")
            _create_test_conversation_data()

        # 4. 🧪 PROBAR INYECCIÓN DE CONTEXTO
        print("\n🧪 Probando inyección de contexto...")

        test_cases = [
            {
                "session_id": "test-session-123",
                "user_message": "¿cómo está funcionando Redis?",
                "description": "Consulta sobre Redis"
            },
            {
                "session_id": "test-session-123",
                "user_message": "¿de qué hablamos ayer?",
                "description": "Referencia al historial"
            },
            {
                "session_id": "test-session-456",
                "user_message": "ejecutar comandos PowerShell",
                "description": "Nueva sesión, comando técnico"
            }
        ]

        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: {test_case['description']} ---")

            # Inyectar contexto
            context = inject_conversational_context(
                user_message=test_case["user_message"],
                session_id=test_case["session_id"],
                agent_id="Agent975"
            )

            # Mostrar resultados
            print(f"✅ Has Context: {context.get('has_context', False)}")
            if context.get('has_context'):
                thread_stats = context.get('thread_stats', {})
                semantic_stats = context.get('semantic_stats', {})
                search_stats = context.get('search_stats', {})

                print(
                    f"   📞 Thread: {thread_stats.get('total_messages', 0)} mensajes")
                print(
                    f"   🧠 Memoria: {len(semantic_stats.get('relevant_memory', []))} items")
                print(
                    f"   🔍 Búsquedas: {len(search_stats.get('search_results', []))} resultados")

                # Mostrar contexto inyectado
                context_summary = context.get('context_summary', '')
                if context_summary:
                    print(f"   📝 Resumen: {context_summary[:200]}...")

            # Probar construcción de prompt enriquecido
            if context.get('has_context'):
                enriched_prompt = build_context_enriched_prompt(
                    original_prompt=test_case["user_message"],
                    user_message=test_case["user_message"],
                    session_id=test_case["session_id"],
                    agent_id="Agent975"
                )

                print(
                    f"   🎯 Prompt Enriquecido: {len(enriched_prompt)} caracteres")
                print(f"   📖 Preview: {enriched_prompt[:150]}...")

        # 5. 📈 ESTADÍSTICAS FINALES
        print("\n📈 Estadísticas de contexto:")

        for session_id in ["test-session-123", "test-session-456", "nueva-session-789"]:
            stats = get_context_stats(session_id)
            print(f"   • Sesión {session_id[:12]}...: Context={stats.get('has_context', False)} | "
                  f"Messages={stats.get('thread_messages', 0)} | "
                  f"Memory={stats.get('semantic_memories', 0)}")

        print("\n✅ Test de continuidad conversacional completado exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error en test de continuidad: {e}")
        import traceback
        traceback.print_exc()
        return False


def _create_test_conversation_data():
    """Crea datos de prueba para simular conversaciones previas"""
    try:
        from services.redis_buffer_service import redis_buffer

        # Crear algunos mensajes de thread simulados
        test_threads = [
            {
                "key": "thread:test-session-123:msg_001",
                "data": {
                    "session_id": "test-session-123",
                    "agent_id": "Agent975",
                    "event_type": "user_input",
                    "texto_semantico": "¿Cómo configurar Redis para el proyecto?",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                    "exito": True
                }
            },
            {
                "key": "thread:test-session-123:msg_002",
                "data": {
                    "session_id": "test-session-123",
                    "agent_id": "Agent975",
                    "event_type": "agent_response",
                    "texto_semantico": "Redis está configurado con Azure Cache, usando puerto 6380 con SSL",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1, minutes=50)).isoformat(),
                    "exito": True
                }
            }
        ]

        # Crear memoria semántica simulada
        test_memory = [
            {
                "key": "memoria:redis_config",
                "data": {
                    "content": "Configuración de Redis completada con éxito usando Azure Cache for Redis",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
                    "type": "configuration"
                }
            }
        ]

        # Insertar en Redis
        for thread in test_threads:
            redis_buffer.set(thread["key"], json.dumps(
                thread["data"]), ex=3600)
            print(f"   ✅ Thread creado: {thread['key']}")

        for memory in test_memory:
            redis_buffer.set(memory["key"], json.dumps(
                memory["data"]), ex=3600)
            print(f"   🧠 Memoria creada: {memory['key']}")

        print(f"✅ Datos de prueba creados en Redis")

    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")


def test_middleware_integration():
    """Prueba la integración del middleware con memory_route_wrapper"""
    print("\n🔗 Probando integración del middleware...")

    try:
        # Simular request HTTP con body
        class MockRequest:
            def __init__(self, body_data, headers=None):
                self._body = body_data
                self._headers = headers or {}
                self.method = "POST"

            def get_json(self):
                return self._body

            @property
            def headers(self):
                return self._headers

        # Test case: mensaje que debería activar continuidad
        test_body = {
            "input": "¿qué comandos Redis ejecutamos antes?",
            "session_id": "test-session-123"
        }

        test_headers = {
            "Session-ID": "test-session-123",
            "Agent-ID": "Agent975"
        }

        mock_req = MockRequest(test_body, test_headers)

        # Simular procesamiento del middleware
        from conversational_continuity_middleware import build_context_enriched_prompt

        enriched = build_context_enriched_prompt(
            original_prompt=test_body["input"],
            user_message=test_body["input"],
            session_id="test-session-123",
            agent_id="Agent975"
        )

        print(f"   📥 Input Original: {test_body['input']}")
        print(f"   🎯 Prompt Enriquecido: {len(enriched)} chars")
        print(f"   📖 Preview: {enriched[:200]}...")

        # Verificar que el prompt fue enriquecido
        if len(enriched) > len(test_body["input"]) * 2:
            print("   ✅ Middleware aplicado correctamente - prompt enriquecido")
            return True
        else:
            print("   ⚠️ Middleware no aplicó enriquecimiento suficiente")
            return False

    except Exception as e:
        print(f"   ❌ Error en integración: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 TEST DE CONTINUIDAD CONVERSACIONAL AUTOMÁTICA")
    print("=" * 60)

    # Ejecutar todos los tests
    success = True

    success &= test_conversational_continuity()
    success &= test_middleware_integration()

    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS LOS TESTS PASARON - Continuidad conversacional operativa!")
        print("🎯 Los agentes ahora responderán con verdadera continuidad conversacional")
    else:
        print("❌ ALGUNOS TESTS FALLARON - Revisar configuración")

    print("=" * 60)

    sys.exit(0 if success else 1)
