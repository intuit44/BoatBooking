#!/usr/bin/env python3
"""
Script para revertir cambios y limpiar el archivo function_app.py
"""

import re
from pathlib import Path

def revert_function_app():
    """Revierte los cambios del script anterior"""
    
    file_path = Path("function_app.py")
    if not file_path.exists():
        print("[ERROR] function_app.py no encontrado")
        return
    
    print("[REVERT] Revirtiendo cambios...")
    
    # Leer archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Eliminar la sección de stubs agregada
    if "# === STUBS PARA FUNCIONES FALTANTES ===" in content:
        parts = content.split("# === STUBS PARA FUNCIONES FALTANTES ===")
        content = parts[0].rstrip()
    
    # 2. Restaurar returns comentados
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Restaurar returns que fueron comentados
        if line.strip().startswith("# FIXED: ") and "return" in line:
            original_line = line.replace("# FIXED: ", "")
            fixed_lines.append(original_line)
        else:
            fixed_lines.append(line)
    
    # 3. Escribir archivo limpio
    content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Archivo revertido a estado anterior")
    print("[INFO] Stubs eliminados, returns restaurados")

if __name__ == "__main__":
    revert_function_app()