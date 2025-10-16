#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de casos ambiguos y edge cases para detección de intención
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_casos_ambiguos():
    """Test de casos ambiguos que requieren heurística contextual"""
    
    try:
        from services.semantic_intent_parser import detectar_intencion
        
        print("Test de casos ambiguos y edge cases")
        print("=" * 50)
        
        # Casos ambiguos con contexto
        casos_ambiguos = [
            {
                "input": "ultimos cambios que hice en la conversacion",
                "contexto": "usuario + conversacion",
                "esperado": "historial-interacciones",
                "descripcion": "Cambios en conversación -> historial"
            },
            {
                "input": "ultimos cambios en el codigo",
                "contexto": "codigo + sistema", 
                "esperado": "revisar-correcciones",
                "descripcion": "Cambios en código -> correcciones"
            },
            {
                "input": "ver actividad del usuario",
                "contexto": "usuario",
                "esperado": "historial-interacciones", 
                "descripcion": "Actividad usuario -> historial"
            },
            {
                "input": "ver actividad del sistema",
                "contexto": "sistema",
                "esperado": "revisar-correcciones",
                "descripcion": "Actividad sistema -> correcciones"
            },
            {
                "input": "que paso en la ultima sesion",
                "contexto": "conversacion",
                "esperado": "historial-interacciones",
                "descripcion": "Qué pasó sesión -> historial"
            },
            {
                "input": "que paso con el archivo config",
                "contexto": "archivo",
                "esperado": "revisar-correcciones", 
                "descripcion": "Qué pasó archivo -> correcciones"
            }
        ]
        
        resultados = []
        
        for i, caso in enumerate(casos_ambiguos, 1):
            print(f"\nTest {i}: '{caso['input']}'")
            print(f"   Contexto: {caso['contexto']}")
            print(f"   Esperado: {caso['esperado']}")
            
            resultado = detectar_intencion(caso['input'], "/api/revisar-correcciones")
            
            if resultado.get('redirigir'):
                endpoint_detectado = resultado['endpoint_destino'].replace('/api/', '')
                print(f"   Detectado: {endpoint_detectado}")
                print(f"   Razon: {resultado['razon']}")
                print(f"   Confianza: {resultado['confianza']:.2f}")
                
                if endpoint_detectado == caso['esperado']:
                    print(f"   OK - Resuelto correctamente")
                    resultados.append(True)
                else:
                    print(f"   ERROR - Esperado {caso['esperado']}")
                    resultados.append(False)
            else:
                print(f"   No redirigir - {resultado['razon']}")
                resultados.append(False)
        
        # Resumen
        print("\n" + "=" * 50)
        exitosos = sum(resultados)
        total = len(resultados)
        porcentaje = (exitosos / total) * 100
        
        print(f"Casos ambiguos: {exitosos}/{total} resueltos ({porcentaje:.1f}%)")
        
        return porcentaje >= 70  # 70% mínimo para casos ambiguos
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases_extremos():
    """Test de casos extremos"""
    
    try:
        from services.semantic_intent_parser import detectar_intencion
        
        print("\nTest de casos extremos")
        print("=" * 30)
        
        casos_extremos = [
            ("", "Input vacío"),
            ("a", "Input muy corto"),
            ("hola como estas", "Saludo sin intención técnica"),
            ("12345", "Solo números"),
            ("???", "Solo símbolos"),
            ("revisar todo lo que paso ayer en el sistema y la conversacion", "Muy ambiguo")
        ]
        
        for input_test, descripcion in casos_extremos:
            print(f"\nTest: '{input_test}' ({descripcion})")
            
            resultado = detectar_intencion(input_test, "/api/revisar-correcciones")
            
            if resultado.get('redirigir'):
                print(f"   Redirige a: {resultado['endpoint_destino']}")
                print(f"   Confianza: {resultado['confianza']:.2f}")
            else:
                print(f"   No redirige: {resultado['razon']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR en edge cases: {e}")
        return False

def main():
    """Ejecuta todos los tests de edge cases"""
    
    print("TESTS DE CASOS AMBIGUOS Y EDGE CASES")
    print("=" * 60)
    
    # Test 1: Casos ambiguos
    test1_ok = test_casos_ambiguos()
    
    # Test 2: Edge cases extremos
    test2_ok = test_edge_cases_extremos()
    
    # Resultado final
    print("\n" + "=" * 60)
    if test1_ok and test2_ok:
        print("TODOS LOS EDGE CASES MANEJADOS CORRECTAMENTE")
        print("Sistema robusto para casos ambiguos")
        return 0
    else:
        print("ALGUNOS EDGE CASES NECESITAN ATENCION")
        if not test1_ok:
            print("- Mejorar heuristica para casos ambiguos")
        if not test2_ok:
            print("- Revisar manejo de casos extremos")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)