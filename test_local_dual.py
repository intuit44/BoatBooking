#!/usr/bin/env python3
"""
Prueba local de la funcionalidad dual
"""
import os
import json

def test_dual_logic():
    """Simula la lógica dual que implementé"""
    ruta = "boat-rental-project/copiloto-function/function_app.py"
    
    print(f"[TEST] Probando lógica dual para: {ruta}")
    
    # Paso 1: Local
    print(f"[LOCAL] Verificando si existe: {ruta}")
    local_exists = os.path.exists(ruta)
    print(f"[LOCAL] Resultado: {local_exists}")
    
    if local_exists:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            print(f"[LOCAL] SUCCESS: {len(contenido)} caracteres leídos")
            return {
                "exito": True,
                "origen": "local",
                "size": len(contenido),
                "preview": contenido[:100] + "..."
            }
        except Exception as e:
            print(f"[LOCAL] ERROR: {e}")
    
    # Paso 2: Blob (simulado)
    print(f"[BLOB] Intentando Blob Storage...")
    
    # Parsear ruta para Blob
    parts = ruta.replace("\\", "/").split("/")
    container = parts[0] if len(parts) > 1 else "boat-rental-project"
    blob_name = "/".join(parts[1:]) if len(parts) > 1 else ruta
    
    print(f"[BLOB] Container: {container}")
    print(f"[BLOB] Blob name: {blob_name}")
    
    # Verificar si tenemos connection string
    conn_str = os.environ.get("AzureWebJobsStorage")
    print(f"[BLOB] Connection string disponible: {bool(conn_str)}")
    
    if conn_str:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service = BlobServiceClient.from_connection_string(conn_str)
            blob_client = blob_service.get_blob_client(container=container, blob=blob_name)
            contenido = blob_client.download_blob().readall().decode("utf-8")
            
            print(f"[BLOB] SUCCESS: {len(contenido)} caracteres leídos")
            return {
                "exito": True,
                "origen": "blob",
                "container": container,
                "blob_name": blob_name,
                "size": len(contenido),
                "preview": contenido[:100] + "..."
            }
        except Exception as e:
            print(f"[BLOB] ERROR: {e}")
    
    print(f"[RESULT] Archivo no encontrado en ninguna ubicación")
    return {
        "exito": False,
        "error": "Archivo no encontrado"
    }

if __name__ == "__main__":
    result = test_dual_logic()
    print(f"\n[FINAL] {json.dumps(result, indent=2, ensure_ascii=False)}")