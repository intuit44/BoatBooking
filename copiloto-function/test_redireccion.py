#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de redirección /api/revisar-correcciones -> /api/copiloto
"""

import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_redireccion():
    """Prueba la redirección automática"""
    print("Probando redireccion /api/revisar-correcciones -> /api/copiloto")
    
    try:
        # Importar la función
        from revisar_correcciones_http import revisar_correcciones_http
        
        # Mock request con headers de Foundry
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                self.headers = {
                    "Session-ID": "test_session_123",
                    "Agent-ID": "FoundryAgent"
                }
                self.params = {}
            
            def get_body(self):
                return b""
        
        # Ejecutar prueba
        req = MockRequest()
        response = revisar_correcciones_http(req)
        
        print(f"Status Code: {response.status_code}")
        
        # Parsear respuesta
        body = response.get_body().decode('utf-8')
        data = json.loads(body)
        
        print(f"Tipo: {data.get('tipo')}")
        print(f"Mensaje: {data.get('mensaje')}")
        print(f"Endpoint recomendado: {data.get('endpoint_recomendado')}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_redireccion()
    sys.exit(0 if success else 1)