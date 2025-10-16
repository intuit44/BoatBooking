#!/usr/bin/env python3
"""
Test para debuggear exactamente qué está pasando con Foundry
"""

import requests
import json

def test_foundry_real():
    """Simula exactamente lo que hace Foundry"""
    
    # URL del endpoint que Foundry está llamando
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/revisar-correcciones"
    
    # Parámetros que Foundry envía
    params = {
        "consulta": "cuales fueron las ultimas 10 interacciones que hice"
    }
    
    print("=== TEST FOUNDRY REAL ===")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Verificar si hay headers de redirección
        if "X-Redirigido-Desde" in response.headers:
            print("✅ REDIRECCIÓN DETECTADA")
            print(f"Desde: {response.headers['X-Redirigido-Desde']}")
        else:
            print("❌ NO HAY REDIRECCIÓN")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            
            # Verificar si hay metadata de redirección
            if "_redireccion" in data:
                print("✅ METADATA DE REDIRECCIÓN ENCONTRADA")
            else:
                print("❌ SIN METADATA DE REDIRECCIÓN")
                
        except:
            print(f"Raw response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_foundry_real()