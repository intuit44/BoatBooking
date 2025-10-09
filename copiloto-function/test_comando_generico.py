#!/usr/bin/env python3
"""
Test del endpoint ejecutar-comando genérico
Prueba diferentes tipos de comandos dinámicamente
"""

import requests
import json
import time

# URL base del endpoint
BASE_URL = "http://localhost:7071/api/ejecutar-comando"

def test_comando(comando, descripcion):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🧪 {descripcion}")
    print(f"Comando: {comando}")
    print("-" * 50)
    
    try:
        response = requests.post(BASE_URL, json={"comando": comando}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Éxito: {result.get('exito')}")
            print(f"Tipo detectado: {result.get('tipo_comando', 'N/A')}")
            print(f"Confianza: {result.get('confianza_deteccion', 'N/A')}")
            
            if result.get('resultado'):
                print(f"Resultado: {result['resultado'][:200]}...")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
                
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    time.sleep(1)  # Pausa entre tests

def main():
    """Ejecuta todos los tests"""
    print("🚀 Iniciando tests del endpoint ejecutar-comando genérico")
    
    # Tests de diferentes tipos de comandos
    tests = [
        # Azure CLI
        ("az account show", "Azure CLI - Mostrar cuenta actual"),
        ("az storage account list", "Azure CLI - Listar storage accounts"),
        
        # Python
        ("python -c \"print('Hola desde Python')\"", "Python - Comando simple"),
        ("pip list", "Python - Listar paquetes"),
        
        # PowerShell (Windows)
        ("Get-Date", "PowerShell - Obtener fecha"),
        ("Get-Process | Select-Object -First 5", "PowerShell - Procesos"),
        
        # Bash/Linux
        ("echo 'Hola desde bash'", "Bash - Echo simple"),
        ("ls -la", "Bash - Listar archivos"),
        
        # NPM
        ("npm --version", "NPM - Versión"),
        
        # Docker
        ("docker --version", "Docker - Versión"),
        
        # Comando genérico
        ("whoami", "Genérico - Usuario actual"),
        ("date", "Genérico - Fecha del sistema"),
        
        # Comandos que pueden fallar
        ("comando_inexistente", "Test - Comando inexistente"),
        ("", "Test - Comando vacío")
    ]
    
    for comando, descripcion in tests:
        test_comando(comando, descripcion)
    
    print("\n" + "="*60)
    print("🏁 Tests completados")
    print("="*60)

if __name__ == "__main__":
    main()