#!/usr/bin/env python3
"""
Prueba del nuevo endpoint test-dual
"""
import requests
import json

def test_dual_endpoint():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/test-dual"
    params = {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
    
    print(f"[TEST] Probando endpoint test-dual")
    print(f"[PARAMS] ruta={params['ruta']}")
    
    response = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": "azure-agents",
            "Accept": "application/json"
        },
        timeout=30
    )
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"[RESULT] test_dual: {data.get('test_dual')}")
            print(f"[RESULT] local_exists: {data.get('local_exists')}")
            print(f"[RESULT] blob_available: {data.get('blob_available')}")
            print(f"[RESULT] blob_result: {data.get('blob_result')}")
            print(f"[RESULT] run_id: {data.get('run_id')}")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(f"[TEXT] {response.text[:200]}")

if __name__ == "__main__":
    test_dual_endpoint()