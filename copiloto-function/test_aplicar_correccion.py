#!/usr/bin/env python3
"""
Test básico para validar /api/aplicar-correccion-manual
"""
import requests
import json

BASE_URL = "http://localhost:7071"  # Local
# BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"  # Azure

def test_cosmos_db_correction():
    """Test corrección Cosmos DB"""
    payload = {
        "timeout": 30,
        "database": "cosmos-db"
    }
    
    response = requests.post(f"{BASE_URL}/api/aplicar-correccion-manual", json=payload)
    print(f"✅ Cosmos DB Test: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_cli_correction():
    """Test corrección CLI"""
    payload = {
        "comando": "az storage account list"
    }
    
    response = requests.post(f"{BASE_URL}/api/aplicar-correccion-manual", json=payload)
    print(f"✅ CLI Test: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_config_correction():
    """Test corrección configuración"""
    payload = {
        "ruta": "app.json",
        "configuracion": {
            "timeout": 30
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/aplicar-correccion-manual", json=payload)
    print(f"✅ Config Test: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_generic_correction():
    """Test corrección genérica"""
    payload = {
        "custom_field": "test_value",
        "another_field": 123
    }
    
    response = requests.post(f"{BASE_URL}/api/aplicar-correccion-manual", json=payload)
    print(f"✅ Generic Test: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    print("🧪 Testing /api/aplicar-correccion-manual")
    
    tests = [
        test_cosmos_db_correction,
        test_cli_correction, 
        test_config_correction,
        test_generic_correction
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Results: {passed}/{total} tests passed")