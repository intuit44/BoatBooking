#!/usr/bin/env python3
"""
Test final simplificado
"""

def test_final():
    try:
        from services.semantic_intent_parser import detectar_intencion
        
        input_test = "cuales fueron las ultimas 10 interacciones"
        endpoint = "/api/revisar-correcciones"
        
        resultado = detectar_intencion(input_test, endpoint)
        
        print("Test Final")
        print("=" * 20)
        print(f"Input: {input_test}")
        print(f"Endpoint: {endpoint}")
        print(f"Redirigir: {resultado.get('redirigir')}")
        print(f"Destino: {resultado.get('endpoint_destino', 'N/A')}")
        
        if resultado.get('redirigir'):
            print("SUCCESS: Redireccion detectada")
            return True
        else:
            print("ERROR: No redireccion")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_final()
    if success:
        print("\nLISTO PARA DESPLEGAR")
    else:
        print("\nNECESITA REVISION")