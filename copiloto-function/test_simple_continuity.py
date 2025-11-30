#!/usr/bin/env python3
"""
Test simple de continuidad conversacional
"""

import requests
import json
import time

# URL del endpoint
ENDPOINT_URL = "http://localhost:7071/api/ejecutar-cli"


def test_simple():
    session_id = f"test_session_{int(time.time())}"

    print(f"🧪 Test simple - Session: {session_id}")

    # Test 1
    print("\n1️⃣ Primera consulta...")
    response1 = requests.post(ENDPOINT_URL, json={
        "comando": "echo 'Esta es mi primera consulta para establecer contexto'"
    }, headers={
        "Session-ID": session_id,
        "Agent-ID": "test_agent"
    }, timeout=10)

    print(f"Status: {response1.status_code}")
    data1 = response1.json()
    print(
        f"Memoria aplicada: {data1.get('metadata', {}).get('memoria_aplicada', False)}")
    print(
        f"Interacciones previas: {data1.get('metadata', {}).get('interacciones_previas', 0)}")

    time.sleep(3)  # Esperar para que se procese

    # Test 2
    print("\n2️⃣ Segunda consulta (debería tener memoria)...")
    response2 = requests.post(ENDPOINT_URL, json={
        "comando": "echo 'Esta es mi segunda consulta, debería recordar la anterior'"
    }, headers={
        "Session-ID": session_id,
        "Agent-ID": "test_agent"
    }, timeout=10)

    print(f"Status: {response2.status_code}")
    data2 = response2.json()
    print(
        f"Memoria aplicada: {data2.get('metadata', {}).get('memoria_aplicada', False)}")
    print(
        f"Interacciones previas: {data2.get('metadata', {}).get('interacciones_previas', 0)}")

    # Verificar contexto conversacional
    contexto = data2.get('contexto_conversacion', {})
    print(f"Mensaje de contexto: {contexto.get('mensaje', 'Sin contexto')}")

    print("\n✅ Test completado")


if __name__ == "__main__":
    test_simple()
