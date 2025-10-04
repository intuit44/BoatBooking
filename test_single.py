#!/usr/bin/env python3
"""
Prueba individual para diagnosticar el problema
"""
import requests
import json

def test_single():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/leer-archivo"
    params = {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
    
    print("[TEST] Probando endpoint leer-archivo")
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
    print(f"[CONTENT_TYPE] {response.headers.get('Content-Type', 'N/A')}")
    print(f"[CONTENT_LEN] {response.headers.get('Content-Length', 'N/A')}")
    
    try:
        data = response.json()
        print(f"[JSON_KEYS] {list(data.keys())}")
        print(f"[EXITO] {data.get('exito', 'N/A')}")
        if 'error' in data:
            print(f"[ERROR] {data['error']}")
        if 'contenido' in data:
            print(f"[CONTENT_LEN] {len(data['contenido'])}")
        if 'origen' in data:
            print(f"[ORIGEN] {data['origen']}")
    except Exception as e:
        print(f"[PARSE_ERROR] {e}")
        print(f"[TEXT_LEN] {len(response.text)}")

if __name__ == "__main__":
    test_single()