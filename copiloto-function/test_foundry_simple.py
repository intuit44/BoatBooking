#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

try:
    with open('local.settings.json', 'r') as f:
        for k, v in json.load(f).get('Values', {}).items():
            if k not in os.environ: os.environ[k] = v
except: pass

import azure.functions as func
from function_app import app

print("\n" + "="*80)
print("TEST: Simulacion Foundry - Memoria Completa")
print("="*80)

# TEST 1: historial-interacciones
print("\n[1] historial-interacciones")
func_obj = [f for f in app.get_functions() if f.get_function_name() == "historial_interacciones"][0]

req = func.HttpRequest(
    method="GET",
    url="http://localhost:7071/api/historial-interacciones",
    headers={"Session-ID": "assistant", "Agent-ID": "assistant"},
    params={}, body=b""
)

resp = func_obj.get_user_function()(req)
data = json.loads(resp.get_body().decode())

print(f"Status: {resp.status_code}")
print(f"Exito: {data.get('exito')}")
print(f"Total: {data.get('total')}")
print(f"Tiene respuesta_usuario: {'respuesta_usuario' in data}")

if 'respuesta_usuario' in data:
    print(f"Longitud respuesta: {len(data['respuesta_usuario'])}")

meta = data.get('metadata', {})
print(f"Memoria aplicada: {meta.get('memoria_aplicada')}")
print(f"Interacciones previas: {meta.get('interacciones_previas')}")
print(f"Docs vectoriales: {meta.get('docs_vectoriales')}")

# TEST 2: memoria-global
print("\n[2] memoria-global")
func_obj2 = [f for f in app.get_functions() if f.get_function_name() == "memoria_global"][0]

req2 = func.HttpRequest(
    method="GET",
    url="http://localhost:7071/api/memoria-global",
    headers={}, params={"limite": "3"}, body=b""
)

resp2 = func_obj2.get_user_function()(req2)
data2 = json.loads(resp2.get_body().decode())

print(f"Status: {resp2.status_code}")
print(f"Total interacciones: {data2.get('resumen', {}).get('total_interacciones')}")

print("\nAnalisis texto_semantico:")
for i, inter in enumerate(data2.get('interacciones', [])[:3], 1):
    texto = inter.get('texto_semantico', '')
    es_generico = "Interaccion en" in texto and len(texto) < 100
    print(f"  [{i}] Longitud: {len(texto)}, Tipo: {'GENERICO' if es_generico else 'RICO'}")
    print(f"      Preview: {texto[:100]}")

# TEST 3: Guardar y recuperar
print("\n[3] Test generador semantico")
from services.memory_service import memory_service

test_data = {
    "exito": True,
    "mensaje": "Test del generador semantico enriquecido",
    "interpretacion_semantica": "Validacion de construccion de texto rico",
    "total": 5,
    "documentos_relevantes": 10
}

result = memory_service.registrar_llamada(
    source="test", endpoint="/api/test", method="POST",
    params={"session_id": "test_session", "agent_id": "test_agent"},
    response_data=test_data, success=True
)

print(f"Guardado: {'OK' if result else 'FALLO'}")

hist = memory_service.get_session_history("test_session", limit=1)
if hist:
    texto = hist[0].get('texto_semantico', '')
    print(f"Recuperado: {len(texto)} chars")
    print(f"Contenido: {texto[:200]}")
    print(f"Es rico: {'SI' if len(texto) > 100 else 'NO'}")

print("\n" + "="*80)
