#!/usr/bin/env python3
"""
Test de flujos reales de Foundry - Simula payloads exactos
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:7071"  # Cambiar a Azure URL si es necesario
SESSION_ID = f"assistant-test-{int(datetime.now().timestamp())}"
AGENT_ID = "foundry-autopilot"

def test_copiloto_mensaje_vacio():
    """Foundry llama /api/copiloto sin mensaje"""
    print("\n🧪 TEST 1: /api/copiloto con mensaje vacío")
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID,
            "Content-Type": "application/json"
        },
        json={}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tipo: {data.get('tipo')}")
    print(f"Tiene respuesta_usuario: {'respuesta_usuario' in data}")
    return data

def test_copiloto_comando_no_reconocido():
    """Foundry envía comando genérico que debe activar narrativa"""
    print("\n🧪 TEST 2: /api/copiloto con comando no reconocido")
    try:
        response = requests.post(
            f"{BASE_URL}/api/copiloto",
            headers={
                "Session-ID": SESSION_ID,
                "Agent-ID": AGENT_ID,
                "Content-Type": "application/json"
            },
            json={"mensaje": "qué hemos hablado"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print(f"❌ ERROR 500: {response.text[:500]}")
            return {"error": "HTTP 500", "details": response.text}
        
        data = response.json()
        print(f"Acción: {data.get('accion')}")
        print(f"Respuesta usuario: {data.get('respuesta_usuario', '')[:200]}...")
        print(f"Sin embeddings: {data.get('metadata', {}).get('sin_embeddings_adicionales')}")
        return data
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"error": str(e)}

def test_historial_sin_query():
    """Foundry llama /api/historial-interacciones sin filtros"""
    print("\n🧪 TEST 3: /api/historial-interacciones sin query")
    response = requests.get(
        f"{BASE_URL}/api/historial-interacciones",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID
        },
        params={"limit": 10}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tiene interacciones: {'interacciones' in data}")
    print(f"Total: {len(data.get('interacciones', []))}")
    return data

def test_historial_con_filtros():
    """Foundry llama con session_id en query (caso problemático)"""
    print("\n🧪 TEST 4: /api/historial-interacciones con filtros")
    response = requests.get(
        f"{BASE_URL}/api/historial-interacciones",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID
        },
        params={"session_id": SESSION_ID, "limit": 5}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tiene respuesta_usuario: {'respuesta_usuario' in data}")
    print(f"Tiene narrativa: {'resumen' in data or 'texto_semantico' in data}")
    return data

def test_listar_threads():
    """Verificar que los threads se guardaron"""
    print("\n🧪 TEST 5: /api/listar-blobs para verificar threads")
    response = requests.get(
        f"{BASE_URL}/api/listar-blobs",
        params={"prefix": "threads/", "top": 10}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    blobs = data.get("blobs", [])
    print(f"Threads encontrados: {len(blobs)}")
    for blob in blobs[:3]:
        print(f"  - {blob.get('name')}")
    return data

if __name__ == "__main__":
    print(f"🚀 Iniciando tests con Session-ID: {SESSION_ID}")
    
    # Ejecutar tests en orden
    test_copiloto_mensaje_vacio()
    test_copiloto_comando_no_reconocido()
    test_historial_sin_query()
    test_historial_con_filtros()
    test_listar_threads()
    
    print("\n✅ Tests completados")
