#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script maestro para ejecutar todas las pruebas de validación
del endpoint /api/escribir-archivo antes del despliegue.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_test_script(script_name, description):
    """Ejecuta un script de prueba y retorna el resultado"""
    print(f"\n{'='*60}")
    print(f"🚀 EJECUTANDO: {description}")
    print(f"Script: {script_name}")
    print('='*60)
    
    try:
        # Ejecutar el script
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=300)  # 5 minutos timeout
        
        # Mostrar output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Retornar código de salida
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: El script excedió 5 minutos")
        return False
    except Exception as e:
        print(f"💥 ERROR ejecutando {script_name}: {e}")
        return False

def check_prerequisites():
    """Verifica que los prerequisitos estén disponibles"""
    print("🔍 VERIFICANDO PREREQUISITOS")
    
    # Verificar que requests esté instalado
    try:
        import requests
        print("  ✅ requests library disponible")
    except ImportError:
        print("  ❌ requests library no encontrada")
        print("     Instalar con: pip install requests")
        return False
    
    # Verificar que los scripts de prueba existan
    test_scripts = [
        "test_deployment_validation.py",
        "azure_compatibility_test.py"
    ]
    
    for script in test_scripts:
        if os.path.exists(script):
            print(f"  ✅ {script} encontrado")
        else:
            print(f"  ❌ {script} no encontrado")
            return False
    
    return True

def main():
    """Ejecuta todas las pruebas en secuencia"""
    print("🎯 VALIDACIÓN COMPLETA DEL ENDPOINT /api/escribir-archivo")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Directorio: {os.getcwd()}")
    
    # Verificar prerequisitos
    if not check_prerequisites():
        print("\n❌ PREREQUISITOS NO CUMPLIDOS")
        return 1
    
    # Lista de pruebas a ejecutar
    tests = [
        {
            "script": "test_deployment_validation.py",
            "description": "Validación de las 3 Fases Implementadas",
            "critical": True
        },
        {
            "script": "azure_compatibility_test.py", 
            "description": "Compatibilidad con Azure en Producción",
            "critical": False  # No crítico si Azure no está disponible
        }
    ]
    
    results = []
    critical_failures = 0
    
    # Ejecutar cada prueba
    for test in tests:
        success = run_test_script(test["script"], test["description"])
        
        results.append({
            "script": test["script"],
            "description": test["description"],
            "success": success,
            "critical": test["critical"]
        })
        
        if not success and test["critical"]:
            critical_failures += 1
    
    # Generar reporte final
    print("\n" + "="*80)
    print("📊 REPORTE FINAL DE VALIDACIÓN")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    
    print(f"Total de pruebas: {total_tests}")
    print(f"✅ Exitosas: {passed_tests}")
    print(f"❌ Fallidas: {total_tests - passed_tests}")
    print(f"🚨 Fallas críticas: {critical_failures}")
    
    print("\nDetalle por prueba:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        critical = " (CRÍTICA)" if result["critical"] else ""
        print(f"  {status} {result['description']}{critical}")
    
    # Determinar resultado final
    if critical_failures == 0:
        if passed_tests == total_tests:
            print("\n🎉 TODAS LAS PRUEBAS PASARON")
            print("✅ LISTO PARA DESPLIEGUE EN AZURE")
            final_status = 0
        else:
            print("\n⚠️ ALGUNAS PRUEBAS NO CRÍTICAS FALLARON")
            print("✅ PUEDE PROCEDER CON DESPLIEGUE (con precaución)")
            final_status = 0
    else:
        print("\n❌ FALLAS CRÍTICAS DETECTADAS")
        print("🚫 NO DESPLEGAR HASTA RESOLVER PROBLEMAS")
        final_status = 1
    
    # Mostrar archivos de reporte generados
    report_files = [
        "deployment_validation_report.json",
        "azure_compatibility_report.json"
    ]
    
    print("\n📄 Reportes generados:")
    for report_file in report_files:
        if os.path.exists(report_file):
            print(f"  📋 {report_file}")
    
    # Instrucciones finales
    if final_status == 0:
        print("\n🚀 PRÓXIMOS PASOS:")
        print("  1. Revisar reportes JSON para detalles")
        print("  2. Hacer commit de los cambios")
        print("  3. Desplegar a Azure con confianza")
        print("  4. Ejecutar azure_compatibility_test.py post-despliegue")
    else:
        print("\n🔧 ACCIONES REQUERIDAS:")
        print("  1. Revisar errores en los reportes")
        print("  2. Corregir problemas críticos")
        print("  3. Re-ejecutar pruebas")
        print("  4. Solo desplegar cuando todas las pruebas críticas pasen")
    
    return final_status

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR INESPERADO: {e}")
        sys.exit(1)