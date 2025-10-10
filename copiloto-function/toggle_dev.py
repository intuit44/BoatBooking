#!/usr/bin/env python3
"""
Script ultra simple para alternar entre desarrollo y producción
Cambia URLs y versión para forzar refresh en Foundry
"""

import json
import sys
from pathlib import Path

def toggle():
    openapi_file = Path(__file__).parent / "openapi.yaml"
    
    with open(openapi_file, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    current_first_url = spec["servers"][0]["url"]
    current_version = spec["info"]["version"]
    
    # Incrementar versión para forzar refresh en Foundry
    version_parts = current_version.split('.')
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    new_version = '.'.join(version_parts)
    spec["info"]["version"] = new_version
    
    if "ngrok.app" in current_first_url:
        # Cambiar a producción
        spec["servers"] = [
            {"url": "https://copiloto-semantico-func-us2.azurewebsites.net"},
            {"url": "https://copiloto-func.ngrok.app"}
        ]
        print(f"[OK] Cambiado a PRODUCCIÓN (v{new_version})")
        print("   Foundry usará: Azure")
    else:
        # Cambiar a desarrollo
        spec["servers"] = [
            {"url": "https://copiloto-func.ngrok.app"},
            {"url": "https://copiloto-semantico-func-us2.azurewebsites.net"}
        ]
        print(f"[OK] Cambiado a DESARROLLO (v{new_version})")
        print("   Foundry usará: ngrok")
        print("   Ejecuta: func start")
    
    with open(openapi_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    toggle()