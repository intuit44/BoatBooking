#!/usr/bin/env python3
"""
Test para validar que la redirección llama al handler real
"""

def test_handler_direct_call():
    """Test de llamada directa al handler"""
    
    try:
        # Importar función directamente
        import function_app
        
        print("Test de llamada directa al handler")
        print("=" * 40)
        
        # Verificar que la función existe
        handler = getattr(function_app, 'historial_interacciones', None)
        
        if handler:
            print("OK: Función historial_interacciones encontrada")
            print(f"Tipo: {type(handler)}")
            
            # Mock request simple
            class MockRequest:
                def __init__(self):
                    self.method = "GET"
                    self.url = "/api/historial-interacciones"
                    self.params = {"limit": "5"}
                    self.headers = {}
                
                def get_json(self):
                    return None
            
            mock_req = MockRequest()
            
            # Llamar directamente al handler
            print("Llamando directamente al handler...")
            response = handler(mock_req)
            
            print(f"Respuesta tipo: {type(response)}")
            
            if hasattr(response, 'get_body'):
                try:
                    body = response.get_body().decode()
                    print(f"Body (primeros 200 chars): {body[:200]}...")
                    return True
                except Exception as e:
                    print(f"Error leyendo body: {e}")
                    return False
            else:
                print(f"Respuesta: {response}")
                return True
                
        else:
            print("ERROR: Función historial_interacciones NO encontrada")
            
            # Listar funciones disponibles
            available = [name for name in dir(function_app) if not name.startswith('_')]
            print(f"Funciones disponibles: {available[:10]}...")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redirection_with_direct_call():
    """Test de redirección con llamada directa"""
    
    try:
        from services.semantic_intent_parser import invocar_endpoint_interno
        
        print("\nTest de redirección con llamada directa")
        print("=" * 40)
        
        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                self.url = "/api/revisar-correcciones"
                self.params = {"consulta": "ultimas interacciones"}
                self.headers = {}
            
            def get_json(self):
                return None
        
        mock_req = MockRequest()
        payload = {"input_original": "ultimas interacciones"}
        
        print("Invocando endpoint interno...")
        response = invocar_endpoint_interno("/api/historial-interacciones", payload, mock_req)
        
        print(f"Respuesta tipo: {type(response)}")
        
        if hasattr(response, 'get_body'):
            try:
                body = response.get_body().decode()
                print(f"Body (primeros 200 chars): {body[:200]}...")
                return True
            except Exception as e:
                print(f"Error leyendo body: {e}")
                return False
        else:
            print(f"Respuesta: {response}")
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("VALIDANDO LLAMADA DIRECTA AL HANDLER")
    print("=" * 50)
    
    test1 = test_handler_direct_call()
    test2 = test_redirection_with_direct_call()
    
    if test1 and test2:
        print("\nOK: Handler se puede llamar directamente")
        print("LISTO PARA DESPLEGAR")
    else:
        print("\nERROR: Problema con llamada directa")
        print("NECESITA REVISION")