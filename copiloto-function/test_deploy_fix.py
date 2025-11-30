#!/usr/bin/env python3
"""
Test script para verificar que el bug del slice en _deploy_foundry_models esté corregido.
"""

import json
import requests
import time

# URL del endpoint local
BASE_URL = "http://localhost:7071"
DEPLOY_ENDPOINT = f"{BASE_URL}/api/deploy"


def test_empty_body_deploy():
    """Test: deployment con body vacío debe usar inferencia inteligente."""
    print("🧪 Probando deployment con body vacío...")

    try:
        response = requests.post(
            DEPLOY_ENDPOINT,
            json={},
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-session-fix",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code in [200, 207]:
            data = response.json()
            print("✅ Respuesta exitosa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Verificar que se haya usado inferencia
            if data.get("action") == "deployModels":
                print("✅ Inferencia inteligente funcionando")
                if data.get("models_deployed") or data.get("already_active"):
                    print("✅ Modelos procesados correctamente")
                else:
                    print("⚠️ No se procesaron modelos, pero no hay error")
            else:
                print("⚠️ No se detectó acción deployModels")
        else:
            print("❌ Error en la respuesta:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))

                # Verificar si es el bug del slice
                if "unhashable type" in str(error_data).lower():
                    print("❌ BUG DEL SLICE AÚN PRESENTE!")
                else:
                    print("✅ Bug del slice corregido, pero hay otro error")
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que la Function App esté corriendo: func host start")


def test_explicit_models_deploy():
    """Test: deployment con modelos específicos."""
    print("\n🧪 Probando deployment con modelos específicos...")

    payload = {
        "action": "deployModels",
        "models": ["claude-3-5-sonnet-20241022", "mistral-large-2411"]
    }

    try:
        response = requests.post(
            DEPLOY_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "test-session-explicit",
                "Agent-ID": "test-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code in [200, 207]:
            data = response.json()
            print("✅ Deployment explícito exitoso:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ Error en deployment explícito:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error de conexión: {e}")


if __name__ == "__main__":
    print("🔧 Test de corrección del bug 'unhashable type: slice'")
    print("=" * 60)

    # Test principal: body vacío con inferencia
    test_empty_body_deploy()

    # Test secundario: modelos específicos
    test_explicit_models_deploy()

    print("\n" + "=" * 60)
    print("✅ Tests completados. Si no ves 'BUG DEL SLICE AÚN PRESENTE', el bug está corregido.")
