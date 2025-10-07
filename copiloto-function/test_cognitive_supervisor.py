#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del supervisor cognitivo
"""

import sys

def test_cognitive_supervisor():
    """Test del supervisor cognitivo"""
    try:
        from services.cognitive_supervisor import CognitiveSupervisor
        
        print("Iniciando supervisor cognitivo...")
        supervisor = CognitiveSupervisor()
        
        # Ejecutar análisis
        resultado = supervisor.analyze_and_learn(1)  # Última hora
        
        if resultado.get("exito"):
            conocimiento = resultado["conocimiento"]
            print(f"OK - Snapshot creado: {resultado['snapshot_id']}")
            print(f"OK - Evaluación: {conocimiento['evaluacion_sistema']}")
            print(f"OK - Tasa éxito: {conocimiento['metricas_clave']['tasa_exito']:.1%}")
            print(f"OK - Recomendaciones: {len(conocimiento['recomendaciones'])}")
            
            # Test obtener conocimiento
            ultimo = supervisor.get_latest_knowledge()
            if ultimo.get("exito"):
                print("OK - Conocimiento recuperado correctamente")
            else:
                print(f"WARN - No se pudo recuperar: {ultimo.get('error')}")
            
            return True
        else:
            print(f"ERROR: {resultado.get('error')}")
            return False
            
    except Exception as e:
        print(f"ERROR en test: {e}")
        return False

if __name__ == "__main__":
    print("Test Supervisor Cognitivo")
    print("=" * 30)
    
    success = test_cognitive_supervisor()
    
    print("\n" + "=" * 30)
    if success:
        print("Test completado exitosamente")
        sys.exit(0)
    else:
        print("Test falló")
        sys.exit(1)