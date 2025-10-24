#!/usr/bin/env python3
"""
Debug script para probar invocar_endpoint_directo
"""

import requests
import json

def test_invocar_endpoint_directo():
    """Simula lo que hace invocar_endpoint_directo"""
    
    base_url = "http://localhost:7071"
    endpoint = "/api/diagnostico-recursos-completo"
    params = {"metricas": "true"}
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-App-Name": "",
        "X-Resource-Group": "boat-rental-app-group",
        "X-Subscription-Id": ""
    }
    
    print("Probando invocar_endpoint_directo simulado...")
    print(f"URL: {base_url}{endpoint}")
    print(f"Params: {params}")
    print(f"Headers: {headers}")
    print()
    
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Simular la estructura que devuelve invocar_endpoint_directo
            resultado = {
                "exito": True,
                "status_code": response.status_code,
                "data": data,
                "endpoint": endpoint,
                "method": "GET",
                "mensaje": f"Endpoint {endpoint} respondio correctamente"
            }
            
            print("Resultado simulado de invocar_endpoint_directo:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            
            # Verificar si tiene métricas
            function_app_metrics = data.get("metricas", {}).get("function_app")
            if function_app_metrics:
                print(f"\nMetricas encontradas: {list(function_app_metrics.keys())}")
            else:
                print("\nNo se encontraron metricas de function_app")
                
        else:
            print(f"Error HTTP: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Excepción: {str(e)}")

if __name__ == "__main__":
    test_invocar_endpoint_directo()