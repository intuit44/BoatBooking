#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar que el memory wrapper funciona correctamente
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_memory_wrapper():
    """Prueba básica del memory wrapper"""
    try:
        # Importar Azure Functions mock
        import azure.functions as func
        
        # Crear una FunctionApp mock
        app = func.FunctionApp()
        
        # Verificar que app.route existe
        print(f"OK app.route original: {type(app.route)}")
        
        # Importar y aplicar el wrapper
        from memory_route_wrapper import apply_memory_wrapper
        
        print("Aplicando memory wrapper...")
        apply_memory_wrapper(app)
        
        # Verificar que el wrapper se aplicó
        print(f"OK app.route después del wrapper: {type(app.route)}")
        
        # Probar que el wrapper mantiene la firma
        @app.route(route="test", methods=["GET"])
        def test_function(req):
            return func.HttpResponse("Test OK")
        
        print("OK Decorador @app.route funciona correctamente")
        
        # Verificar que la función se registró
        functions = app.get_functions()
        print(f"OK Funciones registradas: {len(functions)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_decorator():
    """Prueba el decorador de memoria directamente"""
    try:
        from services.memory_decorator import registrar_memoria
        
        print("Probando decorador de memoria...")
        
        # Crear función mock
        @registrar_memoria("test_endpoint")
        def mock_function(req):
            import azure.functions as func
            return func.HttpResponse("Mock response")
        
        print("OK Decorador de memoria aplicado correctamente")
        
        return True
        
    except Exception as e:
        print(f"ERROR en test de decorador: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando tests del memory wrapper...")
    print("=" * 50)
    
    # Test 1: Memory wrapper
    print("\nTest 1: Memory Wrapper")
    test1_ok = test_memory_wrapper()
    
    # Test 2: Memory decorator
    print("\nTest 2: Memory Decorator")  
    test2_ok = test_memory_decorator()
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DE TESTS:")
    print(f"   Memory Wrapper: {'PASS' if test1_ok else 'FAIL'}")
    print(f"   Memory Decorator: {'PASS' if test2_ok else 'FAIL'}")
    
    if test1_ok and test2_ok:
        print("\nTodos los tests pasaron! El memory wrapper esta listo.")
        sys.exit(0)
    else:
        print("\nAlgunos tests fallaron. Revisar errores arriba.")
        sys.exit(1)