#!/usr/bin/env python3
"""
Test script para verificar que Test-Path funciona correctamente en el endpoint ejecutar-cli
"""

import json
import requests

# URL del endpoint local
BASE_URL = "http://localhost:7071"
CLI_ENDPOINT = f"{BASE_URL}/api/ejecutar-cli"


def test_test_path_command():
    """Test: comando Test-Path de PowerShell."""
    print("🧪 Probando comando Test-Path de PowerShell...")

    # Comando que antes fallaba
    test_path_command = 'Test-Path "C:\\home\\logs\\resumen_memoria.txt"'

    payload = {
        "comando": test_path_command
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-test-path",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Test-Path ejecutado:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Verificar que se ejecutó correctamente
            if data.get("exito"):
                salida = data.get("salida", "")
                print("✅ Test-Path se ejecutó sin errores")
                print(f"Resultado: {salida.strip()}")
            else:
                error_msg = data.get("error", "")
                if "no se reconoce como un comando" in error_msg.lower():
                    print("❌ BUG PERSISTE: Test-Path no se reconoce")
                else:
                    print(f"⚠️ Test-Path falló por otro motivo: {error_msg}")
        else:
            print("❌ Error en la respuesta:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que la Function App esté corriendo: func host start")


def test_get_childitem_command():
    """Test: comando Get-ChildItem que sí funciona para comparar."""
    print("\n🧪 Probando comando Get-ChildItem (que funciona)...")

    get_childitem_command = 'Get-ChildItem "C:\\home\\logs\\resumen_memoria.txt"'

    payload = {
        "comando": get_childitem_command
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-get-childitem",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Get-ChildItem ejecutado:")
            print("Exito:", data.get("exito"))
            print("Salida:", data.get("salida", "")[
                  :200] + "..." if len(data.get("salida", "")) > 200 else data.get("salida", ""))
        else:
            print("❌ Error en Get-ChildItem:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")


def test_simple_test_path():
    """Test: Test-Path simple sin comillas."""
    print("\n🧪 Probando Test-Path simple sin comillas...")

    simple_command = 'Test-Path C:\\Windows'

    payload = {
        "comando": simple_command
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-simple-path",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Test-Path simple ejecutado:")
            print("Exito:", data.get("exito"))
            print("Salida:", data.get("salida", "").strip())
            print("Error:", data.get("error", "").strip())

            # Verificar método de ejecución
            print("Método:", data.get("metodo_ejecucion", "desconocido"))
        else:
            print("❌ Error en Test-Path simple:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")


if __name__ == "__main__":
    print("🔧 Test de corrección del bug de Test-Path")
    print("=" * 60)

    # Test principal: Test-Path que fallaba
    test_test_path_command()

    # Test de comparación: Get-ChildItem que funciona
    test_get_childitem_command()

    # Test simple: Test-Path básico
    test_simple_test_path()

    print("\n" + "=" * 60)
    print("✅ Tests completados. Si Test-Path se ejecuta sin 'no se reconoce', el bug está corregido.")
