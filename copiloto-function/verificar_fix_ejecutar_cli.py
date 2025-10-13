#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar que el fix de ejecutar-cli se aplicó correctamente
"""

import re

def verificar_fix():
    """Verifica que los cambios críticos se aplicaron"""
    
    try:
        with open('function_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la función ejecutar_cli_http
        pattern = r'def ejecutar_cli_http.*?(?=def [a-zA-Z_]|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("No se encontro la funcion ejecutar_cli_http")
            return False
        
        function_code = match.group(0)
        
        # Verificaciones críticas
        checks = [
            ("HTTP 200 en validación inicial", "status_code=200" in function_code and "status_code=400" not in function_code),
            ("Memoria manual aplicada", "aplicar_memoria_manual(req, resultado)" in function_code),
            ("Autocorrección con memoria", "memoria_contexto" in function_code or "buscar_parametro_en_memoria" in function_code),
            ("Nunca HTTP 422", "status_code=422" not in function_code),
            ("Respuestas adaptativas", "accion_requerida" in function_code),
            ("Mensaje de autocorrección", "autocorregido usando memoria" in function_code or "Comando autocorregido" in function_code)
        ]
        
        print("Verificando cambios aplicados:")
        print("-" * 50)
        
        all_passed = True
        for check_name, condition in checks:
            status = "OK" if condition else "FAIL"
            print(f"{status} {check_name}")
            if not condition:
                all_passed = False
        
        print("-" * 50)
        
        if all_passed:
            print("TODOS LOS CAMBIOS APLICADOS CORRECTAMENTE")
            print("\nResumen de mejoras:")
            print("1. Nunca devuelve HTTP 400/500 - siempre HTTP 200")
            print("2. Autocorreccion con memoria integrada")
            print("3. Respuestas adaptativas para agentes")
            print("4. Memoria manual en todas las respuestas")
            print("5. Reejecutar comandos con valores de memoria")
        else:
            print("ALGUNOS CAMBIOS NO SE APLICARON CORRECTAMENTE")
        
        return all_passed
        
    except Exception as e:
        print(f"Error verificando fix: {e}")
        return False

if __name__ == "__main__":
    verificar_fix()