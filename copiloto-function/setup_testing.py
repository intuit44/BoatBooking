#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuración para preparar el entorno de testing
del endpoint /api/escribir-archivo
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Instala las dependencias necesarias para testing"""
    print("📦 INSTALANDO DEPENDENCIAS")
    
    dependencies = [
        "requests>=2.25.0",
        "pytest>=6.0.0",  # Para futuros tests más avanzados
    ]
    
    for dep in dependencies:
        print(f"  Instalando {dep}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep
            ])
            print(f"    ✅ {dep} instalado")
        except subprocess.CalledProcessError as e:
            print(f"    ❌ Error instalando {dep}: {e}")
            return False
    
    return True

def verify_function_app():
    """Verifica que function_app.py tenga las implementaciones"""
    print("\n🔍 VERIFICANDO IMPLEMENTACIONES EN function_app.py")
    
    function_app_path = Path("function_app.py")
    
    if not function_app_path.exists():
        print("  ❌ function_app.py no encontrado")
        return False
    
    content = function_app_path.read_text(encoding='utf-8')
    
    # Verificar que las 3 fases estén implementadas
    checks = [
        ("FASE 1: Validación previa", "# 🔍 FASE 1: VALIDACIÓN PREVIA COMPLETA"),
        ("FASE 2: Inyección delimitada", "# 🔧 BLOQUES DELIMITADOS DE INYECCIÓN"),
        ("FASE 3: Respaldo automático", "# 💾 RESPALDO AUTOMÁTICO ANTES DE MODIFICAR"),
        ("Bing Fallback Guard", "from bing_fallback_guard import ejecutar_grounding_fallback"),
        ("Endpoint escribir-archivo", "@app.route(route=\"escribir-archivo\"")
    ]
    
    all_present = True
    for check_name, check_pattern in checks:
        if check_pattern in content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name} - NO ENCONTRADO")
            all_present = False
    
    return all_present

def create_test_environment():
    """Crea el entorno de testing"""
    print("\n🏗️ CONFIGURANDO ENTORNO DE TESTING")
    
    # Crear directorio de tests si no existe
    test_dir = Path("tests")
    test_dir.mkdir(exist_ok=True)
    print(f"  ✅ Directorio {test_dir} creado/verificado")
    
    # Crear directorio de reportes
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    print(f"  ✅ Directorio {reports_dir} creado/verificado")
    
    # Crear archivo .gitignore para reportes si no existe
    gitignore_path = Path(".gitignore")
    gitignore_content = """
# Test reports
*_report.json
reports/
*.log

# Python cache
__pycache__/
*.pyc
*.pyo

# Backup files
*.bak
"""
    
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content.strip())
        print("  ✅ .gitignore creado")
    else:
        print("  ✅ .gitignore ya existe")
    
    return True

def check_azure_function_tools():
    """Verifica herramientas de Azure Functions"""
    print("\n🔧 VERIFICANDO HERRAMIENTAS AZURE FUNCTIONS")
    
    # Verificar Azure Functions Core Tools
    try:
        result = subprocess.run(["func", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ Azure Functions Core Tools: {version}")
        else:
            print("  ❌ Azure Functions Core Tools no encontrado")
            print("     Instalar desde: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local")
            return False
    except FileNotFoundError:
        print("  ❌ Azure Functions Core Tools no encontrado")
        print("     Instalar desde: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local")
        return False
    
    # Verificar Azure CLI (opcional)
    try:
        result = subprocess.run(["az", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Azure CLI disponible")
        else:
            print("  ⚠️ Azure CLI no encontrado (opcional)")
    except FileNotFoundError:
        print("  ⚠️ Azure CLI no encontrado (opcional)")
    
    return True

def create_quick_test_script():
    """Crea un script de prueba rápida"""
    print("\n📝 CREANDO SCRIPT DE PRUEBA RÁPIDA")
    
    quick_test_content = '''#!/usr/bin/env python3
"""Prueba rápida del endpoint escribir-archivo"""

import requests
import json

def quick_test():
    url = "http://localhost:7071/api/escribir-archivo"
    
    test_data = {
        "ruta": "quick_test.py",
        "contenido": "print('Quick test successful')"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        result = response.json()
        
        if result.get("exito"):
            print("✅ QUICK TEST PASSED")
            print(f"Archivo creado: {result.get('ubicacion', 'N/A')}")
        else:
            print("❌ QUICK TEST FAILED")
            print(f"Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"💥 QUICK TEST ERROR: {e}")

if __name__ == "__main__":
    quick_test()
'''
    
    quick_test_path = Path("quick_test.py")
    quick_test_path.write_text(quick_test_content)
    print(f"  ✅ {quick_test_path} creado")
    
    return True

def main():
    """Configura todo el entorno de testing"""
    print("🚀 CONFIGURACIÓN DE ENTORNO DE TESTING")
    print("Para el endpoint /api/escribir-archivo con 3 fases implementadas")
    print("="*60)
    
    steps = [
        ("Instalando dependencias", install_dependencies),
        ("Verificando implementaciones", verify_function_app),
        ("Configurando entorno", create_test_environment),
        ("Verificando herramientas Azure", check_azure_function_tools),
        ("Creando script de prueba rápida", create_quick_test_script)
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            success_count += 1
        else:
            print(f"  ⚠️ {step_name} tuvo problemas")
    
    # Reporte final
    print("\n" + "="*60)
    print("📊 REPORTE DE CONFIGURACIÓN")
    print("="*60)
    
    print(f"Pasos completados: {success_count}/{len(steps)}")
    
    if success_count == len(steps):
        print("\n🎉 CONFIGURACIÓN COMPLETA")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("  1. Iniciar Azure Functions localmente:")
        print("     func start")
        print("  2. Ejecutar prueba rápida:")
        print("     python quick_test.py")
        print("  3. Ejecutar validación completa:")
        print("     python run_all_tests.py")
        return 0
    else:
        print("\n⚠️ CONFIGURACIÓN INCOMPLETA")
        print("Revisar errores arriba y corregir antes de continuar")
        return 1

if __name__ == "__main__":
    exit(main())