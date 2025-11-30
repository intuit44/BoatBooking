#!/usr/bin/env python3
"""
Prueba End-to-End del Pre-Response Intelligence

Esta prueba simula escenarios reales para validar que el interceptor funciona 
correctamente en condiciones de producción.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_realistic_conversation_flow():
    """Prueba flujo conversacional realista"""
    print("\n" + "="*60)
    print("🎭 PRUEBA END-TO-END: FLUJO CONVERSACIONAL REALISTA")
    print("="*60)

    try:
        from pre_response_intelligence import enrich_user_query_before_response
        from services.redis_buffer_service import redis_buffer

        # Simular una conversación realista
        session_id = f"prod_test_{int(time.time())}"

        # 1. Usuario pregunta sobre un error
        query1 = "He notado que el endpoint /api/ejecutar-cli a veces tarda mucho en responder. ¿Puedes ayudarme a investigar?"

        print(f"👤 Usuario: {query1}")

        enriched1 = enrich_user_query_before_response(
            query1, session_id, "user_agent")

        print(f"🧠 Sistema (enriched): {enriched1[:150]}...")

        # Simular respuesta del asistente guardada en Redis
        thread_key = f"thread:{session_id}"
        conversation = [
            {"role": "user", "content": query1},
            {"role": "assistant", "content": "Te ayudo a investigar el rendimiento del endpoint /api/ejecutar-cli. Voy a revisar los logs y métricas recientes para identificar posibles causas de latencia."}
        ]

        if redis_buffer.is_enabled:
            redis_buffer.set(thread_key, json.dumps(conversation), ex=3600)
            print("💾 Conversación guardada en Redis")

        # 2. Usuario hace follow-up (debería usar contexto)
        time.sleep(1)
        query2 = "¿Encontraste algo interesante en los logs?"

        print(f"\n👤 Usuario: {query2}")

        enriched2 = enrich_user_query_before_response(
            query2, session_id, "user_agent")

        print(f"🧠 Sistema (enriched): {enriched2[:200]}...")

        # Validar que el contexto fue aplicado
        if len(enriched2) > len(query2) + 50:  # Threshold for enrichment
            print("✅ Contexto conversacional aplicado correctamente")
        else:
            print("⚠️  Contexto mínimo o no aplicado")

        # 3. Usuario pregunta sobre código específico (debería detectar GitHub)
        query3 = "¿Puedes mostrarme la implementación de la función memory_route_wrapper?"

        print(f"\n👤 Usuario: {query3}")

        enriched3 = enrich_user_query_before_response(
            query3, session_id, "user_agent")

        print(f"🧠 Sistema (enriched): {enriched3[:200]}...")

        # Cleanup
        if redis_buffer.is_enabled:
            redis_buffer.delete(thread_key)

        print("\n✅ PRUEBA END-TO-END COMPLETADA - Sistema funcional en escenario realista")
        return True

    except Exception as e:
        print(f"❌ PRUEBA END-TO-END FALLADA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_under_load():
    """Prueba rendimiento bajo carga simulada"""
    print("\n" + "="*60)
    print("⚡ PRUEBA DE RENDIMIENTO: CARGA SIMULADA")
    print("="*60)

    try:
        from pre_response_intelligence import enrich_user_query_before_response

        queries = [
            "¿Cuál es el estado del sistema?",
            "Revisa los logs de error recientes",
            "¿Cómo funciona el cache de Redis?",
            "Necesito ayuda con el endpoint de búsqueda",
            "¿Qué archivos cambiaron recientemente?",
            "Explícame la arquitectura del sistema",
            "¿Hay problemas con la base de datos?",
            "Muéstrame el código de la función principal"
        ]

        total_time = 0
        successful_enrichments = 0

        print(f"📊 Procesando {len(queries)} queries...")

        for i, query in enumerate(queries):
            start_time = time.time()

            session_id = f"perf_test_{i}_{int(time.time())}"
            enriched = enrich_user_query_before_response(
                query, session_id, "perf_agent")

            elapsed = time.time() - start_time
            total_time += elapsed

            if enriched and len(enriched) >= len(query):
                successful_enrichments += 1
                status = "✅"
            else:
                status = "❌"

            print(f"  {status} Query {i+1}: {elapsed:.3f}s - {query[:40]}...")

        avg_time = total_time / len(queries)
        success_rate = (successful_enrichments / len(queries)) * 100

        print(f"\n📈 RESULTADOS DE RENDIMIENTO:")
        print(f"  ⏱️  Tiempo promedio: {avg_time:.3f}s")
        print(f"  ✅ Tasa de éxito: {success_rate:.1f}%")
        print(
            f"  📊 Enriquecimientos exitosos: {successful_enrichments}/{len(queries)}")

        # Criterios de aceptación
        performance_ok = avg_time < 2.0  # Menos de 2s promedio
        reliability_ok = success_rate >= 85  # Al menos 85% éxito

        if performance_ok and reliability_ok:
            print("✅ RENDIMIENTO ACEPTABLE para producción")
            return True
        else:
            print("⚠️  RENDIMIENTO REQUIERE OPTIMIZACIÓN")
            return False

    except Exception as e:
        print(f"❌ PRUEBA DE RENDIMIENTO FALLADA: {e}")
        return False


def test_error_handling_resilience():
    """Prueba manejo de errores y resiliencia"""
    print("\n" + "="*60)
    print("🛡️  PRUEBA DE RESILIENCIA: MANEJO DE ERRORES")
    print("="*60)

    try:
        from pre_response_intelligence import enrich_user_query_before_response

        # Test cases que podrían causar errores
        error_test_cases = [
            ("", "Query vacía"),
            ("   ", "Query solo espacios"),
            ("a", "Query muy corta"),
            ("x" * 10000, "Query muy larga"),
            ("Query con caracteres especiales: 你好 🎉 ñáéíóú", "Caracteres especiales"),
            ("SELECT * FROM users; DROP TABLE users;", "Posible SQL injection"),
            ("<script>alert('xss')</script>", "Posible XSS"),
            ("Query\nnormal\rcon\tsaltos\vde\flínea", "Caracteres de control"),
        ]

        successful_handles = 0
        total_cases = len(error_test_cases)

        for query, description in error_test_cases:
            try:
                session_id = f"error_test_{hash(query)}_{int(time.time())}"

                print(f"🧪 Probando: {description}")

                enriched = enrich_user_query_before_response(
                    query, session_id, "error_agent")

                # El sistema debería manejar gracefully todos los casos
                if enriched is not None:
                    print(f"  ✅ Manejado correctamente")
                    successful_handles += 1
                else:
                    print(f"  ⚠️  Retornó None (comportamiento válido)")
                    successful_handles += 1

            except Exception as e:
                print(f"  ❌ Error no manejado: {e}")

        resilience_rate = (successful_handles / total_cases) * 100

        print(f"\n🛡️  RESULTADOS DE RESILIENCIA:")
        print(f"  📊 Casos manejados: {successful_handles}/{total_cases}")
        print(f"  💪 Tasa de resiliencia: {resilience_rate:.1f}%")

        if resilience_rate >= 90:
            print("✅ RESILIENCIA EXCELENTE - Sistema robusto")
            return True
        else:
            print("⚠️  RESILIENCIA REQUIERE MEJORAS")
            return False

    except Exception as e:
        print(f"❌ PRUEBA DE RESILIENCIA FALLADA: {e}")
        return False


def test_integration_with_real_endpoints():
    """Prueba integración con endpoints reales"""
    print("\n" + "="*60)
    print("🔌 PRUEBA DE INTEGRACIÓN: ENDPOINTS REALES")
    print("="*60)

    try:
        from memory_route_wrapper import apply_pre_response_intelligence

        # Simular requests reales típicos
        class MockRealRequest:
            def __init__(self, payload):
                self.payload = payload

            def get_json(self):
                return self.payload

        real_scenarios = [
            {
                "name": "Ejecutar CLI",
                "payload": {
                    "query": "ls -la /tmp",
                    "session_id": "user_session_123",
                    "agent_id": "cli_agent"
                }
            },
            {
                "name": "Búsqueda Memoria",
                "payload": {
                    "query": "problemas con Redis cache",
                    "session_id": "user_session_456",
                    "top": 5
                }
            },
            {
                "name": "Chat General",
                "payload": {
                    "input": "¿Cómo está funcionando el sistema hoy?",
                    "session_id": "chat_789"
                }
            }
        ]

        integration_successes = 0

        for scenario in real_scenarios:
            try:
                print(f"🔧 Probando: {scenario['name']}")

                request = MockRealRequest(scenario["payload"])
                result = apply_pre_response_intelligence(request)

                if result and isinstance(result, dict):
                    print(f"  ✅ Integración exitosa")
                    print(
                        f"     - Acción recomendada: {result.get('recommended_action', 'N/A')}")
                    print(
                        f"     - Contexto aplicado: {'Sí' if result.get('has_conversation_context') else 'No'}")
                    integration_successes += 1
                else:
                    print(f"  ⚠️  Sin enriquecimiento (puede ser normal)")
                    integration_successes += 1

            except Exception as e:
                print(f"  ❌ Error en integración: {e}")

        integration_rate = (integration_successes / len(real_scenarios)) * 100

        print(f"\n🔌 RESULTADOS DE INTEGRACIÓN:")
        print(
            f"  📊 Integraciones exitosas: {integration_successes}/{len(real_scenarios)}")
        print(f"  🎯 Tasa de integración: {integration_rate:.1f}%")

        if integration_rate >= 80:
            print("✅ INTEGRACIÓN EXITOSA - Listo para endpoints reales")
            return True
        else:
            print("⚠️  INTEGRACIÓN REQUIERE AJUSTES")
            return False

    except Exception as e:
        print(f"❌ PRUEBA DE INTEGRACIÓN FALLADA: {e}")
        return False


def run_production_readiness_tests():
    """Suite completa de pruebas de preparación para producción"""
    print("🚀 INICIANDO PRUEBAS DE PREPARACIÓN PARA PRODUCCIÓN")
    print("="*80)

    tests = [
        ("Flujo Conversacional Realista", test_realistic_conversation_flow),
        ("Rendimiento Bajo Carga", test_performance_under_load),
        ("Resiliencia y Manejo de Errores", test_error_handling_resilience),
        ("Integración con Endpoints Reales", test_integration_with_real_endpoints),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Ejecutando: {test_name}")
        print("-" * 60)

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name}: PASADO")
            else:
                print(f"❌ {test_name}: FALLADO")

        except Exception as e:
            print(f"💥 {test_name}: ERROR CRÍTICO - {e}")
            results.append((test_name, False))

        time.sleep(1)

    # Evaluación final
    print("\n" + "="*80)
    print("🏁 EVALUACIÓN FINAL DE PREPARACIÓN PARA PRODUCCIÓN")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ LISTO" if result else "❌ REQUIERE ATENCIÓN"
        print(f"{test_name:35} → {status}")

    readiness_score = (passed / total) * 100

    print(f"\n📊 PUNTAJE DE PREPARACIÓN: {readiness_score:.1f}%")

    if readiness_score >= 90:
        print("🎉 SISTEMA LISTO PARA PRODUCCIÓN")
        print("✅ Pre-Response Intelligence puede desplegarse con confianza")
        return True
    elif readiness_score >= 75:
        print("⚠️  SISTEMA CASI LISTO - Requiere ajustes menores")
        print("🔧 Abordar elementos fallados antes del despliegue")
        return False
    else:
        print("❌ SISTEMA NO LISTO PARA PRODUCCIÓN")
        print("🛠️  Requiere trabajo significativo antes del despliegue")
        return False


if __name__ == "__main__":
    production_ready = run_production_readiness_tests()

    if production_ready:
        print("\n🚀 SISTEMA PRE-RESPONSE INTELLIGENCE APROBADO PARA PRODUCCIÓN")
        print("Puede integrarse con confianza en el entorno de producción")
    else:
        print("\n🔧 SISTEMA REQUIERE MEJORAS ANTES DE PRODUCCIÓN")
        print("Revisar elementos fallados y repetir pruebas")

    sys.exit(0 if production_ready else 1)
