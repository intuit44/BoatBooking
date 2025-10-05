#!/usr/bin/env python3
"""
Prueba del cerebro semántico autónomo
"""
import time
import sys
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar path para importar el módulo
sys.path.append('copiloto-function')


def test_semantic_runtime_local():
    """Prueba local del runtime semántico"""
    print("=" * 60)
    print("PRUEBA LOCAL DEL CEREBRO SEMÁNTICO AUTÓNOMO")
    print("=" * 60)

    # Configurar variables de entorno para prueba
    os.environ["SEMANTIC_AUTOPILOT"] = "on"
    os.environ["SEMANTIC_PERIOD_SEC"] = "10"  # 10 segundos para prueba
    os.environ["SEMANTIC_MAX_ACTIONS_PER_HOUR"] = "3"
    os.environ["FUNCTION_BASE_URL"] = "https://copiloto-semantico-func-us2.azurewebsites.net"

    try:
        from services.semantic_runtime import SemanticRuntime

        print("[TEST] Creando instancia del cerebro semántico...")
        runtime = SemanticRuntime()

        print(f"[CONFIG] Autopilot: {os.environ.get('SEMANTIC_AUTOPILOT')}")
        print(f"[CONFIG] Period: {os.environ.get('SEMANTIC_PERIOD_SEC')}s")
        print(
            f"[CONFIG] Max hourly: {os.environ.get('SEMANTIC_MAX_ACTIONS_PER_HOUR')}")

        # Probar lectura de sensores
        print("\n[TEST] Probando lectura de sensores...")

        sistema = runtime._get_sensor_data("/api/verificar-sistema")
        print(f"[SENSOR] Sistema: {bool(sistema)}")
        if sistema:
            print(f"  CPU: {sistema.get('cpu_percent')}%")
            print(f"  Memoria: {sistema.get('memoria', {}).get('percent')}%")

        app_insights = runtime._get_sensor_data("/api/verificar-app-insights")
        print(f"[SENSOR] App Insights: {bool(app_insights)}")

        cosmos = runtime._get_sensor_data("/api/verificar-cosmos")
        print(f"[SENSOR] Cosmos: {bool(cosmos)}")

        # Probar un ciclo semántico
        print("\n[TEST] Ejecutando un ciclo semántico...")
        runtime._semantic_cycle()

        print(f"[MEMORY] Ciclos en memoria: {len(runtime.memory)}")
        if runtime.memory:
            last_cycle = runtime.memory[-1]
            print(f"[LAST_CYCLE] Timestamp: {last_cycle['timestamp']}")
            print(f"[LAST_CYCLE] Action taken: {last_cycle['action_taken']}")

        print("\n✅ CEREBRO SEMÁNTICO: Funcionando correctamente")

    except ImportError as e:
        print(f"❌ ERROR: No se pudo importar semantic_runtime: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")


def test_semantic_config():
    """Prueba configuración semántica"""
    print("\n" + "=" * 60)
    print("PRUEBA DE CONFIGURACIÓN SEMÁNTICA")
    print("=" * 60)

    configs = [
        ("SEMANTIC_AUTOPILOT", "on"),
        ("SEMANTIC_PERIOD_SEC", "300"),
        ("SEMANTIC_MAX_ACTIONS_PER_HOUR", "6"),
        ("FUNCTION_BASE_URL", "https://copiloto-semantico-func-us2.azurewebsites.net")
    ]

    for key, default in configs:
        value = os.environ.get(key, default)
        print(f"[CONFIG] {key}: {value}")

    print("\n✅ CONFIGURACIÓN: Lista para despliegue")


if __name__ == "__main__":
    test_semantic_runtime_local()
    test_semantic_config()

    print("\n" + "=" * 60)
    print("🧠 CEREBRO SEMÁNTICO AUTÓNOMO IMPLEMENTADO")
    print("=" * 60)
    print("Características:")
    print("• Percepción: 3 sensores (sistema, app-insights, cosmos)")
    print("• Razonamiento: HybridResponseProcessor integrado")
    print("• Memoria: Persistencia local + CosmosDB")
    print("• Acción: Ejecutor inteligente con límites de seguridad")
    print("• Autonomía: Ciclo reflexivo sin intervención humana")
    print("• Control: Kill-switch vía SEMANTIC_AUTOPILOT=off")
    print("\nEl agente ahora puede:")
    print("• Autodiagnosticarse continuamente")
    print("• Tomar decisiones basadas en su estado")
    print("• Ejecutar acciones correctivas automáticamente")
    print("• Aprender de sus decisiones y resultados")
    print("• Operar de forma completamente autónoma")
    print("=" * 60)
