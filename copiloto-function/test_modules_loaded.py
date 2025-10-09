#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si los nuevos módulos están cargados en la Function App
"""

import requests
import json

BASE_URL = "http://localhost:7071"

def test_module_availability():
    """Prueba si los nuevos módulos están disponibles"""
    print("🔍 VERIFICANDO DISPONIBILIDAD DE MÓDULOS SEMÁNTICOS")
    print(f"URL Base: {BASE_URL}")
    print("="*60)
    
    # Test 1: Verificar que /api/hybrid responde
    print("\n1. Probando /api/hybrid básico...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/hybrid",
            json={"agent_response": "test"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            version = data.get("metadata", {}).get("version", "unknown")
            print(f"   Versión: {version}")
            
            if "semantic" in version:
                print("   ✅ Versión semántica detectada")
            else:
                print("   ⚠️ Versión anterior detectada")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Verificar endpoint /api/bing-grounding
    print("\n2. Probando /api/bing-grounding...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/bing-grounding",
            json={"query": "test query"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Endpoint bing-grounding disponible")
        else:
            print(f"   ⚠️ Endpoint responde con: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Verificar si hay logs de importación
    print("\n3. Probando importación de módulos semánticos...")
    try:
        # Hacer una llamada que debería activar la importación
        response = requests.post(
            f"{BASE_URL}/api/hybrid",
            json={"agent_response": "clasificar esta consulta semánticamente"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Buscar evidencia de clasificación semántica
            has_classification = False
            resultado = data.get("resultado", {})
            
            if "semantic_classification" in str(data):
                has_classification = True
                print("   ✅ Clasificación semántica encontrada en respuesta")
            elif "classification" in str(data):
                has_classification = True
                print("   ✅ Clasificación encontrada en respuesta")
            else:
                print("   ⚠️ No se encontró clasificación semántica")
                print(f"   Respuesta: {json.dumps(data, indent=2)[:300]}...")
            
            return has_classification
        else:
            print(f"   ❌ Error en llamada: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Ejecuta verificación de módulos"""
    modules_loaded = test_module_availability()
    
    print("\n" + "="*60)
    print("📊 RESULTADO DE VERIFICACIÓN")
    print("="*60)
    
    if modules_loaded:
        print("✅ MÓDULOS SEMÁNTICOS CARGADOS CORRECTAMENTE")
        print("El sistema está listo para clasificación semántica")
    else:
        print("❌ MÓDULOS SEMÁNTICOS NO DISPONIBLES")
        print("Necesitas reiniciar la Function App para cargar los cambios")
        print("\nPasos para actualizar:")
        print("1. Detener la Function App (Ctrl+C)")
        print("2. Ejecutar: func start")
        print("3. Esperar a que cargue completamente")
        print("4. Volver a ejecutar las pruebas")
    
    return modules_loaded

if __name__ == "__main__":
    main()