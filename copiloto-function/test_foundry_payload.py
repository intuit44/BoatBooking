#!/usr/bin/env python3
"""
Test de Payload Foundry - Simulación exacta del payload enviado por el agente Foundry
Basado en los logs reales de la función buscar_memoria_endpoint
"""

import json
import time
from datetime import datetime


def test_foundry_payload_simulation():
    """
    Simula el payload exacto que envía Foundry según los logs:
    "arguments": "{\"query\":\"validar uso de buscar_memoria_endpoint\",\"agent_id\":\"GlobalAgent\",\"session_id\":\"temp_1765487255\"}"
    """

    print("🧪 TEST: Simulando payload de Foundry")
    print("=" * 60)

    # Payload exacto de Foundry (sin enhancement params)
    foundry_payload = {
        "query": "validar uso de buscar_memoria_endpoint",
        "agent_id": "GlobalAgent",
        "session_id": "temp_1765487255"
    }

    print("📤 Payload Foundry (simulado):")
    print(json.dumps(foundry_payload, indent=2, ensure_ascii=False))
    print()

    # Importar función del endpoint
    try:
        from endpoints_search_memory import buscar_memoria_endpoint
    except ImportError as e:
        print(f"❌ Error importando endpoint: {e}")
        return False

    # Medir tiempo de ejecución
    print("⏱️  Iniciando búsqueda...")
    start_time = time.time()

    try:
        resultado = buscar_memoria_endpoint(foundry_payload)
        end_time = time.time()

        print(f"✅ Búsqueda completada en {end_time - start_time:.2f} segundos")
        print()

        # Analizar respuesta
        print("📊 ANÁLISIS DE RESPUESTA:")
        print("-" * 40)

        if isinstance(resultado, dict):
            print(f"🔹 Éxito: {resultado.get('exito', 'N/A')}")
            print(f"🔹 Total documentos: {resultado.get('total', 0)}")
            print(
                f"🔹 Enhancement LLM activo: {resultado.get('llm_ready', False)}")

            # Verificar si tiene campos enhanced
            enhanced_response = resultado.get('enhanced_response')
            if enhanced_response:
                print(f"🔹 Enhancement response: ✅ Presente")
                print(
                    f"🔹 Narrativa LLM: {'✅' if enhanced_response.get('narrativa_llm') else '❌'}")
                print(
                    f"🔹 Contextos extraídos: {len(enhanced_response.get('contextos_extraidos', []))}")
            else:
                print(f"🔹 Enhancement response: ❌ Ausente (comportamiento esperado)")

            # Mostrar metadata
            metadata = resultado.get('metadata', {})
            if metadata:
                print(
                    f"🔹 Modo búsqueda: {metadata.get('modo_busqueda', 'N/A')}")
                print(
                    f"🔹 Session widening: {metadata.get('session_widening_activo', False)}")

            # Mostrar primeros documentos si existen
            documentos = resultado.get('documentos', [])
            if documentos:
                print(f"\n📄 PRIMER DOCUMENTO:")
                doc = documentos[0]
                print(f"🔸 ID: {doc.get('id', 'N/A')}")
                print(f"🔸 Texto: {doc.get('texto_semantico', 'N/A')[:100]}...")
                print(f"🔸 Score: {doc.get('@search.score', 'N/A')}")
                print(f"🔸 Timestamp: {doc.get('timestamp', 'N/A')}")

        else:
            print(f"❌ Respuesta inesperada: {type(resultado)}")

        print("\n" + "=" * 60)
        return True

    except Exception as e:
        end_time = time.time()
        print(f"❌ Error en búsqueda: {str(e)}")
        print(f"⏱️  Tiempo transcurrido: {end_time - start_time:.2f} segundos")
        return False


def test_foundry_payload_with_enhancement():
    """
    Test adicional: Foundry con parámetros de enhancement explícitos
    """

    print("\n🧪 TEST ADICIONAL: Foundry con Enhancement Explícito")
    print("=" * 60)

    # Payload con enhancement activado
    enhanced_payload = {
        "query": "validar uso de buscar_memoria_endpoint",
        "agent_id": "GlobalAgent",
        "session_id": "temp_1765487255",
        "include_context": True,
        "include_narrative": True,
        "format": "json"
    }

    print("📤 Payload Foundry Enhanced:")
    print(json.dumps(enhanced_payload, indent=2, ensure_ascii=False))
    print()

    try:
        from endpoints_search_memory import buscar_memoria_endpoint

        print("⏱️  Iniciando búsqueda con enhancement...")
        start_time = time.time()

        resultado = buscar_memoria_endpoint(enhanced_payload)
        end_time = time.time()

        print(f"✅ Búsqueda completada en {end_time - start_time:.2f} segundos")

        # Verificar enhancement
        enhanced_response = resultado.get('enhanced_response')
        if enhanced_response:
            print(f"🔹 Enhancement activado: ✅")
            print(
                f"🔹 Narrativa LLM: {'✅' if enhanced_response.get('narrativa_llm') else '❌'}")
            narrativa = enhanced_response.get('narrativa_llm', '')
            if narrativa:
                print(f"🔹 Narrativa preview: {narrativa[:150]}...")
        else:
            print(f"❌ Enhancement no funcionó correctamente")

        return True

    except Exception as e:
        print(f"❌ Error en test enhancement: {str(e)}")
        return False


def test_performance_comparison():
    """
    Comparación de rendimiento: sin enhancement vs con enhancement
    """

    print("\n🏁 TEST RENDIMIENTO: Sin Enhancement vs Con Enhancement")
    print("=" * 60)

    base_payload = {
        "query": "validar uso de buscar_memoria_endpoint",
        "agent_id": "GlobalAgent",
        "session_id": "temp_1765487255"
    }

    enhanced_payload = {**base_payload,
                        "include_context": True, "include_narrative": True}

    try:
        from endpoints_search_memory import buscar_memoria_endpoint

        # Test sin enhancement
        print("⚡ Ejecutando SIN enhancement...")
        start = time.time()
        resultado_base = buscar_memoria_endpoint(base_payload)
        tiempo_base = time.time() - start

        # Test con enhancement
        print("⚡ Ejecutando CON enhancement...")
        start = time.time()
        resultado_enhanced = buscar_memoria_endpoint(enhanced_payload)
        tiempo_enhanced = time.time() - start

        print(f"\n📊 RESULTADOS:")
        print(f"🔸 Sin enhancement: {tiempo_base:.2f}s")
        print(f"🔸 Con enhancement: {tiempo_enhanced:.2f}s")
        print(
            f"🔸 Diferencia: +{tiempo_enhanced - tiempo_base:.2f}s ({((tiempo_enhanced / tiempo_base - 1) * 100):.1f}%)")

        print(
            f"\n🔸 Enhancement funcional: {'✅' if resultado_enhanced.get('llm_ready') else '❌'}")

        return True

    except Exception as e:
        print(f"❌ Error en test de rendimiento: {str(e)}")
        return False


if __name__ == "__main__":
    print(f"🚀 INICIANDO TESTS DE FOUNDRY PAYLOAD")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print()

    # Ejecutar tests
    success_count = 0

    if test_foundry_payload_simulation():
        success_count += 1

    if test_foundry_payload_with_enhancement():
        success_count += 1

    if test_performance_comparison():
        success_count += 1

    print(f"\n🏆 RESUMEN: {success_count}/3 tests exitosos")

    if success_count == 3:
        print("✅ Todos los tests pasaron correctamente")
    else:
        print("⚠️  Algunos tests fallaron - revisar logs")
