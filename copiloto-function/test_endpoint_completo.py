#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo del endpoint ejecutar-comando genérico
"""

import requests
import json
import time

# URL base del endpoint
BASE_URL = "http://localhost:7071/api/ejecutar-comando"

def test_comando(comando, descripcion, expected_success=True):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"[TEST] {descripcion}")
    print(f"Comando: {comando}")
    print("-" * 60)
    
    try:
        payload = {"comando": comando}
        response = requests.post(BASE_URL, json=payload, timeout=15)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"[OK] Exito: {result.get('exito', False)}")
                print(f"Tipo detectado: {result.get('tipo_comando', 'N/A')}")
                print(f"Confianza: {result.get('confianza_deteccion', 'N/A')}")
                
                if result.get('resultado'):
                    output = result['resultado']
                    if len(output) > 200:
                        print(f"Resultado: {output[:200]}...")
                    else:
                        print(f"Resultado: {output}")
                
                if result.get('error'):
                    print(f"Error: {result['error']}")
                    
                if result.get('tiempo_ejecucion'):
                    print(f"Tiempo: {result['tiempo_ejecucion']}")
                    
            except json.JSONDecodeError:
                print(f"Respuesta no JSON: {response.text[:200]}")
                
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Sin mensaje')}")
            except:
                print(f"Respuesta: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Error de conexion - Esta corriendo la Azure Function?")
        return False
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout - El comando tardo mas de 15 segundos")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return False
    
    time.sleep(1)  # Pausa entre tests
    return True

def main():
    """Ejecuta todos los tests"""
    print("[INICIO] TESTS DEL ENDPOINT EJECUTAR-COMANDO GENERICO")
    print("="*80)
    
    # Verificar conectividad primero
    try:
        response = requests.get("http://localhost:7071/api/status", timeout=5)
        if response.status_code == 200:
            print("[OK] Azure Function esta corriendo")
        else:
            print("[WARN] Azure Function responde pero con status:", response.status_code)
    except:
        print("[ERROR] No se puede conectar a Azure Function en puerto 7071")
        print("   Asegúrate de ejecutar: func start")
        return
    
    # Tests de diferentes tipos de comandos
    tests = [
        # Comandos básicos del sistema
        ("echo 'Hola mundo'", "Echo simple"),
        ("whoami", "Usuario actual"),
        ("date", "Fecha del sistema"),
        
        # Azure CLI (debería redirigir)
        ("az account show", "Azure CLI - Mostrar cuenta"),
        ("az storage account list", "Azure CLI - Listar storage"),
        
        # Python
        ("python -c \"print('Hola desde Python')\"", "Python - Print simple"),
        ("pip --version", "Python - Versión de pip"),
        
        # PowerShell (Windows)
        ("Get-Date", "PowerShell - Fecha"),
        ("Get-Location", "PowerShell - Ubicación actual"),
        
        # NPM
        ("npm --version", "NPM - Versión"),
        
        # Docker
        ("docker --version", "Docker - Versión"),
        
        # Comandos que pueden fallar
        ("comando_que_no_existe", "Test - Comando inexistente", False),
    ]
    
    successful_tests = 0
    total_tests = len(tests)
    
    for comando, descripcion, *expected in tests:
        expected_success = expected[0] if expected else True
        if test_comando(comando, descripcion, expected_success):
            successful_tests += 1
    
    print("\n" + "="*80)
    print("[RESUMEN] TESTS COMPLETADOS")
    print("="*80)
    print(f"Tests ejecutados: {total_tests}")
    print(f"Tests exitosos: {successful_tests}")
    print(f"Tests fallidos: {total_tests - successful_tests}")
    print(f"Porcentaje de éxito: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("[EXITO] Todos los tests pasaron!")
    else:
        print("[WARN] Algunos tests fallaron - revisar logs arriba")

if __name__ == "__main__":
    main()