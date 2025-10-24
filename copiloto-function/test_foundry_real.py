#!/usr/bin/env python3
"""
Test que simula exactamente cómo Foundry interactúa con el sistema
Valida que las métricas reales se devuelvan correctamente
"""

import requests
import json
from datetime import datetime

def test_foundry_real_interaction():
    """Simula la interacción real de Foundry con headers y payload correctos"""
    
    base_url = "http://localhost:7071"
    
    # Headers que usa Foundry
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant", 
        "Content-Type": "application/json"
    }
    
    print(f"[TEST] FOUNDRY REAL INTERACTION - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    
    # Test 1: Simular pregunta de Foundry sobre métricas
    print("\n1. Simulando pregunta de Foundry: '¿Cuántas solicitudes ha procesado la función en las últimas 24 horas?'")
    
    payload = {
        "intencion": "diagnosticar:completo",
        "parametros": {}
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura de métricas que Foundry necesita
            # Buscar métricas tanto en estructura directa como en data.metricas
            metricas = data.get("metricas", {}) or data.get("data", {}).get("metricas", {})
            function_app_metrics = metricas.get("function_app", {})
            
            print(f"   Métricas encontradas: {list(metricas.keys())}")
            
            # Verificar métricas específicas que Foundry busca
            required_metrics = ["FunctionExecutionCount", "Requests", "Http2xx", "Http5xx"]
            found_metrics = []
            
            for metric in required_metrics:
                if metric in function_app_metrics:
                    metric_data = function_app_metrics[metric]
                    if isinstance(metric_data, dict) and "total" in metric_data:
                        found_metrics.append(f"{metric}: {metric_data['total']}")
                    else:
                        found_metrics.append(f"{metric}: {metric_data}")
            
            if found_metrics:
                print(f"   [OK] MÉTRICAS ENCONTRADAS:")
                for metric in found_metrics:
                    print(f"        • {metric}")
                result = "PASS"
            else:
                print(f"   [FAIL] NO SE ENCONTRARON MÉTRICAS UTILIZABLES")
                print(f"        Estructura actual: {json.dumps(metricas, indent=2)[:300]}...")
                result = "FAIL"
                
        else:
            print(f"   [FAIL] ERROR HTTP {response.status_code}")
            result = "FAIL"
            
    except Exception as e:
        print(f"   [FAIL] ERROR: {str(e)}")
        result = "FAIL"
    
    # Test 2: Verificar endpoint directo para comparación
    print("\n2. Verificando endpoint directo /api/diagnostico-recursos-completo")
    
    try:
        response = requests.get(
            f"{base_url}/api/diagnostico-recursos-completo?metricas=true",
            headers=headers,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            metricas = data.get("metricas", {})
            
            if metricas:
                print(f"   [OK] ENDPOINT DIRECTO TIENE MÉTRICAS")
                print(f"        Claves: {list(metricas.keys())}")
            else:
                print(f"   [WARN] ENDPOINT DIRECTO SIN MÉTRICAS")
                
        else:
            print(f"   [FAIL] ERROR HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   [FAIL] ERROR: {str(e)}")
    
    # Test 3: Verificar que obtener_metricas_function_app se esté llamando
    print("\n3. Verificando llamada a obtener_metricas_function_app")
    
    payload_with_metrics = {
        "intencion": "verificar:metricas",
        "parametros": {"metricas": True}
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar",
            headers=headers,
            json=payload_with_metrics,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Buscar evidencia de que se llamó obtener_metricas_function_app
            # Buscar métricas tanto en estructura directa como en data.metricas
            metricas_test3 = data.get("metricas", {}) or data.get("data", {}).get("metricas", {})
            if "function_app" in metricas_test3:
                fa_metrics = metricas_test3["function_app"]
                
                # Verificar métricas específicas de Function App
                execution_metrics = ["FunctionExecutionCount", "FunctionExecutionUnits"]
                http_metrics = ["Requests", "Http2xx", "Http4xx", "Http5xx"]
                
                execution_found = any(m in fa_metrics for m in execution_metrics)
                http_found = any(m in fa_metrics for m in http_metrics)
                
                if execution_found or http_found:
                    print(f"   [OK] MÉTRICAS DE FUNCTION APP ENCONTRADAS")
                    print(f"        Execution metrics: {execution_found}")
                    print(f"        HTTP metrics: {http_found}")
                else:
                    print(f"   [WARN] MÉTRICAS PRESENTES PERO NO LAS ESPERADAS")
                    print(f"        Disponibles: {list(fa_metrics.keys())}")
            else:
                print(f"   [FAIL] NO SE ENCONTRARON MÉTRICAS DE FUNCTION APP")
                
    except Exception as e:
        print(f"   [FAIL] ERROR: {str(e)}")
    
    print("\n" + "=" * 70)
    print("[SUMMARY] DIAGNÓSTICO DEL PROBLEMA")
    print("=" * 70)
    
    if result == "PASS":
        print("[SUCCESS] El sistema devuelve métricas correctamente a Foundry")
    else:
        print("[PROBLEM] Foundry no puede obtener métricas utilizables")
        print("POSIBLES CAUSAS:")
        print("1. obtener_metricas_function_app() no se está llamando")
        print("2. Las métricas no se están embebiendo en diagnostico['metricas']['function_app']")
        print("3. La estructura de respuesta no es la que Foundry espera")
        print("4. Timeout o permisos insuficientes en Azure SDK")
    
    return result

if __name__ == "__main__":
    test_foundry_real_interaction()