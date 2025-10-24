#!/usr/bin/env python3
"""
Test simple para verificar la corrección de Foundry Metrics Integration
"""

import requests
import json
import sys
from datetime import datetime

def test_semantic_route():
    """Test de la ruta semántica"""
    print("Probando ruta semantica /api/ejecutar con diagnosticar:completo...")
    
    try:
        payload = {"intencion": "diagnosticar:completo"}
        response = requests.post(
            "http://localhost:7071/api/ejecutar", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            function_app_metrics = data.get("data", {}).get("metricas", {}).get("function_app")
            
            if function_app_metrics and not function_app_metrics.get("error"):
                print("EXITO: Ruta semantica devuelve metricas")
                print(f"Metricas encontradas: {list(function_app_metrics.keys())}")
                return True
            else:
                print("FALLO: Ruta semantica no devuelve metricas")
                
                # Verificar resource group
                function_app_info = data.get("data", {}).get("recursos", {}).get("function_app", {})
                error_msg = function_app_info.get("error", "")
                
                if "boat-rental-rg" in error_msg:
                    print("PROBLEMA: Usando resource group incorrecto 'boat-rental-rg'")
                    print("SOLUCION: Reiniciar servidor Azure Functions")
                    return False
                else:
                    print(f"Error: {error_msg}")
                    return False
        else:
            print(f"Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Excepcion: {str(e)}")
        return False

def test_direct_endpoint():
    """Test del endpoint directo"""
    print("Probando endpoint directo /api/diagnostico-recursos-completo...")
    
    try:
        response = requests.get("http://localhost:7071/api/diagnostico-recursos-completo?metricas=true", timeout=30)
        if response.status_code == 200:
            data = response.json()
            function_app_metrics = data.get("metricas", {}).get("function_app")
            if function_app_metrics and not function_app_metrics.get("error"):
                print("EXITO: Endpoint directo funciona")
                return True
            else:
                print("FALLO: Endpoint directo sin metricas")
                return False
        else:
            print(f"Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Excepcion: {str(e)}")
        return False

def main():
    print("FOUNDRY METRICS INTEGRATION - TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    direct_works = test_direct_endpoint()
    print()
    semantic_works = test_semantic_route()
    
    print()
    print("RESUMEN:")
    print(f"Endpoint directo: {'OK' if direct_works else 'FALLO'}")
    print(f"Ruta semantica: {'OK' if semantic_works else 'FALLO'}")
    
    if semantic_works:
        print("RESULTADO: CORRECCIONES FUNCIONAN")
        sys.exit(0)
    else:
        print("RESULTADO: NECESITA REINICIO DEL SERVIDOR")
        sys.exit(1)

if __name__ == "__main__":
    main()