#!/usr/bin/env python3
"""
Test directo de analizar_intencion_semantica
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from intelligent_intent_detector import analizar_intencion_semantica

def test_intencion():
    """
    Prueba directa de la detección de intención
    """
    
    consultas = [
        "En que estabamos trabajando?",
        "Muestra el estado de los recursos",
        "Ejecuta az storage account list",
        "Busca en la memoria",
        "Diagnostico completo"
    ]
    
    print("=" * 60)
    print("TEST: Deteccion de Intencion Semantica")
    print("=" * 60)
    print()
    
    for consulta in consultas:
        print(f"Consulta: '{consulta}'")
        resultado = analizar_intencion_semantica(consulta)
        print(f"  Tipo: {resultado.get('tipo')}")
        print(f"  Confianza: {resultado.get('confianza')}")
        print(f"  Endpoint sugerido: {resultado.get('endpoint_sugerido', 'N/A')}")
        print()

if __name__ == "__main__":
    test_intencion()
