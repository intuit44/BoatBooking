#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico de compatibilidad con Azure para el endpoint /api/escribir-archivo
Valida que las implementaciones funcionen correctamente en el entorno Azure.
"""

import json
import requests
import time
import sys
from datetime import datetime

# URLs de testing
LOCAL_URL = "http://localhost:7071"
AZURE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"

def test_azure_specific_scenarios():
    """Prueba escenarios específicos de Azure"""
    print("☁️ TESTING AZURE-SPECIFIC SCENARIOS")
    
    scenarios = [
        {
            "name": "Archivo con caracteres especiales",
            "data": {
                "ruta": "test_especiales.py",
                "contenido": "# Prueba con ñ, acentos: café, niño\nprint('Funciona en Azure')"
            }
        },
        {
            "name": "Archivo grande (>1KB)",
            "data": {
                "ruta": "test_large.py",
                "contenido": "# " + "x" * 2000 + "\nprint('Large file test')"
            }
        },
        {
            "name": "Múltiples imports con ErrorHandler",
            "data": {
                "ruta": "test_multiple_imports.py",
                "contenido": """import os
import sys
from error_handler import ErrorHandler
import json

def test():
    return True
"""
            }
        },
        {
            "name": "Archivo JSON válido",
            "data": {
                "ruta": "test_config.json",
                "contenido": '{"test": true, "azure": "compatible", "encoding": "utf-8"}'
            }
        }
    ]
    
    results = []
    for scenario in scenarios:
        print(f"  Testing: {scenario['name']}")
        
        # Probar en Azure
        try:
            response = requests.post(
                f"{AZURE_URL}/api/escribir-archivo", 
                json=scenario["data"], 
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("exito"):
                    print(f"    ✅ AZURE PASS")
                    results.append({
                        "scenario": scenario["name"],
                        "azure": "PASS",
                        "details": result
                    })
                else:
                    print(f"    ❌ AZURE FAIL: {result.get('error', 'Unknown error')}")
                    results.append({
                        "scenario": scenario["name"],
                        "azure": "FAIL",
                        "error": result.get('error')
                    })
            else:
                print(f"    ❌ AZURE HTTP {response.status_code}")
                results.append({
                    "scenario": scenario["name"],
                    "azure": "HTTP_ERROR",
                    "status_code": response.status_code
                })
                
        except requests.exceptions.Timeout:
            print(f"    ⏰ AZURE TIMEOUT")
            results.append({
                "scenario": scenario["name"],
                "azure": "TIMEOUT"
            })
        except Exception as e:
            print(f"    💥 AZURE ERROR: {e}")
            results.append({
                "scenario": scenario["name"],
                "azure": "ERROR",
                "error": str(e)
            })
    
    return results

def test_performance_azure():
    """Prueba rendimiento en Azure"""
    print("\n⚡ TESTING AZURE PERFORMANCE")
    
    test_data = {
        "ruta": "perf_test.py",
        "contenido": "print('Performance test')"
    }
    
    times = []
    for i in range(3):
        print(f"  Intento {i+1}/3...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{AZURE_URL}/api/escribir-archivo",
                json=test_data,
                timeout=30
            )
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            
            if response.status_code == 200:
                print(f"    ✅ {duration:.2f}s")
            else:
                print(f"    ❌ HTTP {response.status_code} in {duration:.2f}s")
                
        except Exception as e:
            print(f"    💥 ERROR: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n  📊 Tiempo promedio: {avg_time:.2f}s")
        print(f"  📊 Tiempo mínimo: {min(times):.2f}s")
        print(f"  📊 Tiempo máximo: {max(times):.2f}s")
        
        return {
            "average": avg_time,
            "min": min(times),
            "max": max(times),
            "samples": len(times)
        }
    
    return {"error": "No se pudieron obtener mediciones"}

def test_error_handling_azure():
    """Prueba manejo de errores en Azure"""
    print("\n🚨 TESTING AZURE ERROR HANDLING")
    
    error_scenarios = [
        {
            "name": "Ruta vacía",
            "data": {"ruta": "", "contenido": "test"}
        },
        {
            "name": "Contenido None",
            "data": {"ruta": "test.py", "contenido": None}
        },
        {
            "name": "JSON malformado (simulado)",
            "data": {"ruta": "test.py", "contenido": "print('test')"}
        },
        {
            "name": "Sintaxis Python inválida",
            "data": {"ruta": "bad.py", "contenido": "def broken(\nreturn"}
        }
    ]
    
    results = []
    for scenario in error_scenarios:
        print(f"  Testing: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{AZURE_URL}/api/escribir-archivo",
                json=scenario["data"],
                timeout=20
            )
            
            result = response.json()
            
            # Para errores, esperamos que el sistema los maneje gracefully
            if response.status_code in [200, 400] and "error" in result:
                print(f"    ✅ Error manejado correctamente")
                results.append({
                    "scenario": scenario["name"],
                    "status": "HANDLED",
                    "error_message": result.get("error", "")[:100]
                })
            elif result.get("exito"):
                print(f"    ⚠️ Debería haber fallado pero pasó")
                results.append({
                    "scenario": scenario["name"],
                    "status": "UNEXPECTED_SUCCESS"
                })
            else:
                print(f"    ❌ Error no manejado correctamente")
                results.append({
                    "scenario": scenario["name"],
                    "status": "UNHANDLED"
                })
                
        except Exception as e:
            print(f"    💥 Exception: {e}")
            results.append({
                "scenario": scenario["name"],
                "status": "EXCEPTION",
                "error": str(e)
            })
    
    return results

def test_memory_phases_azure():
    """Prueba las 3 fases específicamente en Azure"""
    print("\n🧠 TESTING 3 PHASES IN AZURE")
    
    # Fase 1: Validación previa
    print("  FASE 1: Validación previa")
    fase1_data = {
        "ruta": "fase1_test.py",
        "contenido": "def test():\n    return 'fase1'"
    }
    
    try:
        response = requests.post(f"{AZURE_URL}/api/escribir-archivo", json=fase1_data, timeout=20)
        result = response.json()
        fase1_ok = result.get("exito") and any("Validación sintáctica Python exitosa" in adv for adv in result.get("advertencias", []))
        print(f"    {'✅' if fase1_ok else '❌'} Fase 1")
    except Exception as e:
        print(f"    💥 Fase 1 ERROR: {e}")
        fase1_ok = False
    
    # Fase 2: Inyección delimitada
    print("  FASE 2: Inyección delimitada")
    fase2_data = {
        "ruta": "fase2_test.py",
        "contenido": "from error_handler import ErrorHandler\n\ndef test():\n    return 'fase2'"
    }
    
    try:
        response = requests.post(f"{AZURE_URL}/api/escribir-archivo", json=fase2_data, timeout=20)
        result = response.json()
        fase2_ok = result.get("exito") and any("inyección ErrorHandler aplicado" in adv for adv in result.get("advertencias", []))
        print(f"    {'✅' if fase2_ok else '❌'} Fase 2")
    except Exception as e:
        print(f"    💥 Fase 2 ERROR: {e}")
        fase2_ok = False
    
    # Fase 3: Respaldo automático (requiere archivo existente)
    print("  FASE 3: Respaldo automático")
    try:
        # Crear archivo inicial
        initial_data = {"ruta": "fase3_test.py", "contenido": "# Initial version"}
        requests.post(f"{AZURE_URL}/api/escribir-archivo", json=initial_data, timeout=20)
        
        time.sleep(1)
        
        # Modificar archivo
        modified_data = {"ruta": "fase3_test.py", "contenido": "# Modified version"}
        response = requests.post(f"{AZURE_URL}/api/escribir-archivo", json=modified_data, timeout=20)
        result = response.json()
        
        fase3_ok = result.get("exito") and any("Respaldo creado" in adv for adv in result.get("advertencias", []))
        print(f"    {'✅' if fase3_ok else '❌'} Fase 3")
    except Exception as e:
        print(f"    💥 Fase 3 ERROR: {e}")
        fase3_ok = False
    
    return {
        "fase1": fase1_ok,
        "fase2": fase2_ok,
        "fase3": fase3_ok,
        "all_phases_ok": fase1_ok and fase2_ok and fase3_ok
    }

def main():
    """Ejecuta todas las pruebas de compatibilidad con Azure"""
    print("🚀 AZURE COMPATIBILITY TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Azure URL: {AZURE_URL}")
    
    # Verificar conectividad básica
    print("\n🔗 Verificando conectividad con Azure...")
    try:
        response = requests.get(f"{AZURE_URL}/api/status", timeout=10)
        if response.status_code == 200:
            print("    ✅ Azure Function App accesible")
        else:
            print(f"    ❌ Azure responde con HTTP {response.status_code}")
            return 1
    except Exception as e:
        print(f"    💥 No se puede conectar con Azure: {e}")
        return 1
    
    # Ejecutar pruebas
    results = {}
    
    results["scenarios"] = test_azure_specific_scenarios()
    results["performance"] = test_performance_azure()
    results["error_handling"] = test_error_handling_azure()
    results["phases"] = test_memory_phases_azure()
    
    # Generar reporte
    print("\n" + "="*60)
    print("📊 AZURE COMPATIBILITY REPORT")
    print("="*60)
    
    # Contar éxitos
    scenario_passes = sum(1 for s in results["scenarios"] if s.get("azure") == "PASS")
    total_scenarios = len(results["scenarios"])
    
    error_handled = sum(1 for e in results["error_handling"] if e.get("status") == "HANDLED")
    total_errors = len(results["error_handling"])
    
    phases_ok = results["phases"]["all_phases_ok"]
    
    print(f"Escenarios Azure: {scenario_passes}/{total_scenarios}")
    print(f"Manejo de errores: {error_handled}/{total_errors}")
    print(f"3 Fases implementadas: {'✅' if phases_ok else '❌'}")
    
    if results["performance"].get("average"):
        print(f"Rendimiento promedio: {results['performance']['average']:.2f}s")
    
    # Guardar reporte
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "azure_url": AZURE_URL,
        "summary": {
            "scenarios_passed": scenario_passes,
            "total_scenarios": total_scenarios,
            "errors_handled": error_handled,
            "total_error_tests": total_errors,
            "phases_working": phases_ok,
            "performance": results["performance"]
        },
        "details": results
    }
    
    with open("azure_compatibility_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado en: azure_compatibility_report.json")
    
    # Determinar éxito general
    success_rate = (scenario_passes + error_handled) / (total_scenarios + total_errors)
    
    if success_rate >= 0.8 and phases_ok:
        print("\n🎉 AZURE COMPATIBILITY: EXCELENTE")
        return 0
    elif success_rate >= 0.6:
        print("\n⚠️ AZURE COMPATIBILITY: ACEPTABLE (revisar fallos)")
        return 0
    else:
        print("\n❌ AZURE COMPATIBILITY: PROBLEMAS DETECTADOS")
        return 1

if __name__ == "__main__":
    exit(main())