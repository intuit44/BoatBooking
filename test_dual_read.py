#!/usr/bin/env python3
import requests
import json

def test_dual_read():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/dual-read"
    params = {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
    
    print("[TEST] Probando dual-read endpoint")
    
    response = requests.get(url, params=params, timeout=30)
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            print(f"[ORIGEN] {data.get('origen')}")
            print(f"[SIZE] {data.get('size')}")
            if 'contenido' in data:
                print(f"[PREVIEW] {data['contenido'][:100]}...")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print(f"[ERROR] {response.status_code}")

if __name__ == "__main__":
    test_dual_read()