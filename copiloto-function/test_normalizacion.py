#!/usr/bin/env python3
"""Test para encontrar DÓNDE se rompen las comillas"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Comando de prueba
comando_original = 'findstr /C:"def buscar_memoria_http" C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py /C:"return"'

print("=" * 60)
print("TEST: Rastrear normalización de comillas")
print("=" * 60)
print(f"Comando original: {comando_original}")
print()

# Test 1: command_type_detector
try:
    from command_type_detector import detect_and_normalize_command
    result = detect_and_normalize_command(comando_original)
    print(f"1. command_type_detector:")
    print(f"   Normalizado: {result['normalized_command']}")
    print(f"   Roto: {'SI' if result['normalized_command'] != comando_original else 'NO'}")
    print()
except Exception as e:
    print(f"1. command_type_detector: ERROR - {e}")
    print()

# Test 2: _normalizar_comando_robusto
try:
    from function_app import _normalizar_comando_robusto
    result = _normalizar_comando_robusto(comando_original)
    print(f"2. _normalizar_comando_robusto:")
    print(f"   Normalizado: {result}")
    print(f"   Roto: {'SI' if result != comando_original else 'NO'}")
    print()
except Exception as e:
    print(f"2. _normalizar_comando_robusto: ERROR - {e}")
    print()

# Test 3: command_cleaner
try:
    from command_cleaner import limpiar_comillas_comando
    result = limpiar_comillas_comando(comando_original)
    print(f"3. limpiar_comillas_comando:")
    print(f"   Limpio: {result}")
    print(f"   Roto: {'SI' if result != comando_original else 'NO'}")
    print()
except Exception as e:
    print(f"3. limpiar_comillas_comando: ERROR - {e}")
    print()

# Test 4: _auto_resolve_file_paths
try:
    from function_app import _auto_resolve_file_paths
    result = _auto_resolve_file_paths(comando_original)
    print(f"4. _auto_resolve_file_paths:")
    print(f"   Resuelto: {result}")
    print(f"   Roto: {'SI' if result != comando_original else 'NO'}")
    print()
except Exception as e:
    print(f"4. _auto_resolve_file_paths: ERROR - {e}")
    print()

print("=" * 60)
print("CONCLUSION:")
print("Buscar la función que muestra 'Roto: SI'")
print("=" * 60)
