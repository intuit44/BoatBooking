#!/usr/bin/env python3
import requests
import json

def test_semantic_script():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar-script"
    
    # Test 1: Semantic payload (like agent sent)
    payload1 = {
        "session_id": "test_semantic",
        "intencion": "leer_archivo", 
        "parametros": {
            "ruta": "verificacion/memoria_test.txt"
        }
    }
    
    print("Test 1: Semantic payload (non-executable file)")
    resp1 = requests.post(url, json=payload1, timeout=30)
    print(f"Status: {resp1.status_code}")
    print(f"Response: {resp1.json()}")
    
    # Test 2: Direct script execution
    payload2 = {
        "session_id": "test_direct",
        "script": "scripts/test.py"
    }
    
    print("\nTest 2: Direct script execution")
    resp2 = requests.post(url, json=payload2, timeout=30)
    print(f"Status: {resp2.status_code}")
    print(f"Response: {resp2.json()}")
    
    # Test 3: Semantic with executable script
    payload3 = {
        "session_id": "test_semantic_exec",
        "intencion": "ejecutar",
        "parametros": {
            "ruta": "scripts/test.py"
        }
    }
    
    print("\nTest 3: Semantic with executable script")
    resp3 = requests.post(url, json=payload3, timeout=30)
    print(f"Status: {resp3.status_code}")
    print(f"Response: {resp3.json()}")

if __name__ == "__main__":
    test_semantic_script()