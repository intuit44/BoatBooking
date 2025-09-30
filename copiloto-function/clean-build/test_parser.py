#!/usr/bin/env python3

import json
import re

def clean_agent_response(agent_response):
    """
    Parser robusto que acepta dict, str (JSON o texto), y maneja casos comunes.
    """
    try:
        print(f"[clean_agent_response] Tipo: {type(agent_response).__name__}, Preview: {str(agent_response)[:80]}")
        
        # Si ya es un dict, devolver tal cual
        if isinstance(agent_response, dict):
            return agent_response

        # Si es string, intentar parsear como JSON directo
        if isinstance(agent_response, str):
            stripped = agent_response.strip()
            print(f"[clean_agent_response] Stripped: '{stripped}'")
            
            # Si parece JSON puro
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass

            # Caso 1: Comandos simples
            simple_commands = {
                "ping": {"endpoint": "ping"},
                "status": {"endpoint": "status"},
                "health": {"endpoint": "health"},
                "estado": {"endpoint": "status"}
            }
            clean_text = stripped.lower()
            print(f"[clean_agent_response] Clean text: '{clean_text}'")
            
            if clean_text in simple_commands:
                print(f"[clean_agent_response] Found in simple_commands: {simple_commands[clean_text]}")
                return simple_commands[clean_text]

            # Caso 3: Palabras clave y semántica mínima
            keywords_map = {
                "dashboard": {"endpoint": "ejecutar", "intencion": "dashboard", "method": "POST"},
                "diagnostico": {"endpoint": "ejecutar", "intencion": "diagnosticar:completo", "method": "POST"},
                "diagnóstico": {"endpoint": "ejecutar", "intencion": "diagnosticar:completo", "method": "POST"},
                "resumen": {"endpoint": "ejecutar", "intencion": "generar:resumen", "method": "POST"},
                "listar archivos": {"endpoint": "ejecutar", "intencion": "buscar:archivos", "method": "POST"},
                "listar blobs": {"endpoint": "listar-blobs", "method": "GET"},
                "leer archivo": {"endpoint": "leer-archivo", "method": "GET"},
                "bateria": {"endpoint": "bateria-endpoints", "method": "GET"},
                "probar endpoint": {"endpoint": "probar-endpoint", "method": "POST"},
            }
            
            print(f"[clean_agent_response] Checking keywords_map...")
            for keyword, command in keywords_map.items():
                print(f"[clean_agent_response] Checking keyword: '{keyword}' in '{clean_text}'")
                if keyword in clean_text:
                    print(f"[clean_agent_response] Found keyword '{keyword}': {command}")
                    # Normalizar endpoint a guion medio
                    if "endpoint" in command:
                        command = dict(command)
                        command["endpoint"] = command["endpoint"].replace("_", "-")
                    return command

            # Fallback seguro: texto libre, usar POST por defecto
            fallback = {
                "endpoint": "copiloto",
                "mensaje": stripped[:100],
                "method": "POST"
            }
            print(f"[clean_agent_response] Using fallback: {fallback}")
            return fallback

        # Si no es dict ni str, error
        return {"error": "Formato de agent_response no soportado"}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

# Pruebas
if __name__ == "__main__":
    test_cases = [
        "dashboard",
        "ping",
        "status",
        "diagnostico",
        '{"endpoint": "ejecutar", "intencion": "dashboard"}',
        "listar blobs"
    ]
    
    for test in test_cases:
        print(f"\n=== Testing: '{test}' ===")
        result = clean_agent_response(test)
        print(f"Result: {result}")
        print("-" * 50)