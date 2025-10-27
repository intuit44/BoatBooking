#!/usr/bin/env python3
"""Test mínimo para verificar que el sistema funciona"""
import requests
import json

def test_simple():
    """Test básico del endpoint de historial"""
    try:
        # Usar el endpoint que sabemos que funciona
        response = requests.get("http://localhost:7071/api/status", timeout=5)
        
        if response.status_code == 200:
            print("OK - Function App esta corriendo")
            
            # Ahora probar historial
            hist_response = requests.get(
                "http://localhost:7071/api/historial-interacciones",
                headers={
                    "Session-ID": "test",
                    "Agent-ID": "test"
                },
                timeout=10
            )
            
            print(f"Historial Status: {hist_response.status_code}")
            
            if hist_response.status_code == 200:
                data = hist_response.json()
                print("OK - Historial funciona")
                print(f"Mensaje presente: {'Si' if data.get('mensaje') else 'No'}")
                return True
            else:
                print(f"ERROR Historial: {hist_response.text}")
                return False
        else:
            print("ERROR - Function App no responde")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_simple()
    print("RESULTADO:", "PASS" if success else "FAIL")