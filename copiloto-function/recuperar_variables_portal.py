#!/usr/bin/env python3
"""
Recupera variables de entorno desde local.settings.json y las sube al portal de Azure
"""

import json
import subprocess
import sys

def recuperar_variables():
    """Lee local.settings.json y sube las variables al portal"""
    
    # Leer local.settings.json
    try:
        with open("local.settings.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"ERROR leyendo local.settings.json: {e}")
        return False
    
    settings = config.get("Values", {})
    
    if not settings:
        print("ERROR: No hay settings en local.settings.json")
        return False
    
    print(f"Encontrados {len(settings)} settings en local.settings.json")
    
    # Configuración de Azure
    resource_group = "boat-rental-app-group"
    function_app = "copiloto-semantico-func-us2"
    
    # Construir comando az cli
    settings_args = []
    for key, value in settings.items():
        # Escapar valores con espacios o caracteres especiales
        value_str = str(value).replace('"', '\\"')
        settings_args.append(f"{key}={value_str}")
    
    print(f"\nSubiendo {len(settings_args)} variables a {function_app}...")
    print("Esto puede tardar 1-2 minutos...\n")
    
    # Ejecutar en lotes de 10 para evitar límites de comando
    batch_size = 10
    for i in range(0, len(settings_args), batch_size):
        batch = settings_args[i:i+batch_size]
        
        cmd = [
            "az", "functionapp", "config", "appsettings", "set",
            "-g", resource_group,
            "-n", function_app,
            "--settings"
        ] + batch
        
        print(f"Lote {i//batch_size + 1}/{(len(settings_args)-1)//batch_size + 1}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"ERROR en lote {i//batch_size + 1}:")
                print(result.stderr)
                return False
            
            print(f"  OK: {len(batch)} variables configuradas")
            
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT en lote {i//batch_size + 1}")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    print(f"\nTodas las variables recuperadas exitosamente")
    return True

if __name__ == "__main__":
    print("Recuperador de Variables de Entorno")
    print("=" * 50)
    
    if recuperar_variables():
        print("\nVariables recuperadas en el portal de Azure")
        sys.exit(0)
    else:
        print("\nFallo al recuperar variables")
        sys.exit(1)
