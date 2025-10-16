#!/usr/bin/env python3
"""
Test simple para verificar que la redirección funciona
"""

def test_redirect_logic():
    """Test de la lógica de redirección"""
    
    try:
        from services.semantic_intent_parser import aplicar_deteccion_intencion
        
        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                self.url = "/api/revisar-correcciones"
                self.params = {"consulta": "cuales fueron las ultimas 10 interacciones"}
                self.headers = {}
            
            def get_json(self):
                return None
        
        mock_req = MockRequest()
        
        print("Test de redirección directa")
        print("=" * 40)
        print(f"URL: {mock_req.url}")
        print(f"Params: {mock_req.params}")
        
        fue_redirigido, respuesta = aplicar_deteccion_intencion(mock_req, "/api/revisar-correcciones")
        
        print(f"Fue redirigido: {fue_redirigido}")
        
        if fue_redirigido:
            print("✅ REDIRECCIÓN FUNCIONANDO")
            print(f"Respuesta tipo: {type(respuesta)}")
            return True
        else:
            print("❌ NO SE APLICÓ REDIRECCIÓN")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_redirect_logic()
    if success:
        print("\n✅ LISTO PARA DESPLEGAR")
    else:
        print("\n❌ NECESITA REVISIÓN")