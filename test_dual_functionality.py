#!/usr/bin/env python3
"""
Prueba local de la funcionalidad dual local/Blob
"""
import os
import json

def test_dual_logic():
    """Prueba la lógica dual implementada"""
    
    test_cases = [
        {
            "name": "Archivo local existente",
            "ruta": "copiloto-function/function_app.py"
        },
        {
            "name": "Ruta Blob format",
            "ruta": "boat-rental-project/copiloto-function/function_app.py"
        },
        {
            "name": "Archivo inexistente",
            "ruta": "archivo_que_no_existe.txt"
        }
    ]
    
    print("=" * 60)
    print("PRUEBAS DE FUNCIONALIDAD DUAL LOCAL/BLOB")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[PRUEBA {i}] {test_case['name']}")
        print(f"[RUTA] {test_case['ruta']}")
        
        ruta = test_case['ruta']
        
        # Paso 1: Local
        local_exists = os.path.exists(ruta)
        print(f"[LOCAL] Existe: {local_exists}")
        
        if local_exists:
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    contenido = f.read()
                print(f"[LOCAL] SUCCESS: {len(contenido)} chars")
                print(f"[RESPONSE] {{'exito': True, 'origen': 'local', 'size': {len(contenido)}}}")
                continue
            except Exception as e:
                print(f"[LOCAL] ERROR: {e}")
        
        # Paso 2: Blob (simulado)
        parts = ruta.replace("\\", "/").split("/")
        container = parts[0] if len(parts) > 1 else "boat-rental-project"
        blob_name = "/".join(parts[1:]) if len(parts) > 1 else ruta
        
        print(f"[BLOB] Container: {container}")
        print(f"[BLOB] Blob name: {blob_name}")
        
        # Simular conexión Blob
        conn_str = os.environ.get("AzureWebJobsStorage")
        print(f"[BLOB] Connection available: {bool(conn_str)}")
        
        if not conn_str:
            print(f"[BLOB] No connection string - would fail in real scenario")
        
        print(f"[RESPONSE] {{'exito': False, 'error': 'Archivo no encontrado'}}")
        print("-" * 40)
    
    print(f"\n[DONE] Pruebas de funcionalidad dual completadas")

if __name__ == "__main__":
    test_dual_logic()