#!/usr/bin/env python3
"""Test simple del endpoint diagnostico-recursos"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno
try:
    settings_path = os.path.join(os.path.dirname(__file__), 'local.settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = value
        print("[INFO] Variables cargadas\n")
except Exception as e:
    print(f"[WARN] {e}\n")

import azure.functions as func
from endpoints.diagnostico_recursos import diagnostico_recursos_http

def test_simple():
    print("=" * 80)
    print("TEST SIMPLE: diagnostico-recursos")
    print("=" * 80)
    
    # Test 1: POST con recurso
    print("\n[1] POST con recurso...")
    body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
    req = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/diagnostico-recursos",
        headers={"Session-ID": "test123", "Agent-ID": "TestAgent"},
        params={},
        body=body_data.encode('utf-8')
    )
    
    try:
        response = diagnostico_recursos_http(req)
        if response is None:
            print("   [FAIL] Response es None")
            print("   Verificando imports...")
            try:
                from function_app import _json
                print("   [OK] _json importado correctamente")
            except Exception as e:
                print(f"   [FAIL] Error importando _json: {e}")
            return False
        
        print(f"   [OK] Status: {response.status_code}")
        data = json.loads(response.get_body().decode())
        print(f"   [OK] Response OK: {data.get('ok')}")
        print(f"   [OK] Metadata: {data.get('metadata', {}).get('memoria_aplicada')}")
        return True
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)
