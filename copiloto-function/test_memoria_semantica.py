# -*- coding: utf-8 -*-
"""
Test de memoria semántica integrada
"""
import requests
import json

def test_copiloto_memoria_semantica():
    """Prueba la integración de memoria semántica en /api/copiloto"""
    
    base_url = "http://localhost:7071"  # Local
    # base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"  # Azure
    
    headers = {
        "Content-Type": "application/json",
        "Session-ID": "test-session-semantica",
        "Agent-ID": "Agent898"
    }
    
    print("Probando memoria semantica integrada...")
    
    # Test 1: Panel inicial con contexto semantico
    print("\n1. Test: Panel inicial")
    response = requests.get(f"{base_url}/api/copiloto", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Panel inicial: {data.get('version', 'N/A')}")
        print(f"Contexto semantico: {'Si' if data.get('contexto_semantico') else 'No'}")
        print(f"Inteligencia activa: {data.get('estado', {}).get('inteligencia', {}).get('memoria_semantica_activa', False)}")
    else:
        print(f"ERROR: {response.status_code}")
    
    # Test 2: Comando diagnosticar con contexto
    print("\n2. Test: Comando diagnosticar enriquecido")
    payload = {"mensaje": "diagnosticar:sistema"}
    response = requests.get(f"{base_url}/api/copiloto", headers=headers, params=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Diagnostico: {data.get('accion', 'N/A')}")
        print(f"Evaluacion cognitiva: {'Si' if data.get('resultado', {}).get('evaluacion_cognitiva') else 'No'}")
    else:
        print(f"ERROR: {response.status_code}")
    
    # Test 3: Comando sugerir con contexto
    print("\n3. Test: Sugerencias contextuales")
    payload = {"mensaje": "sugerir"}
    response = requests.get(f"{base_url}/api/copiloto", headers=headers, params=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK Sugerencias: {data.get('accion', 'N/A')}")
        sugerencias = data.get('resultado', {}).get('sugerencias_contextuales', [])
        print(f"Sugerencias contextuales: {len(sugerencias)} encontradas")
        for i, sug in enumerate(sugerencias[:3], 1):
            print(f"   {i}. {sug}")
    else:
        print(f"ERROR: {response.status_code}")
    
    print("\nPruebas completadas")

if __name__ == "__main__":
    test_copiloto_memoria_semantica()