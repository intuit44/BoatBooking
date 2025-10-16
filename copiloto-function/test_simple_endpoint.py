#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar detección de endpoints
"""

from endpoint_detector import detectar_endpoint_automatico, extraer_endpoint_desde_url, normalizar_endpoint

class MockRequest:
    def __init__(self, url, method="GET", headers=None, params=None):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.params = params or {}

def test_detection():
    print("Test de deteccion de endpoints")
    
    # Test 1: URL completa
    req1 = MockRequest("http://localhost:7071/api/historial-interacciones")
    result1 = detectar_endpoint_automatico(req1)
    print(f"Test 1 - URL completa: {result1}")
    
    # Test 2: Solo extracción desde URL
    result2 = extraer_endpoint_desde_url("http://localhost:7071/api/historial-interacciones")
    print(f"Test 2 - Extraccion URL: {result2}")
    
    # Test 3: Normalización
    result3 = normalizar_endpoint("historial-interacciones")
    print(f"Test 3 - Normalizacion: {result3}")
    
    # Test 4: Diferentes URLs
    test_urls = [
        "http://localhost:7071/api/historial-interacciones",
        "http://localhost:7071/api/status", 
        "http://localhost:7071/api/copiloto",
        "http://localhost:7071/api/listar-blobs"
    ]
    
    print("\nTests multiples:")
    for url in test_urls:
        endpoint = extraer_endpoint_desde_url(url)
        print(f"  {url} -> {endpoint}")
    
    return True

if __name__ == "__main__":
    test_detection()