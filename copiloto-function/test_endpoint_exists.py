#!/usr/bin/env python3
"""
Verificar si el endpoint diagnostico-recursos-completo existe
"""

import requests
import json

def test_endpoint_exists():
    """Verifica endpoints disponibles"""
    
    base_url = "http://localhost:7071"
    
    # 1. Verificar status general
    print("[CHECK] Verificando endpoints disponibles...")
    
    try:
        response = requests.get(f"{base_url}/api/status", timeout=30)
        print(f"Status endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'endpoints' in data.get('estado', {}):
                endpoints = data['estado']['endpoints']
                print(f"Endpoints disponibles: {len(endpoints)}")
                
                # Buscar el endpoint de diagnóstico
                diagnostico_endpoints = [ep for ep in endpoints if 'diagnostico' in ep.lower()]
                print(f"Endpoints de diagnóstico: {diagnostico_endpoints}")
                
    except Exception as e:
        print(f"Error verificando status: {e}")
    
    # 2. Probar endpoints de diagnóstico específicos
    endpoints_to_test = [
        "/api/diagnostico-recursos",
        "/api/diagnostico-recursos-completo", 
        "/api/diagnostico"
    ]
    
    print(f"\n[TEST] Probando endpoints específicos...")
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            print(f"{endpoint}: {response.status_code}")
            
            if response.status_code == 500:
                # Mostrar el error específico
                try:
                    error_data = response.json()
                    cause = error_data.get('cause', 'Unknown')
                    print(f"  Error: {cause}")
                except:
                    print(f"  Error: {response.text[:100]}...")
                    
        except requests.exceptions.ConnectionError:
            print(f"{endpoint}: Connection Error")
        except Exception as e:
            print(f"{endpoint}: {e}")
    
    # 3. Verificar redirección en /api/ejecutar
    print(f"\n[REDIRECT] Verificando redirección en /api/ejecutar...")
    
    redirect_tests = [
        {"intencion": "diagnostico"},
        {"intencion": "diagnosticar:completo"},
        {"intencion": "verificar:metricas"}
    ]
    
    for test in redirect_tests:
        try:
            response = requests.post(
                f"{base_url}/api/ejecutar", 
                json=test, 
                timeout=30
            )
            print(f"Intencion '{test['intencion']}': {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                exito = data.get('exito', False)
                mensaje = data.get('mensaje', '')[:100]
                print(f"  Exito: {exito}, Mensaje: {mensaje}...")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_endpoint_exists()