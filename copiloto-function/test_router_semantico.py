#!/usr/bin/env python3
"""
Test del router semántico para validar redirección correcta
"""

import requests
import json
from datetime import datetime

def test_router_semantico():
    """Prueba las redirecciones del router semántico"""
    
    base_url = "http://localhost:7071"  # Local
    # base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"  # Azure
    
    # Casos de prueba para verificar redirección
    test_cases = [
        {
            "nombre": "Verificar métricas - directo",
            "endpoint": "/api/ejecutar",
            "payload": {
                "intencion": "verificar:metricas",
                "parametros": {}
            },
            "esperado": "diagnostico-recursos-completo"
        },
        {
            "nombre": "Diagnóstico - directo", 
            "endpoint": "/api/ejecutar",
            "payload": {
                "intencion": "diagnostico",
                "parametros": {}
            },
            "esperado": "diagnostico-recursos-completo"
        },
        {
            "nombre": "Diagnóstico completo",
            "endpoint": "/api/ejecutar", 
            "payload": {
                "intencion": "diagnosticar:completo",
                "parametros": {}
            },
            "esperado": "diagnostico-recursos-completo"
        },
        {
            "nombre": "Endpoint directo",
            "endpoint": "/api/diagnostico-recursos-completo",
            "payload": {},
            "method": "GET",
            "esperado": "diagnostico_completado"
        }
    ]
    
    print(f"[TEST] ROUTER SEMANTICO - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    resultados = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['nombre']}")
        print(f"   Endpoint: {test['endpoint']}")
        
        try:
            method = test.get('method', 'POST')
            url = f"{base_url}{test['endpoint']}"
            
            if method == 'GET':
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json=test['payload'], timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verificar si fue redirigido correctamente
                    mensaje = data.get('mensaje', '')
                    
                    if test['esperado'] in mensaje.lower() or 'diagnostico' in mensaje.lower():
                        print(f"   [OK] CORRECTO - Redirigido a diagnostico")
                        resultado = "PASS"
                    elif 'script' in mensaje.lower() or 'ejecutar' in mensaje.lower():
                        print(f"   [FAIL] ERROR - Intento ejecutar script")
                        resultado = "FAIL - Script execution"
                    else:
                        print(f"   [WARN] INCIERTO - Respuesta: {mensaje[:100]}...")
                        resultado = "UNCERTAIN"
                    
                    resultados.append({
                        "test": test['nombre'],
                        "resultado": resultado,
                        "status": response.status_code,
                        "mensaje": mensaje[:200]
                    })
                    
                except json.JSONDecodeError:
                    print(f"   [FAIL] ERROR - Respuesta no es JSON valido")
                    resultados.append({
                        "test": test['nombre'], 
                        "resultado": "FAIL - Invalid JSON",
                        "status": response.status_code
                    })
            else:
                print(f"   [FAIL] ERROR - Status {response.status_code}")
                resultados.append({
                    "test": test['nombre'],
                    "resultado": f"FAIL - HTTP {response.status_code}",
                    "status": response.status_code
                })
                
        except requests.exceptions.ConnectionError:
            print(f"   [FAIL] ERROR - No se pudo conectar (Function App corriendo?)")
            resultados.append({
                "test": test['nombre'],
                "resultado": "FAIL - Connection Error",
                "status": 0
            })
        except Exception as e:
            print(f"   [FAIL] ERROR - {str(e)}")
            resultados.append({
                "test": test['nombre'],
                "resultado": f"FAIL - {str(e)}",
                "status": 0
            })
    
    # Resumen final
    print("\n" + "=" * 60)
    print("[SUMMARY] RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for r in resultados if r['resultado'] == 'PASS')
    total = len(resultados)
    
    for resultado in resultados:
        status_icon = "[OK]" if resultado['resultado'] == 'PASS' else "[FAIL]"
        print(f"{status_icon} {resultado['test']}: {resultado['resultado']}")
    
    print(f"\n[RESULT] FINAL: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("[SUCCESS] TODAS LAS PRUEBAS PASARON! Router semantico funcionando correctamente")
    else:
        print("[WARNING] Algunas pruebas fallaron. Revisar configuracion del router")
    
    return resultados

if __name__ == "__main__":
    test_router_semantico()