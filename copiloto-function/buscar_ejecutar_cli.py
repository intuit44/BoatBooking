#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def buscar_ejecutar_cli():
    """Busca la función ejecutar-cli en function_app.py"""
    
    try:
        with open('function_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar patrones relacionados con ejecutar-cli
        patterns = [
            r'@app\.route\(route="ejecutar-cli".*?\ndef.*?\(.*?\):.*?(?=@app\.|\Z)',
            r'def ejecutar_cli_http.*?(?=def|\Z)',
            r'ejecutar-cli.*?(?=\n)',
            r'ejecutar_cli.*?(?=\n)'
        ]
        
        results = []
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches:
                results.append(f"Pattern {i+1} encontrado:")
                for match in matches:
                    results.append(match[:500] + "..." if len(match) > 500 else match)
                    results.append("-" * 50)
        
        if not results:
            # Buscar líneas que contengan "ejecutar" y "cli"
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'ejecutar' in line.lower() and 'cli' in line.lower():
                    results.append(f"Línea {i+1}: {line.strip()}")
        
        return results
        
    except Exception as e:
        return [f"Error: {str(e)}"]

if __name__ == "__main__":
    results = buscar_ejecutar_cli()
    for result in results:
        print(result)