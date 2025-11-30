#!/usr/bin/env python3
"""
Test script para verificar que los comandos curl no sean corruptos por el normalizador.
"""

import json
import requests

# URL del endpoint local
BASE_URL = "http://localhost:7071"
CLI_ENDPOINT = f"{BASE_URL}/api/ejecutar-cli"


def test_curl_json_preservation():
    """Test: comando curl con JSON no debe ser corrompido."""
    print("🧪 Probando comando curl con JSON...")

    # Comando curl que antes se rompía
    curl_command = 'curl -X POST "http://localhost:7071/api/deploy" -H "Content-Type: application/json" -d \'{"action": "deployModels", "models": ["claude-3-5-sonnet-20241022"]}\''

    payload = {
        "comando": curl_command
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-curl-fix",
                "Agent-ID": "test-agent"
            },
            timeout=60
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Comando curl ejecutado:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Verificar que el comando se ejecutó correctamente
            if data.get("ok"):
                salida = data.get("salida", "")
                if "deployModels" in salida or "models_deployed" in salida:
                    print("✅ Curl ejecutó correctamente y llegó al endpoint")
                else:
                    print("⚠️ Curl se ejecutó pero puede no haber llegado al endpoint")
            else:
                print("⚠️ Curl reportó error, pero el comando se procesó")
        else:
            print("❌ Error ejecutando curl:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))

                # Verificar si es problema de normalización
                error_msg = str(error_data)
                if "syntax error" in error_msg.lower() or "invalid json" in error_msg.lower():
                    print("❌ POSIBLE BUG DE NORMALIZACIÓN AÚN PRESENTE!")
                else:
                    print("✅ Normalización OK, error es de otra cosa")
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que la Function App esté corriendo: func host start")


def test_simple_curl():
    """Test: curl simple sin JSON."""
    print("\n🧪 Probando curl simple...")

    curl_command = 'curl -X GET "http://localhost:7071/api/dashboard"'

    payload = {
        "comando": curl_command
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-curl-simple",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Curl simple exitoso:")
            print("Salida:", data.get("salida", "")[
                  :200] + "..." if len(data.get("salida", "")) > 200 else data.get("salida", ""))
        else:
            print("❌ Error en curl simple:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")


if __name__ == "__main__":
    print("🔧 Test de corrección del bug de normalización de curl")
    print("=" * 60)

    # Test principal: curl con JSON
    test_curl_json_preservation()

    # Test secundario: curl simple
    test_simple_curl()

    print("\n" + "=" * 60)
    print("✅ Tests completados. Si curl ejecuta sin syntax errors, el fix funciona.")
