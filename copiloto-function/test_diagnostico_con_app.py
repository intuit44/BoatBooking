#!/usr/bin/env python3
"""Test usando la instancia app para invocar el endpoint correctamente"""
import sys
import os
import json
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
except Exception:
    pass

import azure.functions as func
from function_app import app

print("\n" + "=" * 80)
print("TEST: diagnostico-recursos usando app.get_functions()")
print("=" * 80)

# Obtener la función registrada en app
print("\n[1] Obteniendo funciones registradas en app...")
functions = app.get_functions()
print(f"   Total funciones: {len(functions)}")

# Buscar diagnostico_recursos_http
func_obj = None
for f in functions:
    if f.get_function_name() == "diagnostico_recursos_http":
        func_obj = f
        break

if not func_obj:
    print("   [FAIL] Función no encontrada")
    print(f"   Disponibles: {[f.get_function_name() for f in functions[:5]]}")
    sys.exit(1)

print(f"   [OK] Función encontrada: {func_obj.get_function_name()}")

# Crear request
print("\n[2] Creando request POST...")
body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
req = func.HttpRequest(
    method="POST",
    url="http://localhost:7071/api/diagnostico-recursos",
    headers={"Session-ID": "test_app_123", "Agent-ID": "TestAppAgent"},
    params={},
    body=body_data.encode('utf-8')
)

# Invocar función a través del objeto registrado
print("\n[3] Invocando función a través de app...")
try:
    response = func_obj.get_user_function()(req)
    
    if response is None:
        print("   [FAIL] Response es None")
        sys.exit(1)
    
    print(f"   [OK] Status: {response.status_code}")
    
    data = json.loads(response.get_body().decode())
    print(f"   [OK] Response OK: {data.get('ok')}")
    print(f"   [OK] Recurso: {data.get('recurso')}")
    print(f"   [OK] Memoria aplicada: {data.get('metadata', {}).get('memoria_aplicada')}")
    
    print("\n[SUCCESS] Test completado correctamente")
    sys.exit(0)
    
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
