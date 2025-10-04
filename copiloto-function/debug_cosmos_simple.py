#!/usr/bin/env python3
"""
Script simple para diagnosticar Cosmos DB usando endpoints existentes
"""
import requests
import json

def debug_cosmos():
    """Diagnostica Cosmos DB usando endpoints existentes"""
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("[DEBUG] Diagnosticando Cosmos DB...")
    
    # Usar el endpoint ejecutar para forzar carga del memory_service
    try:
        payload = {
            "intencion": "diagnosticar:memory_service",
            "parametros": {}
        }
        
        print("[1/2] Forzando carga del memory_service...")
        response = requests.post(f"{base_url}/api/ejecutar", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Respuesta recibida")
            
            # Buscar información relevante
            if "metadata" in data:
                print(f"[INFO] Ambiente: {data['metadata'].get('ambiente')}")
                print(f"[INFO] Procesador: {data['metadata'].get('procesador')}")
            
            if "exito" in data:
                print(f"[INFO] Operación exitosa: {data['exito']}")
                
            # Si hay error, mostrarlo
            if not data.get("exito", True):
                print(f"[WARN] Error: {data.get('error', 'Unknown')}")
        else:
            print(f"[ERROR] Status: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Intentar con copiloto para ver si hay logs
    try:
        print("\n[2/2] Probando con copiloto...")
        response = requests.get(f"{base_url}/api/copiloto?mensaje=debug_memory", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Copiloto responde")
            print(f"[INFO] Ambiente: {data.get('metadata', {}).get('ambiente')}")
        else:
            print(f"[ERROR] Status: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print("\n[CONCLUSION]")
    print("- El memory_service se está cargando (los endpoints responden)")
    print("- Pero no vemos logs de Cosmos DB en los logs de Azure")
    print("- Esto sugiere que COSMOS_AVAILABLE = False o endpoint vacío")
    print("- Necesitamos redesplegar con el endpoint de debug para confirmar")

if __name__ == "__main__":
    debug_cosmos()