#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:7071"
FOUNDRY_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "azure-agents",
    "Session-ID": "assistant", 
    "Agent-ID": "assistant"
}

def test_historial():
    print("TEST: Consultando historial...")
    
    response = requests.get(
        f"{BASE_URL}/api/historial-interacciones",
        headers=FOUNDRY_HEADERS,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK - exito: {data.get('exito')}")
        print(f"OK - interacciones array: {len(data.get('interacciones', []))} elementos")
        print(f"OK - mensaje disponible: {'Si' if data.get('mensaje') else 'No'}")
        
        if data.get("mensaje"):
            print(f"\nMENSAJE PARA FOUNDRY:")
            print(data["mensaje"][:200] + "...")
        
        return True
    else:
        print(f"ERROR: {response.text}")
        return False

if __name__ == "__main__":
    print("PRUEBA REAL DE FOUNDRY")
    print("=" * 30)
    
    success = test_historial()
    
    print("\nRESULTADO:")
    print("OK - Sistema funcionando" if success else "ERROR - Sistema fallando")