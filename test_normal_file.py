#!/usr/bin/env python3
import requests
import json

def test_normal_file():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/leer-archivo"
    params = {"ruta": "boat-rental-project/README.md"}
    
    print("[TEST] Probando archivo normal (no especial)")
    
    response = requests.get(url, params=params, timeout=30)
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"[KEYS] {list(data.keys())}")
            
            if 'exito' in data:
                print(f"[NEW] Mi codigo funciona!")
                print(f"[EXITO] {data.get('exito')}")
                print(f"[ORIGEN] {data.get('origen')}")
            else:
                print(f"[OLD] Codigo anterior")
                
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print(f"[ERROR] HTTP {response.status_code}")

if __name__ == "__main__":
    test_normal_file()