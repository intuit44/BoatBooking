#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar wrapper de memoria
"""

import requests
import json

def test_wrapper():
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("DIAGNOSTICO DEL WRAPPER DE MEMORIA")
    print("=" * 50)
    
    # Test con session_id explícito
    print("\n1. Test con session_id explícito...")
    
    try:
        response = requests.get(
            f"{base_url}/api/status",
            params={
                "session_id": "test_123",
                "agent_id": "TestAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            
            # Verificar metadata
            if "metadata" in data:
                metadata = data["metadata"]
                print(f"Metadata keys: {list(metadata.keys())}")
                
                if "session_info" in metadata:
                    session_info = metadata["session_info"]
                    print(f"Session ID: {session_info.get('session_id')}")
                    print(f"Agent ID: {session_info.get('agent_id')}")
                    print("WRAPPER DETECTADO!")
                else:
                    print("NO session_info en metadata")
                
                if metadata.get("wrapper_aplicado"):
                    print("wrapper_aplicado: True")
                else:
                    print("wrapper_aplicado: False o ausente")
                    
                if metadata.get("memoria_disponible"):
                    print("memoria_disponible: True")
                else:
                    print("memoria_disponible: False o ausente")
            else:
                print("NO metadata en respuesta")
                print(f"Response keys: {list(data.keys())}")
        else:
            print(f"Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTICO COMPLETADO")

if __name__ == "__main__":
    test_wrapper()