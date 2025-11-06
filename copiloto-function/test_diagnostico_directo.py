#!/usr/bin/env python3
"""Test directo sin decoradores"""
import sys
import os
import json
import logging
logging.basicConfig(level=logging.INFO)

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
from datetime import datetime

def test_directo():
    print("\n" + "=" * 80)
    print("TEST DIRECTO: Lógica del endpoint sin decoradores")
    print("=" * 80)
    
    # Imports necesarios
    from function_app import IS_AZURE, MGMT_SDK, STORAGE_CONNECTION_STRING, CACHE
    from services.memory_service import memory_service
    from memory_manual import aplicar_memoria_manual
    from cosmos_memory_direct import aplicar_memoria_cosmos_directo
    from function_app import _json, _s
    
    # Crear request
    body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
    req = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/diagnostico-recursos",
        headers={"Session-ID": "test123", "Agent-ID": "TestAgent"},
        params={},
        body=body_data.encode('utf-8')
    )
    
    # Parsear body
    body = json.loads(req.get_body().decode('utf-8'))
    rid = _s(body.get("recurso"))
    profundidad = _s(body.get("profundidad") or "basico")
    
    print(f"\n[1] Recurso: {rid}, Profundidad: {profundidad}")
    
    # Crear resultado
    result = {
        "ok": True,
        "recurso": rid,
        "profundidad": profundidad,
        "timestamp": datetime.now().isoformat(),
        "diagnostico": {
            "estado": "completado",
            "tipo": "recurso_especifico"
        }
    }
    
    print(f"[2] Resultado base creado: {result.get('ok')}")
    
    # Aplicar memoria
    result = aplicar_memoria_cosmos_directo(req, result)
    result = aplicar_memoria_manual(req, result)
    
    print(f"[3] Memoria aplicada: {result.get('metadata', {}).get('memoria_aplicada')}")
    
    # Registrar llamada
    try:
        memory_service.registrar_llamada(
            source="diagnostico_recursos",
            endpoint="/api/diagnostico-recursos",
            method=req.method,
            params={"session_id": req.headers.get("Session-ID"), "recurso": rid},
            response_data=result,
            success=result.get("ok", False)
        )
        print("[4] Llamada registrada en memoria")
    except Exception as e:
        print(f"[4] Error registrando: {e}")
    
    # Convertir a response
    response = _json(result)
    
    print(f"[5] Response generado: {type(response)}")
    print(f"[6] Status code: {response.status_code}")
    
    # Parsear respuesta
    response_data = json.loads(response.get_body().decode())
    print(f"\n[RESULTADO]")
    print(f"  OK: {response_data.get('ok')}")
    print(f"  Recurso: {response_data.get('recurso')}")
    print(f"  Memoria aplicada: {response_data.get('metadata', {}).get('memoria_aplicada')}")
    print(f"  Session ID: {response_data.get('metadata', {}).get('session_info', {}).get('session_id')}")
    
    return response_data.get('ok') and response_data.get('metadata', {}).get('memoria_aplicada')

if __name__ == "__main__":
    try:
        success = test_directo()
        print(f"\n{'[SUCCESS]' if success else '[PARTIAL]'} Test completado")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
