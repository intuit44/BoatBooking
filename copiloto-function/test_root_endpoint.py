#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar endpoint raíz de Function App
"""

import requests

def test_root():
    """
    Test del endpoint raíz
    """
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("Probando endpoint raiz de Function App")
    print(f"URL: {base_url}")
    print("=" * 50)
    
    # Test endpoint raíz
    print("\nTest 1: /")
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Contenido: {response.text[:500]}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test sin ruta específica
    print("\nTest 2: URL base")
    try:
        response = requests.get(base_url, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Contenido: {response.text[:500]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_root()