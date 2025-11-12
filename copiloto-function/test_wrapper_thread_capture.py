"""
Test: Simula el flujo REAL del wrapper con captura automática de Thread-ID
Valida que el wrapper integrado capture threads cuando Foundry no los envía
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import Mock, patch
import json

print("=" * 60)
print("TEST: Wrapper Real - Captura Automática de Thread-ID")
print("=" * 60)

# Simular payload de Foundry sin thread_id (caso real)
payload_foundry = {
    "input": "Consulta el estado del sistema",
    "function": {
        "name": "CopilotoFunctionApp_getStatus",
        "arguments": "{}"
    }
}

print("\n[1/5] Payload de Foundry (SIN thread_id en headers/body):")
print(json.dumps(payload_foundry, indent=2))

# Simular request HTTP completo
print("\n[2/5] Creando mock request HTTP...")
mock_req = Mock()
mock_req.headers = {}  # Sin Session-ID ni Thread-ID
mock_req.params = {}   # Sin query params
mock_req.method = "POST"
mock_req.get_json = Mock(return_value=payload_foundry)

print("   Headers: {}")
print("   Params: {}")
print("   Body: input='Consulta el estado del sistema'")

# Test: Extraer session info (simula Bloque 0 y 1 del wrapper)
print("\n[3/5] Ejecutando extraer_session_info() (lógica del wrapper)...")

from memory_helpers import extraer_session_info

# Mock de la API de Foundry para que devuelva un thread
with patch('foundry_thread_extractor.obtener_thread_desde_foundry') as mock_foundry_api:
    # Simular que Foundry API devuelve un thread
    mock_foundry_api.return_value = "thread_MOCK_TEST_12345"
    
    session_info = extraer_session_info(mock_req)
    
    print(f"   Session ID capturado: {session_info.get('session_id')}")
    print(f"   Agent ID capturado: {session_info.get('agent_id')}")
    print(f"   Foundry API llamada: {mock_foundry_api.called}")

# Validar resultado
print("\n[4/5] Validando captura...")
session_id = session_info.get('session_id')
agent_id = session_info.get('agent_id')

if session_id and session_id.startswith('thread_'):
    print(f"   [OK] Thread capturado: {session_id}")
    print(f"   [OK] Formato válido: thread_*")
elif session_id == "fallback_session":
    print(f"   [!] Usando fallback (API no disponible)")
else:
    print(f"   [X] Thread no capturado correctamente: {session_id}")

# Simular guardado en Cosmos (Bloque 0 del wrapper)
print("\n[5/5] Simulando guardado en Cosmos...")
evento_simulado = {
    "id": f"{session_id}_user_input_test",
    "session_id": session_id,
    "agent_id": agent_id or "foundry_user",
    "endpoint": "status",
    "event_type": "user_input",
    "texto_semantico": payload_foundry["input"],
    "tipo": "user_input"
}

print(f"   Documento a guardar:")
print(f"   - ID: {evento_simulado['id']}")
print(f"   - Session ID: {evento_simulado['session_id']}")
print(f"   - Agent ID: {evento_simulado['agent_id']}")
print(f"   - Texto: {evento_simulado['texto_semantico'][:50]}...")

print("\n" + "=" * 60)
print("RESULTADO FINAL:")
print("=" * 60)

if session_id and session_id.startswith('thread_'):
    print("[OK] EXITO: Wrapper captura thread automáticamente")
    print(f"   Thread ID: {session_id}")
    print(f"   Estrategia: API Foundry (fallback automático)")
    print("\n[i] En producción:")
    print("   1. Request llega sin Session-ID")
    print("   2. Wrapper llama extraer_session_info()")
    print("   3. extraer_session_info() consulta Foundry API")
    print("   4. Thread capturado se usa en Cosmos")
    print("   5. Documento guardado con session_id correcto")
else:
    print("[!] Thread no capturado, usando fallback")
    print(f"   Session ID: {session_id or 'fallback_session'}")
    print("\n[i] Posibles causas:")
    print("   - Credenciales MSI no configuradas")
    print("   - Foundry API no accesible")
    print("   - No hay threads activos")

print("\n[i] NOTA: Este test simula el flujo REAL del wrapper")
print("   memory_route_wrapper.py ahora integra esta lógica en:")
print("   - Bloque 0: Captura input usuario")
print("   - Bloque 1: Consulta memoria")
print("   - Bloque 4: Snapshot cognitivo")
print("   - Bloque 6: Captura respuesta Foundry")
