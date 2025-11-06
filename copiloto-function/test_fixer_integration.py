#!/usr/bin/env python3
"""
Test de integración: Simula el payload exacto que envía Azure AI Foundry
"""

import json
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from function_app import ejecutar_comando_sistema

def test_foundry_payload():
    """Simula el comando exacto que envía Foundry"""
    
    # Payload exacto de Foundry
    comando_foundry = "powershell -Command \"Get-Content 'C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py' | Select-String -Pattern 'def buscar_memoria_http' -Context 0,10 | Format-Table -AutoSize -Wrap | Out-String\""
    
    print("=" * 80)
    print("TEST: Simulacion de payload de Azure AI Foundry")
    print("=" * 80)
    print(f"\nComando recibido:\n{comando_foundry}\n")
    
    # Ejecutar con el sistema
    resultado = ejecutar_comando_sistema(comando_foundry, "powershell")
    
    print("=" * 80)
    print("RESULTADO:")
    print("=" * 80)
    print(f"\nExito: {resultado.get('exito', False)}")
    print(f"Duracion: {resultado.get('duration', 'N/A')}")
    print(f"Comando ejecutado:\n{resultado.get('comando_ejecutado', 'N/A')}\n")
    
    # Verificar que el fixer se aplicó
    comando_ejecutado = resultado.get('comando_ejecutado', '')
    
    print("=" * 80)
    print("VERIFICACION DEL FIXER:")
    print("=" * 80)
    
    if '-Width 4096' in comando_ejecutado:
        print("[OK] FIXER APLICADO: Se detecto -Width 4096 en el comando ejecutado")
    else:
        print("[FAIL] FIXER NO APLICADO: No se encontro -Width 4096")
        print(f"   Comando ejecutado: {comando_ejecutado[:200]}...")
    
    if 'Format-Table' in comando_ejecutado:
        print("[OK] Format-Table presente en el comando")
    else:
        print("[WARN] Format-Table no encontrado")
    
    # Mostrar salida
    print("\n" + "=" * 80)
    print("SALIDA DEL COMANDO:")
    print("=" * 80)
    output = resultado.get('output', resultado.get('stdout', ''))
    if output:
        print(output[:500])
        if len(output) > 500:
            print(f"\n... ({len(output) - 500} caracteres mas)")
    else:
        print("[WARN] Sin salida")
    
    # Verificar errores
    if resultado.get('error'):
        print("\n" + "=" * 80)
        print("ERRORES:")
        print("=" * 80)
        print(resultado.get('error'))
    
    print("\n" + "=" * 80)
    print("RESUMEN:")
    print("=" * 80)
    print(f"Tipo comando: {resultado.get('tipo_comando', 'N/A')}")
    print(f"Método ejecución: {resultado.get('metodo_ejecucion', 'N/A')}")
    print(f"Código salida: {resultado.get('return_code', resultado.get('codigo_salida', 'N/A'))}")
    
    # Resultado final
    print("\n" + "=" * 80)
    if '-Width 4096' in comando_ejecutado and resultado.get('exito'):
        print("[SUCCESS] TEST EXITOSO: El fixer se aplico correctamente")
        return True
    else:
        print("[FAIL] TEST FALLIDO: El fixer no se aplico")
        return False

if __name__ == "__main__":
    success = test_foundry_payload()
    sys.exit(0 if success else 1)
