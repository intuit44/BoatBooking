#!/usr/bin/env python3
"""
Test detallado del router semántico con análisis de respuestas
"""

import requests
import json
from datetime import datetime

def test_detailed_router():
    """Prueba detallada con análisis de respuestas"""
    
    base_url = "http://localhost:7071"
    
    test_cases = [
        {
            "nombre": "Diagnóstico directo",
            "endpoint": "/api/ejecutar",
            "payload": {"intencion": "diagnostico", "parametros": {}}
        },
        {
            "nombre": "Verificar métricas",
            "endpoint": "/api/ejecutar", 
            "payload": {"intencion": "verificar:metricas", "parametros": {}}
        },
        {
            "nombre": "Diagnóstico completo",
            "endpoint": "/api/ejecutar",
            "payload": {"intencion": "diagnosticar:completo", "parametros": {}}
        }
    ]
    
    print("[DETAILED TEST] Análisis detallado del router")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['nombre']}")
        print(f"   Payload: {test['payload']}")
        
        try:
            url = f"{base_url}{test['endpoint']}"
            response = requests.post(url, json=test['payload'], timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Mostrar campos clave de la respuesta
                    print(f"   Exito: {data.get('exito', 'N/A')}")
                    
                    mensaje = data.get('mensaje', '')
                    if mensaje:
                        print(f"   Mensaje: {mensaje[:150]}...")
                    
                    # Verificar si hay información de endpoint usado
                    if 'endpoint' in data:
                        print(f"   Endpoint usado: {data['endpoint']}")
                    
                    # Verificar si menciona diagnóstico
                    if any(word in mensaje.lower() for word in ['diagnostico', 'recursos', 'metricas']):
                        print(f"   [OK] Respuesta relacionada con diagnóstico")
                    elif any(word in mensaje.lower() for word in ['script', 'ejecutar', 'comando']):
                        print(f"   [WARN] Respuesta relacionada con scripts")
                    else:
                        print(f"   [INFO] Respuesta genérica")
                        
                except json.JSONDecodeError as e:
                    print(f"   [ERROR] JSON inválido: {e}")
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print(f"   [ERROR] HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   [ERROR] Exception: {e}")
    
    # Test directo del endpoint
    print(f"\n4. Test directo del endpoint")
    try:
        url = f"{base_url}/api/diagnostico-recursos-completo"
        response = requests.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Error response: {response.text[:200]}...")
        else:
            data = response.json()
            print(f"   [OK] Endpoint directo funciona")
            if 'mensaje' in data:
                print(f"   Mensaje: {data['mensaje'][:100]}...")
                
    except Exception as e:
        print(f"   [ERROR] {e}")

if __name__ == "__main__":
    test_detailed_router()