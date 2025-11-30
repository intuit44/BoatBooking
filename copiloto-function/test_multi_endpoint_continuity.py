#!/usr/bin/env python3
"""
Test de continuidad conversacional en MÚLTIPLES endpoints
Verifica que la inyección funciona universalmente
"""

import requests
import json
import time

BASE_URL = "http://localhost:7071/api"


def test_multiple_endpoints():
    session_id = f"multi_test_{int(time.time())}"

    print(f"🧪 Test Multi-Endpoint - Session: {session_id}")
    print("="*50)

    # Test diferentes endpoints con el mismo session_id
    endpoints_to_test = [
        {
            "name": "ejecutar-cli",
            "payload": {"comando": "echo 'Primera interacción desde CLI'"}
        },
        {
            "name": "msearch",
            "payload": {"query": "Segunda interacción desde msearch", "limit": 5}
        },
        {
            "name": "guardar_memoria",
            "payload": {"mensaje": "Tercera interacción desde guardar_memoria"}
        }
    ]

    results = []

    for i, endpoint in enumerate(endpoints_to_test, 1):
        print(f"\n{i}️⃣ Testing endpoint: /{endpoint['name']}")

        try:
            response = requests.post(
                f"{BASE_URL}/{endpoint['name']}",
                json=endpoint['payload'],
                headers={
                    "Session-ID": session_id,
                    "Agent-ID": "multi_test_agent"
                },
                timeout=15
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                metadata = data.get('metadata', {})

                print(
                    f"   Wrapper aplicado: {metadata.get('wrapper_aplicado', False)}")
                print(
                    f"   Memoria aplicada: {metadata.get('memoria_aplicada', False)}")
                print(
                    f"   Interacciones previas: {metadata.get('interacciones_previas', 0)}")

                results.append({
                    "endpoint": endpoint['name'],
                    "wrapper_aplicado": metadata.get('wrapper_aplicado', False),
                    "memoria_aplicada": metadata.get('memoria_aplicada', False),
                    "interacciones_previas": metadata.get('interacciones_previas', 0),
                    "success": True
                })
            else:
                print(f"   ❌ Error: {response.status_code}")
                results.append({
                    "endpoint": endpoint['name'],
                    "success": False,
                    "error": response.status_code
                })

        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({
                "endpoint": endpoint['name'],
                "success": False,
                "error": str(e)
            })

        time.sleep(2)  # Esperar entre requests

    # Resumen
    print(f"\n📊 RESUMEN:")
    for result in results:
        if result['success']:
            print(
                f"   ✅ {result['endpoint']}: Wrapper={result['wrapper_aplicado']}, Memoria={result['memoria_aplicada']}, Previas={result['interacciones_previas']}")
        else:
            print(f"   ❌ {result['endpoint']}: Error={result['error']}")

    # Verificar continuidad acumulativa
    successful_results = [r for r in results if r['success']]
    if len(successful_results) > 1:
        first_previas = successful_results[0]['interacciones_previas']
        last_previas = successful_results[-1]['interacciones_previas']

        print(f"\n🔄 CONTINUIDAD ACUMULATIVA:")
        print(f"   Primera consulta: {first_previas} interacciones previas")
        print(f"   Última consulta: {last_previas} interacciones previas")

        if last_previas >= first_previas:
            print(f"   ✅ La memoria se acumula entre diferentes endpoints")
        else:
            print(f"   ⚠️ Posible problema en acumulación entre endpoints")


if __name__ == "__main__":
    test_multiple_endpoints()
