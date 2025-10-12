#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar que la Function App esté funcionando
"""

import requests

def test_status():
    """
    Test básico para verificar conectividad
    """
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("Probando conectividad con Function App")
    print(f"URL: {base_url}")
    print("=" * 50)
    
    # Test endpoint status
    print("\nTest 1: /api/status")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Respuesta: {data}")
                print("Function App funcionando correctamente")
            except:
                print("Respuesta no es JSON valido")
        else:
            print(f"ERROR HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"ERROR de conexion: {e}")
    
    # Test endpoint health
    print("\nTest 2: /api/health")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Health check OK")
        else:
            print(f"Health check fallo: {response.status_code}")
            
    except Exception as e:
        print(f"Error en health check: {e}")

if __name__ == "__main__":
    test_status()