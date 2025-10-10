#!/usr/bin/env python3
"""
Script simple para validar schema OpenAPI para Agent898
"""
import json
import re
import requests
import sys

def validate_openapi_version(openapi_version):
    """Valida que la version OpenAPI cumpla con el patron de Agent898"""
    pattern = r"^3\.1\.\d+(-.+)?$"
    return re.match(pattern, openapi_version) is not None

def test_schema_access():
    """Prueba acceso al schema desde ambas rutas"""
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    # Probar ambas rutas
    routes = ["/openapi.yaml", "/api/openapi.yaml"]
    
    for route in routes:
        print(f"\nProbando ruta: {route}")
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    content = response.text
                    if content.startswith('{'):
                        # Es JSON
                        schema = json.loads(content)
                        openapi_version = schema.get("openapi", "unknown")
                        print(f"OpenAPI Version: {openapi_version}")
                        
                        # Validar version
                        if validate_openapi_version(openapi_version):
                            print(f"Version VALIDA para Agent898")
                            
                            # Contar endpoints
                            paths = schema.get("paths", {})
                            print(f"Endpoints disponibles: {len(paths)}")
                            
                            return True, schema
                        else:
                            print(f"Version INVALIDA para Agent898")
                            print(f"Patron requerido: ^3\\.1\\.\\d+(-.+)?$")
                    else:
                        print(f"Contenido YAML detectado")
                        
                except Exception as e:
                    print(f"Error parseando contenido: {e}")
            else:
                print(f"Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"Error de conexion: {e}")
    
    return False, None

def test_endpoint_call():
    """Prueba llamar a un endpoint simple"""
    print(f"\nProbando endpoint /api/status...")
    
    try:
        response = requests.get("https://copiloto-semantico-func-us2.azurewebsites.net/api/status", timeout=10)
        print(f"/api/status -> {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta exitosa:")
            print(f"  - Copiloto: {data.get('copiloto', 'unknown')}")
            print(f"  - Ambiente: {data.get('ambiente', 'unknown')}")
            print(f"  - Ready: {data.get('ready', False)}")
            return True
        else:
            print(f"Error en endpoint: {response.status_code}")
            
    except Exception as e:
        print(f"Error llamando endpoint: {e}")
    
    return False

def main():
    print("Simulando validacion de Agent898 para OpenAPI Schema")
    print("=" * 60)
    
    # Paso 1: Validar acceso al schema
    success, schema = test_schema_access()
    
    if success:
        print(f"\nSchema accesible y valido para Agent898")
        
        # Paso 2: Probar endpoint
        endpoint_success = test_endpoint_call()
        
        if endpoint_success:
            print(f"\nAgent898 deberia poder conectarse correctamente!")
            return 0
        else:
            print(f"\nSchema valido pero endpoints con problemas")
            return 1
    else:
        print(f"\nProblemas con el schema OpenAPI")
        print(f"\nPosibles soluciones:")
        print(f"  1. Verificar que /openapi.yaml este disponible")
        print(f"  2. Confirmar version OpenAPI 3.1.x")
        print(f"  3. Validar formato JSON/YAML")
        return 1

if __name__ == "__main__":
    sys.exit(main())