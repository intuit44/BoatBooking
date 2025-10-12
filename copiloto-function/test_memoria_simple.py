#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de memoria automática
"""

import json
import requests
import uuid

def test_memoria_simple():
    """
    Test simple para verificar memoria automática
    """
    
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("Probando memoria automatica en endpoints criticos")
    print(f"Session ID: {session_id}")
    print("=" * 50)
    
    # Test endpoint ejecutar-cli
    print("\nTest 1: ejecutar-cli")
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar-cli",
            json={
                "comando": "storage account list",
                "session_id": session_id,
                "agent_id": "TestAgent"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Verificar memoria
                metadata = data.get("metadata", {})
                session_info = metadata.get("session_info", {})
                memoria_disponible = metadata.get("memoria_disponible", False)
                
                print(f"Session ID detectado: {session_info.get('session_id') == session_id}")
                print(f"Agent ID detectado: {bool(session_info.get('agent_id'))}")
                print(f"Memoria disponible: {memoria_disponible}")
                
                if session_info.get('session_id') or session_info.get('agent_id'):
                    print("EXITO: Memoria automatica funcionando")
                else:
                    print("FALLO: No se detecta memoria automatica")
                    
            except json.JSONDecodeError:
                print("Error: Respuesta no es JSON")
        else:
            print(f"Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test endpoint diagnostico-recursos
    print("\nTest 2: diagnostico-recursos")
    try:
        response = requests.get(
            f"{base_url}/api/diagnostico-recursos",
            params={
                "session_id": session_id,
                "agent_id": "TestAgent"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                metadata = data.get("metadata", {})
                session_info = metadata.get("session_info", {})
                
                if session_info.get('session_id') or session_info.get('agent_id'):
                    print("EXITO: Memoria automatica funcionando")
                else:
                    print("FALLO: No se detecta memoria automatica")
                    
            except json.JSONDecodeError:
                print("Error: Respuesta no es JSON")
        else:
            print(f"Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_memoria_simple()