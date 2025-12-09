#!/usr/bin/env python3
"""
Test específico para log_semantic_event que está fallando en verificar_estado_sistema
"""

import os
import sys
import logging
from datetime import datetime

# Configurar entorno
os.environ['COSMOSDB_ENDPOINT'] = "https://copiloto-cosmos.documents.azure.com:443/"
os.environ['COSMOSDB_KEY'] = "iwsmeHZcWSoogZZg5HBS13qSei3yWcOUHaIJZWhy5SqZljmAxxIB13ffJxlniKwZ7PGKeD2oiuELACDbvr66Rg=="
os.environ['COSMOSDB_DATABASE'] = "agentMemory"
os.environ['COSMOSDB_CONTAINER'] = "memory"

# Configurar logging para ver mensajes del fix
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def test_verificar_estado_sistema_event():
    """Test específico para el evento que genera verificar_estado_sistema"""
    try:
        from services.memory_service import memory_service

        print("🧪 Test: log_semantic_event desde verificar_estado_sistema")

        # Simular exactamente lo que hace verificar_estado_sistema
        event_data = {
            "tipo": "monitoring_event",
            "texto_semantico": "Monitoreo verificar-sistema OK - Sistema funcionando correctamente"
        }

        print(f"📝 Evento a registrar: {event_data}")

        # Llamar a log_semantic_event (que internamente llama a log_event)
        resultado = memory_service.log_semantic_event(event_data)

        if resultado:
            print("✅ Test 1 exitoso: log_semantic_event funcionó correctamente")
        else:
            print("❌ Test 1 falló: log_semantic_event retornó False")

        return resultado

    except Exception as e:
        print(f"💥 Test 1 error: {type(e).__name__}: {e}")
        return False


def test_app_insights_event():
    """Test específico para el evento de verificar_app_insights"""
    try:
        from services.memory_service import memory_service

        print("\n🧪 Test: log_semantic_event desde verificar_app_insights")

        # Simular lo que hace verificar_app_insights
        event_data = {
            "tipo": "monitoring_event",
            "texto_semantico": "Monitoreo verificar-app-insights OK - 123 eventos usando tables_iteration"
        }

        print(f"📝 Evento a registrar: {event_data}")

        resultado = memory_service.log_semantic_event(event_data)

        if resultado:
            print("✅ Test 2 exitoso: log_semantic_event funcionó correctamente")
        else:
            print("❌ Test 2 falló: log_semantic_event retornó False")

        return resultado

    except Exception as e:
        print(f"💥 Test 2 error: {type(e).__name__}: {e}")
        return False


def main():
    print("🚀 Iniciando tests de log_semantic_event...")
    print("=" * 60)

    test1_ok = test_verificar_estado_sistema_event()
    test2_ok = test_app_insights_event()

    print("\n" + "=" * 60)
    if test1_ok and test2_ok:
        print("🎉 TODOS LOS TESTS PASARON")
        print("El fix de texto_semantico funciona correctamente con log_semantic_event")
        sys.exit(0)
    else:
        print("🔥 ALGUNOS TESTS FALLARON")
        print("Revisar implementación de log_semantic_event")
        sys.exit(1)


if __name__ == "__main__":
    main()
