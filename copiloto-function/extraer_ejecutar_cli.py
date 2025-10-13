#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def extraer_ejecutar_cli():
    """Extrae la función ejecutar_cli_http completa de function_app.py"""
    
    try:
        with open('function_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la función completa desde @app.route hasta la siguiente función
        pattern = r'(@app\.route\(route="ejecutar-cli".*?def ejecutar_cli_http.*?)(?=@app\.|\ndef [a-zA-Z_]|\Z)'
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        else:
            # Buscar solo la función sin el decorador
            pattern2 = r'(def ejecutar_cli_http.*?)(?=def [a-zA-Z_]|\Z)'
            match2 = re.search(pattern2, content, re.DOTALL)
            if match2:
                return match2.group(1)
        
        return "No se encontró la función ejecutar_cli_http"
        
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = extraer_ejecutar_cli()
    # Escribir a archivo para evitar problemas de encoding
    with open('ejecutar_cli_actual.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print("Función extraída y guardada en ejecutar_cli_actual.txt")