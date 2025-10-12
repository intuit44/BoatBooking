#!/usr/bin/env python3
"""
Test post-deploy para validar memoria en endpoints críticos
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"
SESSION_ID = f"postdeploy_{int(time.time())}"

def test_endpoint_memory(endpoint, method="POST", payload=None):
    """Test individual endpoint con memoria"""
    url = f"{BASE_URL}/api/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": SESSION_ID,
        "X-Agent-ID": "PostDeployAgent"
    }
    
    if payload is None:
        payload = {"session_id": SESSION_ID}
    else:
        payload["session_id"] = SESSION_ID
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=payload, timeout=30)
        else:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        data = resp.json()
        metadata = data.get("metadata", {})
        
        return {
            "endpoint": endpoint,
            "status": resp.status_code,
            "memoria_disponible": metadata.get("memoria_disponible", False),
            "wrapper_aplicado": metadata.get("wrapper_aplicado", False),
            "session_detectado": metadata.get("session_info", {}).get("session_id") == SESSION_ID,
            "timestamp": metadata.get("timestamp"),
            "error": None
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": 0,
            "memoria_disponible": False,
            "wrapper_aplicado": False,
            "session_detectado": False,
            "error": str(e)
        }

def test_session_persistence():
    """Test persistencia de sesión con llamadas consecutivas"""
    print(f"\n=== TEST PERSISTENCIA SESIÓN: {SESSION_ID} ===")
    
    # Primera llamada
    result1 = test_endpoint_memory("ejecutar-cli", payload={"comando": "echo test1"})
    time.sleep(1)
    
    # Segunda llamada con mismo session_id
    result2 = test_endpoint_memory("ejecutar-cli", payload={"comando": "echo test2"})
    
    print(f"Llamada 1 - Session detectado: {result1['session_detectado']}")
    print(f"Llamada 2 - Session detectado: {result2['session_detectado']}")
    print(f"Persistencia: {'OK' if result1['session_detectado'] and result2['session_detectado'] else 'FAIL'}")
    
    return result1['session_detectado'] and result2['session_detectado']

def main():
    print(f"TEST MEMORIA POST-DEPLOY")
    print(f"URL: {BASE_URL}")
    print(f"Session ID: {SESSION_ID}")
    print("=" * 60)
    
    # Endpoints críticos a validar
    critical_endpoints = [
        ("ejecutar-cli", "POST", {"comando": "echo memoria test"}),
        ("ejecutar", "POST", {"intencion": "dashboard"}),
        ("hybrid", "POST", {"agent_response": "ping"}),
        ("status", "GET", {}),
        ("consultar-memoria", "GET", {}),
        ("bing-grounding", "POST", {"query": "test memoria"}),
        ("bateria-endpoints", "GET", {}),
        ("auditar-deploy", "GET", {}),
    ]
    
    results = []
    memory_failures = []
    
    for endpoint, method, payload in critical_endpoints:
        print(f"\nTesting {endpoint}...")
        result = test_endpoint_memory(endpoint, method, payload)
        results.append(result)
        
        if result["status"] == 200:
            if result["memoria_disponible"] and result["wrapper_aplicado"]:
                print(f"  OK Memoria OK - Session: {'OK' if result['session_detectado'] else 'FAIL'}")
            else:
                print(f"  FAIL Memoria FALLA")
                memory_failures.append(endpoint)
        else:
            print(f"  FAIL HTTP {result['status']} - {result.get('error', 'Unknown error')}")
            memory_failures.append(endpoint)
    
    # Test persistencia
    persistence_ok = test_session_persistence()
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN POST-DEPLOY")
    print(f"{'='*60}")
    
    total_endpoints = len(results)
    successful = sum(1 for r in results if r["status"] == 200 and r["memoria_disponible"])
    
    print(f"Endpoints probados: {total_endpoints}")
    print(f"Memoria funcionando: {successful}/{total_endpoints}")
    print(f"Persistencia de sesión: {'OK' if persistence_ok else 'FAIL'}")
    
    if memory_failures:
        print(f"\nFALLOS DE MEMORIA:")
        for endpoint in memory_failures:
            print(f"  - /api/{endpoint}")
    else:
        print(f"\nTODOS LOS ENDPOINTS CON MEMORIA OK")
    
    # Generar alerta si hay fallos
    if memory_failures or not persistence_ok:
        print(f"\nALERTA: Sistema de memoria tiene problemas")
        print(f"   Revisar Application Insights para metadata.memoria_disponible == false")
        return False
    else:
        print(f"\nSISTEMA DE MEMORIA COMPLETAMENTE OPERATIVO")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)