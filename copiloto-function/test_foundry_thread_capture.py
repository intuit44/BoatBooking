"""
Test: Captura automática de Thread-ID cuando Foundry NO lo envía
Simula payload real de Foundry sin thread_id y valida captura desde API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from foundry_thread_extractor import extraer_thread_de_contexto, obtener_thread_desde_foundry
from memory_helpers import extraer_session_info
from unittest.mock import Mock
import json

print("=" * 60)
print("TEST: Captura Automática de Thread-ID desde Foundry")
print("=" * 60)

# Simular payload real de Foundry SIN thread_id
payload_foundry = {
    "id": "call_TZmYgiyhuJFX3DUqNVNnvkSt",
    "type": "openapi",
    "function": {
        "name": "CopilotoFunctionApp_getStatus",
        "arguments": "{}",
        "output": "{'exito': True, 'estado': {'copiloto': 'activo'}}"
    }
}

print("\n[1/4] Payload de Foundry (SIN thread_id):")
print(json.dumps(payload_foundry, indent=2))

# Test 1: Intentar extraer de contexto (debe fallar)
print("\n[2/4] Intentando extraer thread del payload...")
thread_from_payload = extraer_thread_de_contexto(payload_foundry)
if thread_from_payload:
    print(f"[X] INESPERADO: Encontro thread en payload: {thread_from_payload}")
else:
    print("[OK] Correcto: No hay thread en el payload")

# Test 2: Simular request completo (sin llamar API)
print("\n[3/4] Simulando request HTTP completo...")
mock_req = Mock()
mock_req.headers = {}  # Sin headers
mock_req.params = {}   # Sin query params
mock_req.get_json = Mock(return_value=payload_foundry)

session_info = extraer_session_info(mock_req, skip_api_call=True)
print(f"Session ID extraido: {session_info.get('session_id')}")
print(f"Agent ID extraido: {session_info.get('agent_id')}")

# Test 3: Captura desde Foundry API (separado)
print("\n[4/4] Intentando capturar thread desde Foundry API...")
print("   (Esto puede tardar unos segundos...)")
try:
    thread_from_api = obtener_thread_desde_foundry()
except Exception as e:
    print(f"   Error: {e}")
    thread_from_api = None

if thread_from_api:
    print(f"[OK] Thread capturado desde Foundry API: {thread_from_api}")
    print(f"   Formato valido: {thread_from_api.startswith('thread_')}")
else:
    print("[!] No se pudo capturar thread desde API")
    print("   Posibles causas:")
    print("   - Credenciales MSI no configuradas")
    print("   - No hay threads activos en Foundry")
    print("   - Endpoint de Foundry no accesible")

print("\n" + "=" * 60)
print("RESULTADO FINAL:")
print("=" * 60)

final_thread = session_info.get('session_id') or thread_from_api
if final_thread and final_thread.startswith('thread_'):
    print(f"[OK] EXITO: Thread capturado automaticamente")
    print(f"   Thread ID: {final_thread}")
    print(f"   Estrategia: {'API Foundry' if not session_info.get('session_id') else 'Payload/Headers'}")
else:
    print(f"[!] Thread no capturado, usando fallback: {final_thread or 'fallback_session'}")
    print("   El sistema seguira funcionando con session_id generico")

print("\n[i] NOTA: En produccion, el wrapper aplicara esto automaticamente")
print("   y guardara en Cosmos con el thread_id correcto.")
