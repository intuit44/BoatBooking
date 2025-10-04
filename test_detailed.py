#!/usr/bin/env python3
import requests
import json

def test_detailed():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/leer-archivo"
    params = {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
    
    print("[TEST] Probando con detalles completos")
    
    response = requests.get(url, params=params, timeout=30)
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"[KEYS] {list(data.keys())}")
            
            # Verificar si es mi estructura nueva
            if 'exito' in data:
                print(f"[NEW] Estructura nueva detectada!")
                print(f"[EXITO] {data.get('exito')}")
                print(f"[ORIGEN] {data.get('origen')}")
                if 'contenido' in data:
                    print(f"[CONTENT] {len(data['contenido'])} chars")
                    print(f"[PREVIEW] {data['contenido'][:50]}...")
            else:
                print(f"[OLD] Estructura antigua")
                print(f"[OK] {data.get('ok')}")
                print(f"[MESSAGE] {data.get('message', '')[:100]}...")
                
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print(f"[ERROR] HTTP {response.status_code}")

if __name__ == "__main__":
    test_detailed()