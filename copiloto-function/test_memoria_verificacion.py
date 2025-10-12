#!/usr/bin/env python3
import requests
import json

def test_memoria_azure():
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("Verificando sistema de memoria en Azure")
    print("=" * 50)
    
    # Test 1: Verificar si endpoint ejecutar-cli existe y responde
    print("\nTest 1: Verificar endpoint ejecutar-cli")
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar-cli",
            json={"comando": "az --version"},
            headers={"X-Session-ID": "test_memoria_001", "X-Agent-ID": "TestAgent"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta recibida:")
            print(json.dumps(data, indent=2)[:500])
            
            # Verificar si tiene metadata de memoria
            metadata = data.get("metadata", {})
            session_info = metadata.get("session_info", {})
            
            if session_info:
                print("\nMEMORIA DETECTADA:")
                print(f"  Session ID: {session_info.get('session_id')}")
                print(f"  Agent ID: {session_info.get('agent_id')}")
                print(f"  Memoria disponible: {metadata.get('memoria_disponible')}")
            else:
                print("\nNO HAY METADATA DE MEMORIA")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_memoria_azure()