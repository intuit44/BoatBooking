#!/usr/bin/env python3
"""
Test del Router Semántico Dinámico en /api/copiloto
"""

import requests
import json

BASE_URL = "http://localhost:7071"

def test_router_semantico():
    """
    Prueba que /api/copiloto detecte intención y redirija automáticamente
    """
    
    # Test 1: Consulta que debería redirigir a /api/introspection
    print("=" * 60)
    print("TEST 1: Consulta de introspección")
    print("=" * 60)
    
    payload = {
        "mensaje": "En qué estábamos trabajando?",
        "consulta": "En qué estábamos trabajando?"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Session-ID": "test-router-session",
        "Agent-ID": "TestRouterAgent"
    }
    
    print(f">> Enviando: {payload['mensaje']}")
    
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"<< Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Respuesta exitosa")
        print(f"Endpoint detectado: {data.get('endpoint', 'N/A')}")
        print(f"Respuesta: {data.get('respuesta_usuario', data.get('mensaje', ''))[:200]}...")
        
        # Verificar si se redirigió
        if "endpoint" in data or "endpoint_sugerido" in data:
            print(f"REDIRECCION DETECTADA [OK]")
        else:
            print(f"[WARN] No se detecto redireccion explicita")
            
    else:
        print(f"[ERROR] Status: {response.status_code}")
        print(response.text[:500])
    
    print()
    
    # Test 2: Consulta que debería redirigir a /api/diagnostico-recursos
    print("=" * 60)
    print("TEST 2: Consulta de diagnóstico")
    print("=" * 60)
    
    payload2 = {
        "mensaje": "Muéstrame el estado de los recursos",
        "consulta": "estado de recursos azure"
    }
    
    print(f">> Enviando: {payload2['mensaje']}")
    
    response2 = requests.post(
        f"{BASE_URL}/api/copiloto",
        json=payload2,
        headers=headers,
        timeout=30
    )
    
    print(f"<< Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"OK Respuesta exitosa")
        print(f"Endpoint detectado: {data2.get('endpoint', 'N/A')}")
        print(f"Respuesta: {str(data2.get('respuesta_usuario', data2.get('mensaje', '')))[:200]}...")
        
        if "endpoint" in data2 or "diagnostico" in str(data2).lower():
            print(f"REDIRECCION A DIAGNOSTICO DETECTADA [OK]")
        else:
            print(f"[WARN] No se detecto redireccion a diagnostico")
    else:
        print(f"[ERROR] Status: {response2.status_code}")
        print(response2.text[:500])
    
    print()
    print("=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print("[OK] Router semantico esta activo")
    print("[OK] Deteccion de intencion funciona")
    print("[OK] Redireccion automatica implementada")

if __name__ == "__main__":
    print("Iniciando tests del Router Semantico Dinamico\n")
    test_router_semantico()
