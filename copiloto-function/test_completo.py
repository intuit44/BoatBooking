#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo de redirección con detección de errores reales
"""

import json
import sys
import os
import unittest.mock
sys.path.append(os.path.dirname(__file__))

def test_redireccion_completa():
    """Test que detecta problemas reales de redirección"""
    print("Test completo: /api/revisar-correcciones -> /api/copiloto")
    
    # Mock de requests para simular la llamada HTTP
    with unittest.mock.patch('requests.get') as mock_get:
        # Configurar respuesta simulada del copiloto
        mock_response = unittest.mock.Mock()
        mock_response.text = json.dumps({
            "tipo": "respuesta_copiloto",
            "mensaje": "Correcciones disponibles via copiloto",
            "correcciones": [
                {"id": "fix_001", "estado": "pendiente"},
                {"id": "fix_002", "estado": "aplicada"}
            ]
        })
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        try:
            # Mock de azure.functions
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
                        "Session-ID": "test_session_foundry_123",
                        "Agent-ID": "FoundryAgent"
                    }
                    self.params = {}
                
                def get_body(self):
                    return b""

            # Mock del módulo azure.functions
            import types
            func_module = types.ModuleType('azure.functions')
            func_module.HttpResponse = MockHttpResponse
            func_module.HttpRequest = MockHttpRequest
            sys.modules['azure.functions'] = func_module
            
            # Importar y probar la función real
            from revisar_correcciones_http import revisar_correcciones_http
            
            # Crear request con headers de Foundry
            req = MockHttpRequest()
            
            # Ejecutar la función
            response = revisar_correcciones_http(req)
            
            # Verificar que la redirección funcionó
            print(f"Status Code: {response.status_code}")
            
            body = response.get_body().decode('utf-8')
            data = json.loads(body)
            
            print(f"Respuesta: {data.get('tipo')}")
            
            # Verificar que se llamó a requests.get con los parámetros correctos
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            
            # Verificar URL
            url = call_args[0][0]
            print(f"URL llamada: {url}")
            assert "/api/copiloto" in url
            
            # Verificar headers preservados
            headers = call_args[1]['headers']
            print(f"Session-ID preservado: {headers.get('Session-ID')}")
            print(f"Agent-ID preservado: {headers.get('Agent-ID')}")
            
            assert headers.get('Session-ID') == 'test_session_foundry_123'
            assert headers.get('Agent-ID') == 'FoundryAgent'
            
            # Verificar parámetros
            params = call_args[1]['params']
            print(f"Mensaje enviado: {params.get('mensaje')}")
            assert 'correcciones' in params.get('mensaje', '')
            
            print("✅ Test COMPLETO EXITOSO")
            print("- Redirección HTTP funciona")
            print("- Headers preservados correctamente") 
            print("- Parámetros enviados correctamente")
            print("- Respuesta procesada correctamente")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR DETECTADO: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_sin_requests():
    """Test de fallback cuando requests falla"""
    print("\nTest de fallback sin requests...")
    
    # Mock que simula fallo de requests
    with unittest.mock.patch('requests.get', side_effect=Exception("Network error")):
        try:
            # Mismo setup que antes
            class MockHttpResponse:
                def __init__(self, body, status_code=200, mimetype="application/json"):
                    self._body = body.encode('utf-8') if isinstance(body, str) else body
                    self.status_code = status_code
                
                def get_body(self):
                    return self._body

            class MockHttpRequest:
                def __init__(self):
                    self.method = "GET"
                    self.headers = {"Session-ID": "test", "Agent-ID": "test"}
                    self.params = {}
                
                def get_body(self):
                    return b""

            import types
            func_module = types.ModuleType('azure.functions')
            func_module.HttpResponse = MockHttpResponse
            sys.modules['azure.functions'] = func_module
            
            from revisar_correcciones_http import revisar_correcciones_http
            
            req = MockHttpRequest()
            response = revisar_correcciones_http(req)
            
            # Debe usar fallback
            body = response.get_body().decode('utf-8')
            data = json.loads(body)
            
            print(f"Fallback tipo: {data.get('tipo')}")
            assert data.get('tipo') == 'correcciones_disponibles'
            assert '/api/copiloto' in data.get('endpoint_recomendado', '')
            
            print("✅ Fallback funciona correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en fallback: {e}")
            return False

if __name__ == "__main__":
    success1 = test_redireccion_completa()
    success2 = test_sin_requests()
    
    if success1 and success2:
        print("\n🎉 TODOS LOS TESTS EXITOSOS - Listo para desplegar")
    else:
        print("\n💥 TESTS FALLARON - Revisar antes de desplegar")
    
    sys.exit(0 if (success1 and success2) else 1)