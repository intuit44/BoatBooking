#!/usr/bin/env python3
"""Test simple v2 con captura completa de logs"""
import sys
import os
import json
import logging

# Configurar logging para capturar TODO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout
)

sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables
try:
    settings_path = os.path.join(os.path.dirname(__file__), 'local.settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = value
except Exception as e:
    pass

import azure.functions as func

print("\n" + "=" * 80)
print("TEST SIMPLE V2: diagnostico-recursos con logs completos")
print("=" * 80)

# Importar endpoint
print("\n[1] Importando endpoint...")
from endpoints.diagnostico_recursos import diagnostico_recursos_http

# Crear request
print("\n[2] Creando request POST con recurso...")
body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
req = func.HttpRequest(
    method="POST",
    url="http://localhost:7071/api/diagnostico-recursos",
    headers={"Session-ID": "test_v2_123", "Agent-ID": "TestAgentV2"},
    params={},
    body=body_data.encode('utf-8')
)

# Ejecutar
print("\n[3] Ejecutando endpoint...")
print("=" * 80)
try:
    response = diagnostico_recursos_http(req)
    print("=" * 80)
    
    if response is None:
        print("\n[FAIL] Response es None")
        sys.exit(1)
    
    print("\n[OK] Response recibido")
    print(f"   Status: {response.status_code}")
    
    body = response.get_body().decode()
    data = json.loads(body)
    
    print(f"   OK: {data.get('ok')}")
    print(f"   Recurso: {data.get('recurso')}")
    print(f"   Memoria aplicada: {data.get('metadata', {}).get('memoria_aplicada')}")
    
    sys.exit(0)
    
except Exception as e:
    print("=" * 80)
    print(f"\n[FAIL] Excepcion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
