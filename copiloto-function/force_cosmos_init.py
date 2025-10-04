#!/usr/bin/env python3
"""
Script para forzar la inicialización de Cosmos DB y ver logs
"""
import requests
import time

def force_cosmos_initialization():
    """Fuerza la inicialización del memory_service haciendo múltiples llamadas"""
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    endpoints_to_test = [
        "/api/copiloto?mensaje=test_cosmos",
        "/api/status",
        "/api/hybrid",
        "/api/ejecutar"
    ]
    
    print("[INFO] Forzando inicialización del memory_service...")
    
    for i, endpoint in enumerate(endpoints_to_test):
        print(f"[{i+1}/4] Llamando {endpoint}...")
        
        try:
            if endpoint == "/api/ejecutar":
                # POST request
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"intencion": "dashboard"}, 
                                       timeout=30)
            elif endpoint == "/api/hybrid":
                # POST request
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"agent_response": "ping"}, 
                                       timeout=30)
            else:
                # GET request
                response = requests.get(f"{base_url}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                print(f"  [OK] Status: {response.status_code}")
            else:
                print(f"  [WARN] Status: {response.status_code}")
                
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        # Esperar un poco entre llamadas
        time.sleep(2)
    
    print("\n[INFO] Inicialización forzada completada")
    print("[INFO] Ahora revisa los logs con:")
    print("       az webapp log tail --name copiloto-semantico-func-us2 --resource-group boat-rental-app-group")

if __name__ == "__main__":
    force_cosmos_initialization()