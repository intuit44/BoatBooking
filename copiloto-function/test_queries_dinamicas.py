"""Test de queries dinamicas - Version simplificada sin emojis"""
import requests
import json

BASE_URL = "http://localhost:7071/api/historial-interacciones"

print("\n" + "="*80)
print("TEST 1: Llamada basica")
print("="*80)

response = requests.get(
    BASE_URL,
    params={"Session-ID": "assistant", "Agent-ID": "assistant"},
    headers={"Session-ID": "assistant", "Agent-ID": "assistant"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total: {data.get('total', 0)}")
    print(f"Interacciones: {len(data.get('interacciones', []))}")
    print(f"Query dinamica: {data.get('query_dinamica_aplicada', False)}")

print("\n" + "="*80)
print("TEST 2: Con filtros (tipo + contiene)")
print("="*80)

response = requests.get(
    BASE_URL,
    params={
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "tipo": "interaccion_usuario",
        "contiene": "copiloto",
        "limite": 5
    },
    headers={"Session-ID": "assistant", "Agent-ID": "assistant"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Query dinamica aplicada: {data.get('query_dinamica_aplicada', False)}")
    print(f"Total encontrado: {data.get('total', 0)}")
    print(f"Filtros: {json.dumps(data.get('filtros_aplicados', {}), indent=2)}")

print("\n" + "="*80)
print("TEST 3: Filtro temporal")
print("="*80)

response = requests.get(
    BASE_URL,
    params={
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "fecha_inicio": "ultimas 24h",
        "limite": 10
    },
    headers={"Session-ID": "assistant", "Agent-ID": "assistant"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Query dinamica: {data.get('query_dinamica_aplicada', False)}")
    print(f"Total: {data.get('total', 0)}")
    metadata = data.get('metadata', {})
    if 'query_sql' in metadata:
        print(f"SQL: {metadata['query_sql']}")

print("\n" + "="*80)
print("TEST 4: Filtro por endpoint")
print("="*80)

response = requests.get(
    BASE_URL,
    params={
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "endpoint": "/api/copiloto",
        "limite": 5
    },
    headers={"Session-ID": "assistant", "Agent-ID": "assistant"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Query dinamica: {data.get('query_dinamica_aplicada', False)}")
    print(f"Total: {data.get('total', 0)}")
    if data.get('interacciones'):
        print("Endpoints encontrados:")
        for inter in data['interacciones']:
            print(f"  - {inter.get('endpoint')}")

print("\n" + "="*80)
print("TESTS COMPLETADOS")
print("="*80)
