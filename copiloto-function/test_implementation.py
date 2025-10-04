#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la implementación actual de la Function App
Según la regla de compatibilidad, necesitamos verificar el estado antes de modificar
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"
LOCAL_URL = "http://localhost:7071"

def test_endpoint(url, endpoint, method="GET", data=None):
    """Prueba un endpoint específico"""
    try:
        full_url = f"{url}{endpoint}"
        print(f"🔍 Probando: {method} {full_url}")
        
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
                print(f"   ✅ Respuesta JSON válida")
                return True, result
            except:
                print(f"   ✅ Respuesta texto: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   ❌ Error: {response.text[:100]}...")
            return False, response.text
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout")
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Error de conexión")
        return False, "Connection Error"
    except Exception as e:
        print(f"   💥 Error: {str(e)}")
        return False, str(e)

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de implementación")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Endpoints críticos a probar
    endpoints_to_test = [
        {"endpoint": "/api/health", "method": "GET"},
        {"endpoint": "/api/status", "method": "GET"},
        {"endpoint": "/api/copiloto", "method": "GET"},
        {"endpoint": "/api/leer-archivo", "method": "GET", "params": "?ruta=README.md"},
        {"endpoint": "/api/ejecutar", "method": "POST", "data": {"intencion": "dashboard"}},
        {"endpoint": "/api/hybrid", "method": "POST", "data": {"agent_response": "ping"}},
    ]
    
    results = {
        "azure": {"total": 0, "success": 0, "failed": 0, "details": []},
        "local": {"total": 0, "success": 0, "failed": 0, "details": []}
    }
    
    # Probar Azure primero
    print("\n🌐 PROBANDO AZURE FUNCTION APP")
    print("-" * 40)
    
    for test in endpoints_to_test:
        endpoint = test["endpoint"]
        if "params" in test:
            endpoint += test["params"]
            
        results["azure"]["total"] += 1
        success, response = test_endpoint(
            BASE_URL, 
            endpoint, 
            test["method"], 
            test.get("data")
        )
        
        if success:
            results["azure"]["success"] += 1
        else:
            results["azure"]["failed"] += 1
            
        results["azure"]["details"].append({
            "endpoint": endpoint,
            "method": test["method"],
            "success": success,
            "response": str(response)[:200] if response else None
        })
        
        time.sleep(0.5)  # Evitar rate limiting
    
    # Probar local si está disponible
    print("\n🏠 PROBANDO FUNCIÓN LOCAL (si está disponible)")
    print("-" * 40)
    
    for test in endpoints_to_test:
        endpoint = test["endpoint"]
        if "params" in test:
            endpoint += test["params"]
            
        results["local"]["total"] += 1
        success, response = test_endpoint(
            LOCAL_URL, 
            endpoint, 
            test["method"], 
            test.get("data")
        )
        
        if success:
            results["local"]["success"] += 1
        else:
            results["local"]["failed"] += 1
            
        results["local"]["details"].append({
            "endpoint": endpoint,
            "method": test["method"],
            "success": success,
            "response": str(response)[:200] if response else None
        })
        
        time.sleep(0.5)
    
    # Generar reporte
    print("\n📊 REPORTE DE RESULTADOS")
    print("=" * 60)
    
    print(f"\n🌐 Azure Function App:")
    print(f"   Total: {results['azure']['total']}")
    print(f"   Exitosos: {results['azure']['success']}")
    print(f"   Fallidos: {results['azure']['failed']}")
    print(f"   Tasa de éxito: {(results['azure']['success']/results['azure']['total']*100):.1f}%")
    
    print(f"\n🏠 Función Local:")
    print(f"   Total: {results['local']['total']}")
    print(f"   Exitosos: {results['local']['success']}")
    print(f"   Fallidos: {results['local']['failed']}")
    print(f"   Tasa de éxito: {(results['local']['success']/results['local']['total']*100):.1f}%")
    
    # Determinar estado general
    azure_health = results['azure']['success'] >= results['azure']['total'] * 0.7  # 70% success rate
    local_health = results['local']['success'] >= results['local']['total'] * 0.5   # 50% success rate (más tolerante)
    
    print(f"\n🎯 ESTADO GENERAL:")
    print(f"   Azure: {'✅ SALUDABLE' if azure_health else '❌ PROBLEMAS'}")
    print(f"   Local: {'✅ SALUDABLE' if local_health else '❌ PROBLEMAS'}")
    
    # Recomendaciones según regla de compatibilidad
    print(f"\n📋 RECOMENDACIONES SEGÚN REGLA DE COMPATIBILIDAD:")
    
    if azure_health:
        print("   ✅ La aplicación Azure está estable")
        print("   ✅ Es seguro proceder con modificaciones")
        print("   💡 Crear backup antes de cambios importantes")
    else:
        print("   ⚠️  La aplicación Azure tiene problemas")
        print("   🛑 NO proceder con modificaciones hasta resolver")
        print("   🔧 Ejecutar diagnóstico completo primero")
    
    if not local_health and results['local']['failed'] == results['local']['total']:
        print("   ℹ️  Función local no disponible (normal en producción)")
    
    # Guardar reporte detallado
    report_file = f"test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "health_status": {
                "azure": azure_health,
                "local": local_health,
                "overall": azure_health  # Azure es crítico
            },
            "recommendations": {
                "safe_to_modify": azure_health,
                "backup_recommended": True,
                "diagnostics_needed": not azure_health
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte detallado guardado en: {report_file}")
    
    return azure_health

if __name__ == "__main__":
    try:
        is_healthy = main()
        exit(0 if is_healthy else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Prueba interrumpida por el usuario")
        exit(2)
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        exit(3)