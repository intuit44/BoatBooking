#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar la memoria semántica
"""

import sys
import json

def test_semantic_memory():
    """Test básico de memoria semántica"""
    try:
        from services.semantic_memory import obtener_estado_sistema, obtener_contexto_agente
        
        print("Probando obtener_estado_sistema...")
        resultado = obtener_estado_sistema(1)  # Última hora
        
        if resultado.get("exito"):
            estado = resultado["estado"]
            print(f"OK - Interacciones encontradas: {estado.get('total_interacciones', 0)}")
            print(f"OK - Subsistemas activos: {len(estado.get('subsistemas_activos', []))}")
            print(f"OK - Monitoreo detectado: {estado.get('monitoreo_activo', False)}")
        else:
            print(f"ERROR: {resultado.get('error')}")
            return False
        
        print("\nProbando obtener_contexto_agente...")
        contexto = obtener_contexto_agente("test_agent", 5)
        
        if contexto.get("exito"):
            print("OK - Contexto de agente obtenido")
        else:
            print(f"INFO - Sin contexto para test_agent: {contexto.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"ERROR en test: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando test de memoria semantica...")
    print("=" * 40)
    
    success = test_semantic_memory()
    
    print("\n" + "=" * 40)
    if success:
        print("Test completado exitosamente")
        sys.exit(0)
    else:
        print("Test falló")
        sys.exit(1)