#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar que el wrapper de memoria funciona
"""

import requests
import json

def test_simple():
    """Test básico del wrapper de memoria"""
    
    base_url = "http://localhost:7071"
    
    headers = {
        "Content-Type": "application/json",
        "Agent-ID": "TestAgent", 
        "Session-ID": "test-session-123"
    }
    
    print("INICIANDO TEST SIMPLE DEL WRAPPER")
    print("=" * 40)
    
    # Test 1: Status
    print("\n1. Probando /api/status...")
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("OK - Status: Wrapper aplicado correctamente")
            else:
                print("ERROR - Status: Wrapper NO aplicado")
                print(f"Respuesta: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"ERROR - Status: HTTP {response.status_code}")
    except Exception as e:
        print(f"ERROR - Status: {e}")
    
    # Test 2: Historial
    print("\n2. Probando /api/historial-interacciones...")
    try:
        response = requests.get(f"{base_url}/api/historial-interacciones", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("OK - Historial: Wrapper aplicado correctamente")
                if data.get("contexto_conversacion"):
                    print(f"   Contexto: {data['contexto_conversacion']['mensaje']}")
                else:
                    print("   Sin contexto previo (normal para primera ejecucion)")
            else:
                print("ERROR - Historial: Wrapper NO aplicado")
        else:
            print(f"ERROR - Historial: HTTP {response.status_code}")
    except Exception as e:
        print(f"ERROR - Historial: {e}")
    
    print("\n" + "=" * 40)
    print("TEST COMPLETADO")
    print("\nDIAGNOSTICO:")
    print("- Si ves 'OK' en ambos tests, el wrapper funciona")
    print("- Si ves 'ERROR', revisar configuracion del backend")

if __name__ == "__main__":
    test_simple()