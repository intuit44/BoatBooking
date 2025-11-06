#!/usr/bin/env python3
"""Test de debugging detallado para diagnostico-recursos"""
import sys
import os
import json
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

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

def test_debug():
    print("=" * 80)
    print("TEST DEBUG: diagnostico-recursos")
    print("=" * 80)
    
    # Test 1: Importar el endpoint
    print("\n[1] Importando endpoint...")
    try:
        from endpoints.diagnostico_recursos import diagnostico_recursos_http
        print("   [OK] Endpoint importado")
    except Exception as e:
        print(f"   [FAIL] Error importando: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Crear request
    print("\n[2] Creando request...")
    body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
    req = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/diagnostico-recursos",
        headers={"Session-ID": "test123", "Agent-ID": "TestAgent"},
        params={},
        body=body_data.encode('utf-8')
    )
    print("   [OK] Request creado")
    
    # Test 3: Ejecutar endpoint con try-except detallado
    print("\n[3] Ejecutando endpoint...")
    try:
        response = diagnostico_recursos_http(req)
        
        if response is None:
            print("   [FAIL] Response es None - el endpoint no devolvio nada")
            print("   Esto indica que hubo una excepcion no capturada")
            return False
        
        print(f"   [OK] Response recibido: {type(response)}")
        print(f"   [OK] Status code: {response.status_code}")
        
        body = response.get_body().decode()
        print(f"   [OK] Body length: {len(body)}")
        
        data = json.loads(body)
        print(f"   [OK] JSON parseado: ok={data.get('ok')}")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] Excepcion capturada: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_debug()
    sys.exit(0 if success else 1)
