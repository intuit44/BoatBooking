#!/usr/bin/env python3
import requests

def test_version():
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("Verificando version desplegada")
    print("=" * 40)
    
    # Test endpoint status para ver metadata
    try:
        response = requests.get(f"{base_url}/api/status", timeout=30)
        print(f"Status /api/status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta /api/status:")
            print(f"  Version: {data.get('version', 'N/A')}")
            print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"  Endpoints: {len(data.get('endpoints', []))}")
            
            # Verificar si tiene metadata de memoria
            metadata = data.get("metadata", {})
            if metadata:
                print(f"  Metadata presente: SI")
                print(f"  Session info: {metadata.get('session_info', 'N/A')}")
            else:
                print(f"  Metadata presente: NO")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_version()