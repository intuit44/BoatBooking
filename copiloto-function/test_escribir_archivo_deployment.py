#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación para las 3 fases del endpoint /api/escribir-archivo
Prueba que las implementaciones funcionen correctamente en Azure
"""

import json
import requests
import time
import base64
from datetime import datetime

# Configuración
AZURE_FUNCTION_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"
LOCAL_URL = "http://localhost:7071"

def test_fase_1_validacion_previa():
    """Prueba FASE 1: Validación previa completa"""
    print("🔍 FASE 1: Validación Previa Completa")
    
    tests = [
        {
            "name": "Validación UTF-8 inválida",
            "payload": {
                "ruta": "test_utf8.py",
                "contenido": "print('Hola \udcff mundo')"  # Carácter inválido
            },
            "expect_error": True
        },
        {
            "name": "Validación sintaxis Python inválida",
            "payload": {
                "ruta": "test_syntax.py",
                "contenido": "def funcion_mal(\n    print('sin cerrar'"
            },
            "expect_error": True
        },
        {
            "name": "Validación sintaxis Python válida",
            "payload": {
                "ruta": "test_valid.py",
                "contenido": "def funcion_valida():\n    print('Hola mundo')\n    return True"
            },
            "expect_error": False
        },
        {
            "name": "Detección import recursivo",
            "payload": {
                "ruta": "test_recursivo.py",
                "contenido": "import test_recursivo\nprint('Recursivo detectado')"
            },
            "expect_error": False,
            "expect_warning": True
        }
    ]
    
    results = []
    for test in tests:
        print(f"  ⚡ {test['name']}")
        try:
            response = requests.post(
                f"{AZURE_FUNCTION_URL}/api/escribir-archivo",
                json=test["payload"],
                timeout=30
            )
            
            data = response.json()
            
            if test["expect_error"]:
                success = not data.get("exito", True)
                print(f"    {'✅' if success else '❌'} Error esperado: {success}")
            else:
                success = data.get("exito", False)
                print(f"    {'✅' if success else '❌'} Éxito esperado: {success}")
                
                if test.get("expect_warning") and "advertencias" in data:
                    warning_found = any("recursivo" in str(adv).lower() for adv in data["advertencias"])
                    print(f"    {'✅' if warning_found else '❌'} Warning recursivo: {warning_found}")
            
            results.append({
                "test": test["name"],
                "success": success,
                "response": data
            })
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({
                "test": test["name"],
                "success": False,
                "error": str(e)
            })
    
    return results

def test_fase_2_inyeccion_delimitada():
    """Prueba FASE 2: Inyección delimitada con detección de duplicados"""
    print("\n🔧 FASE 2: Inyección Delimitada con Detección de Duplicados")
    
    tests = [
        {
            "name": "Inyección ErrorHandler primera vez",
            "payload": {
                "ruta": "test_inject1.py",
                "contenido": "from error_handler import ErrorHandler\n\ndef test_function():\n    pass"
            },
            "expect_injection": True
        },
        {
            "name": "Inyección ErrorHandler ya existente",
            "payload": {
                "ruta": "test_inject2.py",
                "contenido": "# ===BEGIN AUTO-INJECT: ErrorHandler===\nfrom error_handler import ErrorHandler\n# ===END AUTO-INJECT: ErrorHandler===\n\ndef test_function():\n    pass"
            },
            "expect_injection": False
        },
        {
            "name": "Múltiples inyecciones sin duplicar",
            "payload": {
                "ruta": "test_inject3.py",
                "contenido": "from error_handler import ErrorHandler\nfrom error_handler import ErrorHandler\n\ndef test_function():\n    pass"
            },
            "expect_injection": True
        }
    ]
    
    results = []
    for test in tests:
        print(f"  ⚡ {test['name']}")
        try:
            response = requests.post(
                f"{AZURE_FUNCTION_URL}/api/escribir-archivo",
                json=test["payload"],
                timeout=30
            )
            
            data = response.json()
            success = data.get("exito", False)
            
            if test["expect_injection"]:
                injection_applied = any("inyección" in str(adv).lower() for adv in data.get("advertencias", []))
                print(f"    {'✅' if injection_applied else '❌'} Inyección aplicada: {injection_applied}")
            else:
                no_injection = not any("inyección" in str(adv).lower() for adv in data.get("advertencias", []))
                print(f"    {'✅' if no_injection else '❌'} Sin inyección duplicada: {no_injection}")
            
            results.append({
                "test": test["name"],
                "success": success,
                "response": data
            })
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({
                "test": test["name"],
                "success": False,
                "error": str(e)
            })
    
    return results

def test_fase_3_respaldo_restauracion():
    """Prueba FASE 3: Respaldo automático con restauración"""
    print("\n💾 FASE 3: Respaldo Automático con Restauración")
    
    tests = [
        {
            "name": "Creación con respaldo automático",
            "payload": {
                "ruta": "C:/temp/test_backup.py",  # Ruta local para forzar respaldo
                "contenido": "# Archivo de prueba para respaldo\ndef test():\n    return 'backup_test'"
            },
            "expect_backup": True
        },
        {
            "name": "Validación post-escritura Python",
            "payload": {
                "ruta": "test_validation.py",
                "contenido": "def valid_function():\n    return True\n\nif __name__ == '__main__':\n    print(valid_function())"
            },
            "expect_validation": True
        },
        {
            "name": "Recuperación automática en error",
            "payload": {
                "ruta": "/invalid/path/that/should/fail.py",
                "contenido": "# Este archivo debería fallar pero recuperarse"
            },
            "expect_recovery": True
        }
    ]
    
    results = []
    for test in tests:
        print(f"  ⚡ {test['name']}")
        try:
            response = requests.post(
                f"{AZURE_FUNCTION_URL}/api/escribir-archivo",
                json=test["payload"],
                timeout=30
            )
            
            data = response.json()
            
            if test.get("expect_backup"):
                backup_created = any("respaldo" in str(adv).lower() for adv in data.get("advertencias", []))
                print(f"    {'✅' if backup_created else '❌'} Respaldo creado: {backup_created}")
            
            if test.get("expect_validation"):
                validation_ok = any("validación" in str(adv).lower() for adv in data.get("advertencias", []))
                print(f"    {'✅' if validation_ok else '❌'} Validación post-escritura: {validation_ok}")
            
            if test.get("expect_recovery"):
                recovery_applied = data.get("tipo_operacion") in ["fallback_sintetico", "fallback_total", "fallback_exception"]
                print(f"    {'✅' if recovery_applied else '❌'} Recuperación automática: {recovery_applied}")
            
            success = data.get("exito", False) or recovery_applied
            results.append({
                "test": test["name"],
                "success": success,
                "response": data
            })
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({
                "test": test["name"],
                "success": False,
                "error": str(e)
            })
    
    return results

def test_bing_fallback_integration():
    """Prueba integración con Bing Fallback Guard"""
    print("\n🛡️ PRUEBA: Integración Bing Fallback Guard")
    
    test_payload = {
        "ruta": "",  # Ruta vacía para activar fallback
        "contenido": "# Contenido de prueba para fallback"
    }
    
    try:
        response = requests.post(
            f"{AZURE_FUNCTION_URL}/api/escribir-archivo",
            json=test_payload,
            timeout=30
        )
        
        data = response.json()
        
        # Verificar que el sistema no falle completamente
        fallback_activated = (
            data.get("tipo_operacion") in ["fallback_sintetico", "fallback_total"] or
            any("bing" in str(adv).lower() for adv in data.get("advertencias", []))
        )
        
        print(f"  {'✅' if fallback_activated else '❌'} Bing Fallback activado: {fallback_activated}")
        print(f"  {'✅' if data.get('exito') else '❌'} Sistema no falló: {data.get('exito')}")
        
        return {
            "test": "Bing Fallback Integration",
            "success": fallback_activated and data.get("exito"),
            "response": data
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            "test": "Bing Fallback Integration",
            "success": False,
            "error": str(e)
        }

def test_agente_foundry_scenario():
    """Simula el escenario real del agente de Foundry"""
    print("\n🤖 ESCENARIO: Agente Foundry inyectando ErrorHandler")
    
    # Simular el payload que enviaría el agente de Foundry
    foundry_payload = {
        "ruta": "cosmos_memory_direct.py",
        "contenido": '''# -*- coding: utf-8 -*-
"""
Módulo de memoria directa para Cosmos DB
"""
import json
import logging
from datetime import datetime
from error_handler import ErrorHandler

class CosmosMemoryDirect:
    def __init__(self):
        self.error_handler = ErrorHandler()
        
    def consultar_memoria(self, session_id):
        """Consulta memoria de sesión"""
        try:
            # Lógica de consulta
            return {"exito": True, "datos": []}
        except Exception as e:
            return self.error_handler.handle_error(e)
            
    def registrar_interaccion(self, data):
        """Registra nueva interacción"""
        try:
            # Lógica de registro
            return {"exito": True}
        except Exception as e:
            return self.error_handler.handle_error(e)
'''
    }
    
    try:
        print("  ⚡ Enviando código con ErrorHandler import...")
        response = requests.post(
            f"{AZURE_FUNCTION_URL}/api/escribir-archivo",
            json=foundry_payload,
            timeout=30
        )
        
        data = response.json()
        
        # Verificaciones específicas del escenario Foundry
        checks = {
            "archivo_creado": data.get("exito", False),
            "sintaxis_valida": any("validación sintáctica" in str(adv) for adv in data.get("advertencias", [])),
            "inyeccion_aplicada": any("inyección" in str(adv).lower() for adv in data.get("advertencias", [])),
            "sin_corrupcion": "error" not in data or not data.get("error"),
            "recuperable": data.get("tipo_operacion") != "fallback_exception"
        }
        
        for check, result in checks.items():
            print(f"    {'✅' if result else '❌'} {check.replace('_', ' ').title()}: {result}")
        
        all_passed = all(checks.values())
        print(f"\n  🎯 RESULTADO FOUNDRY: {'✅ ÉXITO' if all_passed else '❌ FALLÓ'}")
        
        return {
            "test": "Agente Foundry Scenario",
            "success": all_passed,
            "checks": checks,
            "response": data
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            "test": "Agente Foundry Scenario",
            "success": False,
            "error": str(e)
        }

def generate_deployment_report(all_results):
    """Genera reporte final de validación"""
    print("\n" + "="*60)
    print("📊 REPORTE FINAL DE VALIDACIÓN DE DESPLIEGUE")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for phase_name, results in all_results.items():
        if isinstance(results, list):
            phase_total = len(results)
            phase_passed = sum(1 for r in results if r.get("success", False))
        else:
            phase_total = 1
            phase_passed = 1 if results.get("success", False) else 0
        
        total_tests += phase_total
        passed_tests += phase_passed
        
        print(f"\n{phase_name}:")
        print(f"  ✅ Pasaron: {phase_passed}/{phase_total}")
        print(f"  📊 Tasa éxito: {(phase_passed/phase_total)*100:.1f}%")
    
    overall_success = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 RESULTADO GENERAL:")
    print(f"  ✅ Tests pasados: {passed_tests}/{total_tests}")
    print(f"  📊 Tasa éxito total: {overall_success:.1f}%")
    
    if overall_success >= 90:
        print(f"  🚀 ESTADO: LISTO PARA PRODUCCIÓN")
    elif overall_success >= 75:
        print(f"  ⚠️ ESTADO: NECESITA AJUSTES MENORES")
    else:
        print(f"  ❌ ESTADO: REQUIERE CORRECCIONES CRÍTICAS")
    
    # Generar archivo de reporte
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": "/api/escribir-archivo",
        "fases_implementadas": ["validacion_previa", "inyeccion_delimitada", "respaldo_restauracion"],
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": overall_success,
        "status": "READY" if overall_success >= 90 else "NEEDS_WORK",
        "detailed_results": all_results
    }
    
    with open("deployment_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte detallado guardado en: deployment_validation_report.json")
    
    return overall_success >= 90

def main():
    """Ejecuta todas las pruebas de validación"""
    print("🚀 INICIANDO VALIDACIÓN DE DESPLIEGUE")
    print("Endpoint: /api/escribir-archivo")
    print("Fases: 3 (Validación + Inyección + Respaldo)")
    print("Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-" * 60)
    
    # Verificar conectividad
    try:
        response = requests.get(f"{AZURE_FUNCTION_URL}/api/status", timeout=10)
        if response.status_code == 200:
            print("✅ Conectividad con Azure Function confirmada")
        else:
            print(f"⚠️ Azure Function responde con código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False
    
    # Ejecutar todas las pruebas
    all_results = {}
    
    try:
        all_results["FASE_1_VALIDACION"] = test_fase_1_validacion_previa()
        time.sleep(1)  # Pausa entre fases
        
        all_results["FASE_2_INYECCION"] = test_fase_2_inyeccion_delimitada()
        time.sleep(1)
        
        all_results["FASE_3_RESPALDO"] = test_fase_3_respaldo_restauracion()
        time.sleep(1)
        
        all_results["BING_FALLBACK"] = test_bing_fallback_integration()
        time.sleep(1)
        
        all_results["FOUNDRY_SCENARIO"] = test_agente_foundry_scenario()
        
        # Generar reporte final
        success = generate_deployment_report(all_results)
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN VALIDACIÓN: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)