#!/usr/bin/env python3
"""Test rápido del detector de comandos"""

from command_type_detector import detect_and_normalize_command

# Casos de prueba
test_cases = [
    "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\" -Recurse",
    "ls C:\\ProyectosSimbolicos\\*_test.py",
    "az storage account list",
    "python script.py",
    "dir C:\\temp"
]

print("=== Test de Detección de Comandos ===\n")

for cmd in test_cases:
    result = detect_and_normalize_command(cmd)
    print(f"Comando: {cmd}")
    print(f"  Tipo: {result['type']}")
    print(f"  Confianza: {result['confidence']}")
    print(f"  Normalizado: {result['normalized_command']}")
    print()
