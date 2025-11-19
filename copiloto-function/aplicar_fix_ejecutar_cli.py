#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar el fix al endpoint ejecutar-cli en function_app.py
"""

import re

def aplicar_fix():
    """Aplica el fix al endpoint ejecutar-cli"""
    
    try:
        # Leer el archivo actual
        with open('function_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Leer el fix generado
        with open('ejecutar_cli_fixed.py', 'r', encoding='utf-8') as f:
            fix_content = f.read()
        
        # Buscar la función actual
        pattern = r'(@app\.route\(route="ejecutar-cli".*?def ejecutar_cli_http.*?)(?=@app\.|\ndef [a-zA-Z_]|\Z)'
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            old_function = match.group(1)
            
            # Reemplazar la función
            new_content = content.replace(old_function, fix_content)
            
            # Crear backup
            with open('function_app_backup.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Escribir el archivo actualizado
            with open('function_app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Fix aplicado exitosamente")
            print("📁 Backup creado: function_app_backup.py")
            print("\n🔧 Cambios aplicados:")
            print("1. Endpoint NUNCA devuelve HTTP 400/500")
            print("2. Autocorrección con memoria integrada")
            print("3. Respuestas semánticas para agentes")
            print("4. Memoria manual en todas las respuestas")
            
            return True
        else:
            print("❌ No se encontró la función ejecutar_cli_http")
            return False
            
    except Exception as e:
        print(f"❌ Error aplicando fix: {e}")
        return False

if __name__ == "__main__":
    aplicar_fix()