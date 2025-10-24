#!/usr/bin/env python3
"""
Test simple para comparar las dos rutas de acceso a métricas
"""

import requests
import json

def test_compare_routes():
    base_url = "http://localhost:7071"
    
    print("=== COMPARACIÓN DE RUTAS ===")
    
    # Ruta 1: Endpoint directo
    print("\n1. Endpoint directo /api/diagnostico-recursos-completo")
    try:
        response1 = requests.get(f"{base_url}/api/diagnostico-recursos-completo?metricas=true", timeout=30)
        data1 = response1.json()
        
        fa_metrics1 = data1.get("metricas", {}).get("function_app", {})
        print(f"   Status: {response1.status_code}")
        print(f"   Function App metrics: {list(fa_metrics1.keys()) if fa_metrics1 else 'NONE'}")
        if fa_metrics1:
            print(f"   Sample metric: {list(fa_metrics1.items())[0] if fa_metrics1 else 'N/A'}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Ruta 2: A través de /api/ejecutar
    print("\n2. A través de /api/ejecutar (ruta semántica)")
    try:
        payload = {"intencion": "diagnosticar:completo", "parametros": {}}
        response2 = requests.post(
            f"{base_url}/api/ejecutar", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        data2 = response2.json()
        
        # Buscar métricas en ambas estructuras posibles
        fa_metrics2 = (data2.get("metricas", {}).get("function_app", {}) or 
                      data2.get("data", {}).get("metricas", {}).get("function_app", {}))
        
        print(f"   Status: {response2.status_code}")
        print(f"   Function App metrics: {list(fa_metrics2.keys()) if fa_metrics2 else 'NONE'}")
        if fa_metrics2:
            print(f"   Sample metric: {list(fa_metrics2.items())[0] if fa_metrics2 else 'N/A'}")
        
        # Debug: mostrar estructura completa de métricas
        all_metrics = data2.get("metricas", {}) or data2.get("data", {}).get("metricas", {})
        print(f"   All metrics keys: {list(all_metrics.keys())}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n=== CONCLUSIÓN ===")
    print("Si el endpoint directo tiene function_app pero la ruta semántica no,")
    print("entonces hay un problema en la redirección o en invocar_endpoint_directo_seguro")

if __name__ == "__main__":
    test_compare_routes()