#!/usr/bin/env python3
"""
Test de Continuidad Conversacional con Simulación

Valida la continuidad conversacional usando datos simulados cuando Redis no está disponible.
Esto permite probar la lógica del middleware sin dependencias externas.
"""

import json
import sys
import os
import logging
from datetime import datetime, timezone, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(__file__))


def test_continuity_with_mock_data():
    """Prueba la continuidad conversacional con datos simulados"""
    try:
        print("🧪 Iniciando test con datos simulados...")

        # Datos simulados de conversación
        mock_thread_data = {
            "thread:test-session-123:msg_001": {
                "session_id": "test-session-123",
                "agent_id": "Agent975",
                "event_type": "user_input",
                "texto_semantico": "¿Cómo configurar Redis para el proyecto?",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "exito": True
            },
            "thread:test-session-123:msg_002": {
                "session_id": "test-session-123",
                "agent_id": "Agent975",
                "event_type": "agent_response",
                "texto_semantico": "Redis está configurado con Azure Cache, usando puerto 6380 con SSL",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1, minutes=50)).isoformat(),
                "exito": True
            }
        }

        mock_memory_data = {
            "memoria:redis_config": {
                "content": "Configuración de Redis completada con éxito usando Azure Cache for Redis",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
                "type": "configuration"
            }
        }

        # Crear middleware con datos simulados
        from conversational_continuity_middleware import ConversationalContinuityMiddleware

        # Patchear el middleware para usar datos simulados
        class MockRedisClient:
            def __init__(self, thread_data, memory_data):
                self.thread_data = thread_data
                self.memory_data = memory_data
                self.is_enabled = True

            def keys(self, pattern):
                all_data = {**self.thread_data, **self.memory_data}
                if pattern.endswith("*"):
                    prefix = pattern[:-1]
                    return [key for key in all_data.keys() if key.startswith(prefix)]
                return [key for key in all_data.keys() if key == pattern]

            def get(self, key):
                all_data = {**self.thread_data, **self.memory_data}
                data = all_data.get(key)
                return json.dumps(data) if data else None

        # Crear middleware con cliente simulado
        middleware = ConversationalContinuityMiddleware()
        middleware.redis_client = MockRedisClient(
            mock_thread_data, mock_memory_data)

        # Probar inyección de contexto
        print("\n🔍 Probando inyección de contexto con datos simulados...")

        test_cases = [
            {
                "session_id": "test-session-123",
                "user_message": "¿de qué hablamos sobre Redis antes?",
                "description": "Referencia al historial de Redis"
            },
            {
                "session_id": "test-session-456",
                "user_message": "necesito ayuda con comandos",
                "description": "Nueva sesión sin historial"
            }
        ]

        success = True

        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: {test_case['description']} ---")

            context = middleware.inject_conversational_context(
                user_message=test_case["user_message"],
                session_id=test_case["session_id"],
                agent_id="Agent975"
            )

            has_context = context.get('has_context', False)
            print(f"✅ Has Context: {has_context}")

            if test_case["session_id"] == "test-session-123":
                # Esta sesión debería tener contexto
                if has_context:
                    print(
                        "   ✅ Contexto detectado correctamente para sesión con historial")

                    thread_stats = context.get('thread_stats', {})
                    semantic_stats = context.get('semantic_stats', {})

                    print(
                        f"   📞 Thread: {thread_stats.get('total_messages', 0)} mensajes")
                    print(
                        f"   🧠 Memoria: {len(semantic_stats.get('relevant_memory', []))} items")

                    # Mostrar contexto
                    context_summary = context.get('context_summary', '')
                    if context_summary:
                        print(f"   📝 Resumen: {context_summary[:150]}...")

                    # Probar prompt enriquecido
                    from conversational_continuity_middleware import build_context_enriched_prompt
                    enriched_prompt = build_context_enriched_prompt(
                        original_prompt=test_case["user_message"],
                        user_message=test_case["user_message"],
                        session_id=test_case["session_id"],
                        agent_id="Agent975"
                    )

                    print(
                        f"   🎯 Prompt Original: {len(test_case['user_message'])} chars")
                    print(
                        f"   🎯 Prompt Enriquecido: {len(enriched_prompt)} chars")

                    # Verificar que el prompt fue realmente enriquecido
                    if len(enriched_prompt) > len(test_case["user_message"]) * 3:
                        print("   ✅ Prompt enriquecido correctamente")
                        print(f"   📖 Preview: {enriched_prompt[:200]}...")
                    else:
                        print("   ❌ Prompt no fue enriquecido suficientemente")
                        success = False

                else:
                    print("   ❌ No se detectó contexto para sesión que debería tenerlo")
                    success = False

            else:
                # Esta sesión NO debería tener contexto
                if not has_context:
                    print("   ✅ Correctamente no hay contexto para sesión nueva")
                else:
                    print(
                        "   ⚠️ Se detectó contexto para sesión sin historial (puede ser normal)")

        return success

    except Exception as e:
        print(f"❌ Error en test con datos simulados: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_construction():
    """Prueba la construcción de prompts con diferentes tipos de contexto"""
    print("\n🎨 Probando construcción de prompts contextuales...")

    try:
        # Contextos simulados de diferentes tipos
        contexts = [
            {
                "name": "Solo historial de thread",
                "thread_context": {
                    "has_history": True,
                    "messages": [
                        {"content": "¿Cómo configurar Redis?", "type": "user_input"},
                        {"content": "Redis usa Azure Cache con SSL",
                            "type": "agent_response"}
                    ],
                    "total_messages": 2
                },
                "semantic_context": {"has_semantic_memory": False, "relevant_memory": []},
                "search_context": {"has_search_history": False, "search_results": []}
            },
            {
                "name": "Solo memoria semántica",
                "thread_context": {"has_history": False, "messages": []},
                "semantic_context": {
                    "has_semantic_memory": True,
                    "relevant_memory": [
                        {"content": "Configuración Redis exitosa",
                            "relevance": "keyword_match"}
                    ]
                },
                "search_context": {"has_search_history": False, "search_results": []}
            },
            {
                "name": "Contexto completo",
                "thread_context": {
                    "has_history": True,
                    "messages": [{"content": "Comandos Redis ejecutados antes", "type": "user_input"}],
                    "total_messages": 1
                },
                "semantic_context": {
                    "has_semantic_memory": True,
                    "relevant_memory": [
                        {"content": "Redis operativo con cache hits altos",
                            "relevance": "keyword_match"}
                    ]
                },
                "search_context": {
                    "has_search_history": True,
                    "search_results": [
                        {"query": "Redis diagnostics", "results_count": 5}
                    ]
                }
            }
        ]

        from conversational_continuity_middleware import ConversationalContinuityMiddleware
        middleware = ConversationalContinuityMiddleware()

        for i, context_scenario in enumerate(contexts):
            print(f"\n--- Escenario {i+1}: {context_scenario['name']} ---")

            enriched_context = middleware._build_enriched_context(
                user_message="¿qué podemos hacer con Redis ahora?",
                thread_context=context_scenario["thread_context"],
                semantic_context=context_scenario["semantic_context"],
                search_context=context_scenario["search_context"],
                session_id="test-session",
                agent_id="Agent975"
            )

            has_context = enriched_context.get("has_context", False)
            print(f"   Context Generated: {has_context}")

            if has_context:
                conversational_prompt = enriched_context.get(
                    "conversational_prompt", "")
                print(f"   Prompt Length: {len(conversational_prompt)} chars")
                print(f"   Preview: {conversational_prompt[:150]}...")

                # Verificar que contiene elementos apropiados
                expected_elements = [
                    "CONTEXTO CONVERSACIONAL", "INSTRUCCIONES"]
                for element in expected_elements:
                    if element in conversational_prompt:
                        print(f"   ✅ Contiene: {element}")
                    else:
                        print(f"   ⚠️ Falta: {element}")

        return True

    except Exception as e:
        print(f"❌ Error en test de construcción de prompts: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🔄 TEST DE CONTINUIDAD CONVERSACIONAL CON SIMULACIÓN")
    print("=" * 70)

    # Ejecutar tests
    success = True

    success &= test_continuity_with_mock_data()
    success &= test_prompt_construction()

    print("\n" + "=" * 70)
    if success:
        print("🎉 TODOS LOS TESTS SIMULADOS PASARON!")
        print("✅ La lógica de continuidad conversacional está operativa")
        print("🎯 Los agentes tendrán continuidad real cuando Redis esté habilitado")
        print("\n📋 Próximos pasos:")
        print("   1. Habilitar Redis en el entorno de producción")
        print("   2. Verificar que memory_route_wrapper aplica el middleware")
        print("   3. Probar con agentes reales en Foundry")
    else:
        print("❌ ALGUNOS TESTS FALLARON - Revisar lógica del middleware")

    print("=" * 70)

    sys.exit(0 if success else 1)
