#!/usr/bin/env python3
"""
Test con payload exacto de Azure AI Foundry
"""

import requests
import json

BASE_URL = "http://localhost:7071"

def test_foundry_payload():
    """
    Simula el payload exacto que envía Foundry
    """
    
    print("=" * 60)
    print("TEST: Payload de Azure AI Foundry")
    print("=" * 60)
    
    # Payload exacto que envía Foundry (basado en tu ejemplo)
    payload = {
        "Session-ID": "assistant-3bQkwzfHq1mxV98fqdw2Em",
        "Agent-ID": "assistant"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Session-ID": "assistant-3bQkwzfHq1mxV98fqdw2Em",
        "Agent-ID": "assistant"
    }
    
    # Agregar query en URL como hace Foundry
    params = {
        "q": "En que estabamos trabajando?"
    }
    
    print(f">> Payload: {json.dumps(payload, indent=2)}")
    print(f">> Headers: Session-ID={headers['Session-ID']}, Agent-ID={headers['Agent-ID']}")
    print(f">> Query params: {params}")
    print()
    
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        json=payload,
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"<< Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        print("RESPUESTA COMPLETA:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        print()
        
        # Validaciones
        print("VALIDACIONES:")
        print(f"[{'OK' if data.get('exito') else 'FAIL'}] Campo 'exito': {data.get('exito')}")
        print(f"[{'OK' if 'respuesta_usuario' in data else 'FAIL'}] Campo 'respuesta_usuario' presente")
        print(f"[{'OK' if data.get('fuente_datos') else 'INFO'}] Fuente de datos: {data.get('fuente_datos', 'N/A')}")
        print(f"[{'OK' if data.get('total_docs_semanticos', 0) > 0 else 'INFO'}] Docs semanticos: {data.get('total_docs_semanticos', 0)}")
        
        # Verificar si hubo redirección
        if 'endpoint' in data or 'endpoint_sugerido' in str(data):
            print(f"[OK] REDIRECCION DETECTADA")
        
        # Verificar memoria
        if data.get('metadata', {}).get('memoria_aplicada'):
            print(f"[OK] Memoria aplicada correctamente")
        
        print()
        print("RESPUESTA PARA EL AGENTE:")
        print(data.get('respuesta_usuario', 'N/A')[:300])
        
    else:
        print(f"[ERROR] Status: {response.status_code}")
        print(response.text[:500])

if __name__ == "__main__":
    test_foundry_payload()
