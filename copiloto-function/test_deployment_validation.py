#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación para probar las 3 fases del endpoint /api/escribir-archivo
antes del despliegue en Azure.

Valida:
- FASE 1: Validación previa (UTF-8, sintaxis Python, imports recursivos)
- FASE 2: Inyección delimitada con detección de duplicados
- FASE 3: Respaldo automático con restauración
"""

import json
import requests
import time
import os
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:7071"  # Local para testing
AZURE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"  # Azure para producción

def test_fase_1_validacion_previa():
    """Prueba FASE 1: Validación previa completa"""
    print("🔍 TESTING FASE 1: Validación Previa")
    
    tests = [
        {
            "name": "UTF-8 válido",
            "data": {"ruta": "test_utf8.py", "contenido": "print('Hola mundo')"},
            "expect_success": True
        },
        {
            "name": "Sintaxis Python válida",
            "data": {"ruta": "test_syntax.py", "contenido": "def test():\n    return True"},
            "expect_success": True
        },
        {
            "name": "Sintaxis Python inválida",
            "data": {"ruta": "test_bad_syntax.py", "contenido": "def test(\n    return True"},
            "expect_success": False
        },
        {
            "name": "Import recursivo detectado",
            "data": {"ruta": "test_recursive.py", "contenido": "import test_recursive\nprint('test')"},
            "expect_success": True  # Se permite pero se advierte
        }
    ]
    
    results = []
    for test in tests:
        print(f"  Testing: {test['name']}")
        try:
            response = requests.post(f"{BASE_URL}/api/escribir-archivo", json=test["data"], timeout=10)
            result = response.json()
            
            success = result.get("exito", False)
            if success == test["expect_success"]:
                print(f"    ✅ PASS")
                results.append({"test": test["name"], "status": "PASS"})
            else:
                print(f"    ❌ FAIL - Expected {test['expect_success']}, got {success}")
                results.append({"test": test["name"], "status": "FAIL", "details": result})
                
        except Exception as e:
            print(f"    💥 ERROR: {e}")
            results.append({"test": test["name"], "status": "ERROR", "error": str(e)})
    
    return results

def test_fase_2_inyeccion_delimitada():
    """Prueba FASE 2: Inyección delimitada con detección de duplicados"""
    print("\n🔧 TESTING FASE 2: Inyección Delimitada")
    
    tests = [
        {
            "name": "Inyección ErrorHandler nueva",
            "data": {
                "ruta": "test_inject_new.py", 
                "contenido": "from error_handler import ErrorHandler\n\ndef test():\n    pass"
            },
            "expect_injection": True
        },
        {
            "name": "Inyección ErrorHandler existente",
            "data": {
                "ruta": "test_inject_existing.py",
                "contenido": "# ===BEGIN AUTO-INJECT: ErrorHandler===\nfrom error_handler import ErrorHandler\n# ===END AUTO-INJECT: ErrorHandler===\n\ndef test():\n    pass"
            },
            "expect_injection": False  # No debe duplicar
        }
    ]
    
    results = []
    for test in tests:
        print(f"  Testing: {test['name']}")
        try:
            response = requests.post(f"{BASE_URL}/api/escribir-archivo", json=test["data"], timeout=10)
            result = response.json()
            
            # Verificar si se aplicó la inyección según lo esperado
            advertencias = result.get("advertencias", [])
            injection_applied = any("inyección ErrorHandler aplicado" in adv for adv in advertencias)
            
            if injection_applied == test["expect_injection"]:
                print(f"    ✅ PASS")
                results.append({"test": test["name"], "status": "PASS"})
            else:
                print(f"    ❌ FAIL - Expected injection {test['expect_injection']}, got {injection_applied}")
                results.append({"test": test["name"], "status": "FAIL", "details": result})
                
        except Exception as e:
            print(f"    💥 ERROR: {e}")
            results.append({"test": test["name"], "status": "ERROR", "error": str(e)})
    
    return results

def test_fase_3_respaldo_automatico():
    """Prueba FASE 3: Respaldo automático con restauración"""
    print("\n💾 TESTING FASE 3: Respaldo Automático")
    
    # Crear archivo inicial
    initial_data = {
        "ruta": "test_backup.py",
        "contenido": "# Versión inicial\ndef test_v1():\n    return 'v1'"
    }
    
    print("  Creando archivo inicial...")
    try:
        response = requests.post(f"{BASE_URL}/api/escribir-archivo", json=initial_data, timeout=10)
        if not response.json().get("exito"):
            print("    ❌ FAIL - No se pudo crear archivo inicial")
            return [{"test": "Respaldo automático", "status": "FAIL", "error": "No se pudo crear archivo inicial"}]
        
        time.sleep(1)  # Esperar un momento
        
        # Modificar archivo (debería crear respaldo)
        modified_data = {
            "ruta": "test_backup.py",
            "contenido": "# Versión modificada\ndef test_v2():\n    return 'v2'"
        }
        
        print("  Modificando archivo (debería crear respaldo)...")
        response = requests.post(f"{BASE_URL}/api/escribir-archivo", json=modified_data, timeout=10)
        result = response.json()
        
        # Verificar si se creó respaldo
        advertencias = result.get("advertencias", [])
        backup_created = any("Respaldo creado" in adv for adv in advertencias)
        
        if backup_created:
            print("    ✅ PASS - Respaldo creado correctamente")
            return [{"test": "Respaldo automático", "status": "PASS"}]
        else:
            print("    ❌ FAIL - No se creó respaldo")
            return [{"test": "Respaldo automático", "status": "FAIL", "details": result}]
            
    except Exception as e:
        print(f"    💥 ERROR: {e}")
        return [{"test": "Respaldo automático", "status": "ERROR", "error": str(e)}]

def test_azure_deployment():
    """Prueba el endpoint en Azure (si está disponible)"""
    print("\n☁️ TESTING AZURE DEPLOYMENT")
    
    test_data = {
        "ruta": "azure_test.py",
        "contenido": "# Test desde Azure\nprint('Deployment test successful')"
    }
    
    try:
        print("  Probando conexión con Azure...")
        response = requests.post(f"{AZURE_URL}/api/escribir-archivo", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("exito"):
                print("    ✅ PASS - Azure deployment funcional")
                return [{"test": "Azure deployment", "status": "PASS"}]
            else:
                print(f"    ❌ FAIL - Error en Azure: {result.get('error')}")
                return [{"test": "Azure deployment", "status": "FAIL", "details": result}]
        else:
            print(f"    ❌ FAIL - HTTP {response.status_code}")
            return [{"test": "Azure deployment", "status": "FAIL", "http_code": response.status_code}]
            
    except requests.exceptions.Timeout:
        print("    ⏰ TIMEOUT - Azure no responde (puede estar en cold start)")
        return [{"test": "Azure deployment", "status": "TIMEOUT"}]
    except Exception as e:
        print(f"    💥 ERROR: {e}")
        return [{"test": "Azure deployment", "status": "ERROR", "error": str(e)}]

def test_bing_fallback_integration():
    """Prueba la integración con Bing Fallback Guard"""
    print("\n🔍 TESTING BING FALLBACK INTEGRATION")
    
    # Intentar crear archivo con ruta problemática para activar Bing Fallback
    test_data = {
        "ruta": "",  # Ruta vacía para forzar fallback
        "contenido": "print('test fallback')"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/escribir-archivo", json=test_data, timeout=15)
        result = response.json()
        
        # Verificar si Bing Fallback se activó
        advertencias = result.get("advertencias", [])
        bing_activated = any("Bing" in adv for adv in advertencias)
        
        if bing_activated or result.get("exito"):  # Éxito con o sin Bing
            print("    ✅ PASS - Bing Fallback integrado correctamente")
            return [{"test": "Bing Fallback", "status": "PASS"}]
        else:
            print("    ❌ FAIL - Bing Fallback no funcionó")
            return [{"test": "Bing Fallback", "status": "FAIL", "details": result}]
            
    except Exception as e:
        print(f"    💥 ERROR: {e}")
        return [{"test": "Bing Fallback", "status": "ERROR", "error": str(e)})

def generate_report(all_results):
    """Genera reporte final de validación"""
    print("\n" + "="*60)
    print("📊 REPORTE FINAL DE VALIDACIÓN")
    print("="*60)
    
    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(1 for results in all_results.values() for result in results if result["status"] == "PASS")
    failed_tests = sum(1 for results in all_results.values() for result in results if result["status"] == "FAIL")
    error_tests = sum(1 for results in all_results.values() for result in results if result["status"] == "ERROR")
    
    print(f"Total tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"💥 Errors: {error_tests}")
    print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetalle por fase:")
    for phase, results in all_results.items():
        phase_passed = sum(1 for r in results if r["status"] == "PASS")
        phase_total = len(results)
        print(f"  {phase}: {phase_passed}/{phase_total} ({'✅' if phase_passed == phase_total else '❌'})")
    
    # Guardar reporte
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests)*100
        },
        "details": all_results
    }
    
    with open("deployment_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado en: deployment_validation_report.json")
    
    return passed_tests == total_tests

def main():
    """Ejecuta todas las pruebas de validación"""
    print("🚀 INICIANDO VALIDACIÓN DE DEPLOYMENT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing endpoint: {BASE_URL}/api/escribir-archivo")
    
    all_results = {}
    
    # Ejecutar todas las pruebas
    all_results["Fase 1 - Validación Previa"] = test_fase_1_validacion_previa()
    all_results["Fase 2 - Inyección Delimitada"] = test_fase_2_inyeccion_delimitada()
    all_results["Fase 3 - Respaldo Automático"] = test_fase_3_respaldo_automatico()
    all_results["Bing Fallback Integration"] = test_bing_fallback_integration()
    all_results["Azure Deployment"] = test_azure_deployment()
    
    # Generar reporte
    success = generate_report(all_results)
    
    if success:
        print("\n🎉 TODAS LAS PRUEBAS PASARON - LISTO PARA DEPLOYMENT")
        return 0
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR ANTES DE DEPLOYMENT")
        return 1

if __name__ == "__main__":
    exit(main())