#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de debug específico para memoria automática
"""

import requests
import json
import uuid

def test_memoria_debug():
    """
    Test específico para debuggear el sistema de memoria
    """
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    session_id = f"debug_{uuid.uuid4().hex[:8]}"
    
    print("=== DEBUG MEMORIA AUTOMATICA ===")
    print(f"URL: {base_url}")
    print(f"Session ID: {session_id}")
    print("=" * 50)
    
    # Test 1: Verificar que el endpoint responde
    print("\n1. Test básico de conectividad")
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar-cli",
            json={"comando": "az --version"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Respuesta JSON válida recibida")
                
                # Verificar estructura de respuesta
                print(f"Campos en respuesta: {list(data.keys())}")
                
                # Buscar cualquier referencia a memoria o metadata
                if "metadata" in data:
                    print(f"METADATA ENCONTRADA: {data['metadata']}")
                else:
                    print("NO HAY METADATA en la respuesta")
                
                # Buscar session info
                session_info = None
                for key, value in data.items():
                    if "session" in str(key).lower() or "memoria" in str(key).lower():
                        print(f"Campo relacionado con memoria: {key} = {value}")
                        session_info = value
                
                if not session_info:
                    print("NO se encontró información de sesión")
                
            except json.JSONDecodeError:
                print("ERROR: Respuesta no es JSON válido")
                print(f"Respuesta raw: {response.text[:200]}")
        else:
            print(f"ERROR HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"ERROR de conexión: {e}")
    
    # Test 2: Con headers explícitos
    print("\n2. Test con headers de sesión explícitos")
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar-cli",
            json={"comando": "az --version"},
            headers={
                "X-Session-ID": session_id,
                "X-Agent-ID": "DebugAgent",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Respuesta con headers:")
                
                # Verificar si los headers fueron procesados
                if "metadata" in data:
                    metadata = data["metadata"]
                    print(f"Metadata: {json.dumps(metadata, indent=2)}")
                    
                    if "session_info" in metadata:
                        session_info = metadata["session_info"]
                        print(f"Session info detectada: {session_info}")
                        
                        if session_info.get("session_id") == session_id:
                            print("✅ Session ID correctamente detectado")
                        else:
                            print(f"❌ Session ID no coincide: esperado={session_id}, recibido={session_info.get('session_id')}")
                    else:
                        print("❌ NO hay session_info en metadata")
                else:
                    print("❌ NO hay metadata en respuesta con headers")
                    
            except json.JSONDecodeError:
                print("ERROR: Respuesta no es JSON válido")
        else:
            print(f"ERROR HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Con parámetros en el body
    print("\n3. Test con session_id en el body")
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar-cli",
            json={
                "comando": "az --version",
                "session_id": session_id,
                "agent_id": "DebugAgent"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Respuesta con session_id en body:")
                
                if "metadata" in data:
                    print(f"Metadata encontrada: {data['metadata']}")
                else:
                    print("NO hay metadata")
                    
            except json.JSONDecodeError:
                print("ERROR: Respuesta no es JSON válido")
        else:
            print(f"ERROR HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_memoria_debug()