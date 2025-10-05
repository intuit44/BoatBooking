#!/usr/bin/env python3
"""
Prueba específica para ejecutar-cli con JSON correcto
"""
import requests
import json

def test_cli_simple():
    """Prueba comando simple"""
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar-cli"
    
    # Comando simple que debería funcionar
    payload = {
        "comando": "echo 'Hello from Azure Functions'"
    }
    
    print("[TEST] Probando comando simple...")
    print(f"[PAYLOAD] {json.dumps(payload)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[STATUS] {response.status_code}")
        print(f"[RESPONSE] {response.text}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

def test_cli_python():
    """Prueba comando Python"""
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar-cli"
    
    # Comando Python simple
    payload = {
        "comando": "python3 -c \"print('Python funcionando')\""
    }
    
    print("\n[TEST] Probando comando Python...")
    print(f"[PAYLOAD] {json.dumps(payload)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[STATUS] {response.status_code}")
        print(f"[RESPONSE] {response.text}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

def test_cli_modules():
    """Prueba importación de módulos"""
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar-cli"
    
    # Verificar módulos disponibles
    payload = {
        "comando": "python3 -c \"import sys; print('Python version:', sys.version)\""
    }
    
    print("\n[TEST] Probando versión Python...")
    print(f"[PAYLOAD] {json.dumps(payload)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('exito'):
                output = data.get('output', {})
                print(f"[SUCCESS] {output.get('raw')}")
                print(f"[TYPE] {output.get('type')}")
            else:
                print(f"[FAILED] {data.get('error')}")
        else:
            print(f"[HTTP_ERROR] {response.text}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    test_cli_simple()
    test_cli_python()
    test_cli_modules()