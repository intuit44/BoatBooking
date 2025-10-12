#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final para verificar wrapper de memoria forzado
"""

import requests
import json

def test_wrapper_final():
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("TEST FINAL DEL WRAPPER DE MEMORIA")
    print("=" * 50)
    
    # Test 1: Endpoint status modificado
    print("\n1. Test endpoint /api/status modificado...")
    
    try:
        response = requests.get(
            f"{base_url}/api/status",
            params={
                "session_id": "test_final_123",
                "agent_id": "FinalTestAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            
            if "metadata" in data:
                metadata = data["metadata"]
                print(f"Metadata keys: {list(metadata.keys())}")
                
                if "session_info" in metadata:
                    session_info = metadata["session_info"]
                    print(f"Session ID: {session_info.get('session_id')}")
                    print(f"Agent ID: {session_info.get('agent_id')}")
                    print("SESSION INFO DETECTADO!")
                
                if metadata.get("wrapper_aplicado"):
                    print("wrapper_aplicado: True")
                
                if metadata.get("wrapper_forzado"):
                    print("wrapper_forzado: True - FUNCIONANDO!")
                    
                if metadata.get("memoria_disponible"):
                    print("memoria_disponible: True")
            else:
                print("NO metadata en respuesta")
        else:
            print(f"Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Nuevo endpoint test-wrapper-memoria
    print("\n2. Test endpoint /api/test-wrapper-memoria...")
    
    try:
        response = requests.get(
            f"{base_url}/api/test-wrapper-memoria",
            params={
                "session_id": "test_wrapper_456",
                "agent_id": "WrapperTestAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            
            if data.get("test_wrapper"):
                print("test_wrapper: True")
            
            if "session_detectado" in data:
                session = data["session_detectado"]
                print(f"Session detectado: {session.get('session_id')}")
                print(f"Agent detectado: {session.get('agent_id')}")
            
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("WRAPPER APLICADO EN ENDPOINT DEDICADO!")
                
        else:
            print(f"Error HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("TEST FINAL COMPLETADO")

if __name__ == "__main__":
    test_wrapper_final()