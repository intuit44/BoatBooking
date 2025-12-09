#!/usr/bin/env python3
"""
Script para probar el fix de texto_semantico en memory_service.
Reproduce el flujo completo que causaba KeyError('texto_semantico').
"""

import os
import sys
import logging
import json
from datetime import datetime, timezone

# Configurar logging para ver todos los mensajes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    """Test principal para validar el fix de texto_semantico."""

    print("🧪 === TEST DE VALIDACIÓN DEL FIX texto_semantico ===")
    print()

    # Verificar variables de entorno
    print("📋 Verificando configuración:")
    required_vars = ['COSMOSDB_ENDPOINT', 'COSMOSDB_KEY',
                     'COSMOSDB_DATABASE', 'COSMOSDB_CONTAINER']
    for var in required_vars:
        value = os.environ.get(var, 'NO CONFIGURADA')
        print(
            f"  {var}: {'✅' if value != 'NO CONFIGURADA' else '❌'} {value[:50]}{'...' if len(value) > 50 else ''}")
    print()

    try:
        # Importar memory_service después de configurar las variables
        print("📦 Importando memory_service...")
        from services.memory_service import memory_service
        print("✅ memory_service importado correctamente")
        print()

        # Test 1: log_event con texto_semantico en data
        print("🔬 TEST 1: log_event con texto_semantico en data")
        test_data_1 = {
            "endpoint": "test-endpoint",
            "texto_semantico": "Esta es una prueba del fix de texto_semantico",
            "success": True,
            "tipo": "test_fix",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        result_1 = memory_service.log_event(
            "test_fix", test_data_1, "test_session_1")
        print(f"Resultado Test 1: {'✅' if result_1 else '❌'}")
        print()

        # Test 2: registrar_llamada (simular memory_route_wrapper)
        print("🔬 TEST 2: registrar_llamada (simular memory_route_wrapper)")
        test_params = {
            "session_id": "test_session_2",
            "agent_id": "test_agent"
        }

        test_response_data = {
            "texto_semantico": "Conversación consolidada: Esta es una prueba del wrapper de memoria",
            "tipo": "conversation_snapshot",
            "total_interacciones": 5,
            "success": True
        }

        result_2 = memory_service.registrar_llamada(
            source="conversation_snapshot",
            endpoint="test-wrapper-endpoint",
            method="AUTO",
            params=test_params,
            response_data=test_response_data,
            success=True
        )
        print(f"Resultado Test 2: {'✅' if result_2 else '❌'}")
        print()

        # Test 3: Verificar log local
        print("🔬 TEST 3: Verificar archivo de log local")
        log_file = memory_service.semantic_log_file
        if log_file.exists():
            print(f"✅ Archivo de log existe: {log_file}")

            # Leer últimas líneas del log
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-5:] if len(lines) >= 5 else lines

            print("📄 Últimas entradas del log:")
            for i, line in enumerate(last_lines, 1):
                try:
                    entry = json.loads(line.strip())
                    has_texto_semantico = 'texto_semantico' in entry
                    print(f"  {i}. ID: {entry.get('id', 'N/A')[:40]}...")
                    print(
                        f"     texto_semantico: {'✅' if has_texto_semantico else '❌'}")
                    if has_texto_semantico:
                        print(
                            f"     Contenido: {entry['texto_semantico'][:80]}...")
                except json.JSONDecodeError:
                    print(f"  {i}. ❌ Línea malformada")
                print()
        else:
            print(f"❌ Archivo de log no existe: {log_file}")

        print("🎯 === RESUMEN DE LA VALIDACIÓN ===")
        print(f"Test 1 (log_event): {'✅ PASÓ' if result_1 else '❌ FALLÓ'}")
        print(
            f"Test 2 (registrar_llamada): {'✅ PASÓ' if result_2 else '❌ FALLÓ'}")

        if result_1 and result_2:
            print()
            print("🎉 ¡TODOS LOS TESTS PASARON!")
            print("✅ El fix de texto_semantico está funcionando correctamente")
            print("✅ Ya NO deberías ver KeyError('texto_semantico') en los logs")
            print(
                "✅ Deberías ver mensajes '[SEMANTIC] Extrayendo texto_semantico al nivel raíz'")
            print()
            print("🚀 Ahora puedes proceder con:")
            print("   1. Reconstruir la imagen Docker")
            print("   2. Desplegar en Azure")
            print("   3. Probar syncfunctiontriggers")
        else:
            print()
            print("❌ ALGUNOS TESTS FALLARON")
            print("⚠️ Revisa los logs arriba para identificar el problema")

    except Exception as e:
        print(f"❌ ERROR durante las pruebas: {e}")
        logging.exception("Error detallado:")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
