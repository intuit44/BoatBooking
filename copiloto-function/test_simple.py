#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba simplificado para verificar la implementación actual
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"

def test_endpoint(url, endpoint, method="GET", data=None):
    """Prueba un endpoint específico"""
    try:
        full_url = f"{url}{endpoint}"
        print(f"Probando: {method} {full_url}")
        
        if method == "GET":
            response = requests.get(full_url, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, json=data, timeout=10)
        else:
            response = requests.request(method, full_url, json=data, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   OK - Respuesta JSON valida")
                return True, result
            except:
                print(f"   OK - Respuesta texto: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   ERROR: {response.text[:100]}...")
            return False, response.text
            
    except requests.exceptions.Timeout:
        print(f"   TIMEOUT")
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        print(f"   CONNECTION ERROR")
        return False, "Connection Error"
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False, str(e)

def main():
    """Función principal de prueba"""
    print("INICIANDO PRUEBAS DE IMPLEMENTACION")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Endpoints críticos a probar
    endpoints_to_test = [
        {"endpoint": "/api/health", "method": "GET"},
        {"endpoint": "/api/status", "method": "GET"},
        {"endpoint": "/api/copiloto", "method": "GET"},
        {"endpoint": "/api/leer-archivo?ruta=README.md", "method": "GET"},
        {"endpoint": "/api/ejecutar", "method": "POST", "data": {"intencion": "dashboard"}},
        {"endpoint": "/api/hybrid", "method": "POST", "data": {"agent_response": "ping"}},
    ]
    
    results = {"total": 0, "success": 0, "failed": 0, "details": []}
    
    print("\nPROBANDO AZURE FUNCTION APP")
    print("-" * 40)
    
    for test in endpoints_to_test:
        endpoint = test["endpoint"]
            
        results["total"] += 1
        success, response = test_endpoint(
            BASE_URL, 
            endpoint, 
            test["method"], 
            test.get("data")
        )
        
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
            
        results["details"].append({
            "endpoint": endpoint,
            "method": test["method"],
            "success": success,
            "response": str(response)[:200] if response else None
        })
        
        time.sleep(0.5)  # Evitar rate limiting
    
    # Generar reporte
    print("\nREPORTE DE RESULTADOS")
    print("=" * 60)
    
    print(f"\nAzure Function App:")
    print(f"   Total: {results['total']}")
    print(f"   Exitosos: {results['success']}")
    print(f"   Fallidos: {results['failed']}")
    success_rate = (results['success']/results['total']*100) if results['total'] > 0 else 0
    print(f"   Tasa de exito: {success_rate:.1f}%")
    
    # Determinar estado general
    is_healthy = results['success'] >= results['total'] * 0.7  # 70% success rate
    
    print(f"\nESTADO GENERAL:")
    print(f"   Azure: {'SALUDABLE' if is_healthy else 'PROBLEMAS'}")
    
    # Recomendaciones según regla de compatibilidad
    print(f"\nRECOMENDACIONES SEGUN REGLA DE COMPATIBILIDAD:")
    
    if is_healthy:
        print("   OK - La aplicacion Azure esta estable")
        print("   OK - Es seguro proceder con modificaciones")
        print("   NOTA - Crear backup antes de cambios importantes")
    else:
        print("   ATENCION - La aplicacion Azure tiene problemas")
        print("   STOP - NO proceder con modificaciones hasta resolver")
        print("   ACCION - Ejecutar diagnostico completo primero")
    
    # Mostrar detalles de fallos
    if results['failed'] > 0:
        print(f"\nDETALLES DE FALLOS:")
        for detail in results['details']:
            if not detail['success']:
                print(f"   {detail['method']} {detail['endpoint']}: {detail['response'][:100]}")
    
    # Guardar reporte detallado
    report_file = f"test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "health_status": {
                "azure": is_healthy,
                "overall": is_healthy
            },
            "recommendations": {
                "safe_to_modify": is_healthy,
                "backup_recommended": True,
                "diagnostics_needed": not is_healthy
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte detallado guardado en: {report_file}")
    
    return is_healthy

if __name__ == "__main__":
    try:
        is_healthy = main()
        print(f"\nRESULTADO FINAL: {'APTO PARA MODIFICACIONES' if is_healthy else 'NO APTO - REQUIERE DIAGNOSTICO'}")
        exit(0 if is_healthy else 1)
    except KeyboardInterrupt:
        print("\n\nPrueba interrumpida por el usuario")
        exit(2)
    except Exception as e:
        print(f"\nError critico: {str(e)}")
        exit(3)