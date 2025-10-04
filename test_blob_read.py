#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad dual local/Blob
"""
import os
import json
import requests
from urllib.parse import urlencode

def test_leer_archivo_endpoint():
    """Prueba el endpoint leer-archivo con diferentes rutas"""
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    endpoint = "/api/leer-archivo"
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Ruta Blob completa",
            "params": {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
        },
        {
            "name": "Solo nombre archivo",
            "params": {"ruta": "function_app.py"}
        },
        {
            "name": "Ruta local absoluta",
            "params": {"ruta": "c:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py"}
        },
        {
            "name": "Sin parámetros",
            "params": {}
        }
    ]
    
    print("[TEST] Iniciando pruebas del endpoint leer-archivo...")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[PRUEBA {i}] {test['name']}")
        print(f"   Parametros: {test['params']}")
        
        try:
            # Construir URL con parámetros
            url = f"{base_url}{endpoint}"
            if test['params']:
                url += "?" + urlencode(test['params'])
            
            print(f"   URL: {url}")
            
            # Hacer request
            response = requests.get(
                url,
                headers={
                    "User-Agent": "azure-agents",
                    "Accept": "application/json"
                },
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            # Procesar respuesta
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("exito"):
                        print(f"   [OK] Exito: {data.get('mensaje', 'Sin mensaje')}")
                        if "contenido" in data:
                            content_preview = data["contenido"][:100] + "..." if len(data["contenido"]) > 100 else data["contenido"]
                            print(f"   [CONTENT] Contenido: {content_preview}")
                        print(f"   [SOURCE] Origen: {data.get('origen', 'No especificado')}")
                    else:
                        print(f"   [ERROR] Error: {data.get('error', 'Error desconocido')}")
                        if "detalles" in data:
                            print(f"   [DETAILS] Detalles: {data['detalles']}")
                except json.JSONDecodeError:
                    print(f"   [TEXT] Respuesta texto: {response.text[:200]}...")
            else:
                print(f"   [HTTP_ERROR] Error HTTP: {response.status_code}")
                print(f"   [RESPONSE] Respuesta: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   [TIMEOUT] Timeout despues de 30s")
        except requests.exceptions.ConnectionError:
            print(f"   [CONNECTION] Error de conexion")
        except Exception as e:
            print(f"   [UNEXPECTED] Error inesperado: {str(e)}")
        
        print("-" * 40)
    
    print("\n[DONE] Pruebas completadas")

if __name__ == "__main__":
    test_leer_archivo_endpoint()