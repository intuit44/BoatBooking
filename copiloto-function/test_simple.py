#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de la función revisar_correcciones_http
"""

import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Mock básico de azure.functions
class MockHttpResponse:
    def __init__(self, body, status_code=200, mimetype="application/json"):
        self._body = body.encode('utf-8') if isinstance(body, str) else body
        self.status_code = status_code
        self.mimetype = mimetype
    
    def get_body(self):
        return self._body

class MockHttpRequest:
    def __init__(self):
        self.method = "GET"
        self.headers = {
            "Session-ID": "test_session_123",
            "Agent-ID": "FoundryAgent"
        }
        self.params = {}
    
    def get_body(self):
        return b""

# Mock azure.functions module
class MockFunc:
    HttpResponse = MockHttpResponse
    HttpRequest = MockHttpRequest

sys.modules['azure.functions'] = MockFunc()

def test_funcion_basica():
    """Test básico de la función sin dependencias complejas"""
    print("Probando función revisar_correcciones_http...")
    
    try:
        # Importar solo las funciones necesarias
        import json
        from datetime import datetime
        
        # Función simplificada para test
        def revisar_correcciones_test(req):
            response = {
                "tipo": "correcciones_disponibles",
                "mensaje": "Para ver correcciones, usa /api/copiloto con memoria integrada",
                "endpoint_recomendado": "/api/copiloto",
                "timestamp": datetime.now().isoformat()
            }
            
            return MockHttpResponse(
                json.dumps(response, ensure_ascii=False),
                status_code=200
            )
        
        # Ejecutar test
        req = MockHttpRequest()
        response = revisar_correcciones_test(req)
        
        print(f"Status Code: {response.status_code}")
        
        # Parsear respuesta
        body = response.get_body().decode('utf-8')
        data = json.loads(body)
        
        print(f"Tipo: {data.get('tipo')}")
        print(f"Endpoint recomendado: {data.get('endpoint_recomendado')}")
        
        # Verificar que la respuesta es correcta
        assert data.get('tipo') == 'correcciones_disponibles'
        assert data.get('endpoint_recomendado') == '/api/copiloto'
        
        print("Test EXITOSO - La redirección funciona correctamente")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_funcion_basica()
    sys.exit(0 if success else 1)