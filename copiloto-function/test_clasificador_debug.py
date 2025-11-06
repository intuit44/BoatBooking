#!/usr/bin/env python3
"""
Debug del clasificador de intención
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Simular el entorno de Azure Functions
os.environ.setdefault('AZURE_FUNCTIONS_ENVIRONMENT', 'Development')

from intelligent_intent_detector import analizar_intencion_semantica
import json

def test_clasificador():
    consulta = "En que estabamos trabajando?"
    
    print("=" * 60)
    print("DEBUG: Clasificador de Intencion")
    print("=" * 60)
    print(f"Consulta: '{consulta}'")
    print()
    
    resultado = analizar_intencion_semantica(consulta)
    
    print("RESULTADO DEL CLASIFICADOR:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print()
    
    print("VALIDACIONES:")
    print(f"[{'OK' if resultado.get('tipo') else 'FAIL'}] Tipo detectado: {resultado.get('tipo')}")
    print(f"[{'OK' if resultado.get('confianza') else 'FAIL'}] Confianza: {resultado.get('confianza')}")
    print(f"[{'OK' if resultado.get('endpoint_sugerido') else 'FAIL'}] Endpoint sugerido: {resultado.get('endpoint_sugerido', 'NINGUNO')}")
    print()
    
    if resultado.get('endpoint_sugerido'):
        print(f"[OK] ROUTER DEBERIA REDIRIGIR A: {resultado['endpoint_sugerido']}")
    else:
        print("[FAIL] NO HAY ENDPOINT SUGERIDO - ROUTER NO DISPARARA")

if __name__ == "__main__":
    test_clasificador()
