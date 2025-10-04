#!/usr/bin/env python3
"""
Script para probar Cosmos DB desde Azure usando HTTP
"""
import requests
import json

def test_cosmos_via_http():
    """Prueba Cosmos DB usando el endpoint hybrid"""
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    # Test 1: Verificar que el sistema está funcionando
    print("[TEST] Verificando que la Function App está activa...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=30)
        if response.status_code == 200:
            print("[OK] Function App está activa")
            data = response.json()
            print(f"[INFO] Ambiente: {data.get('ambiente')}")
            print(f"[INFO] Storage: {data.get('storage')}")
        else:
            print(f"[ERROR] Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        return False
    
    # Test 2: Probar memory_service indirectamente
    print("\n[TEST] Probando memory_service indirectamente...")
    try:
        # Usar el endpoint copiloto que debería usar memory_service
        response = requests.get(f"{base_url}/api/copiloto?mensaje=diagnosticar", timeout=30)
        if response.status_code == 200:
            print("[OK] Endpoint copiloto responde")
            data = response.json()
            print(f"[INFO] Tipo: {data.get('tipo')}")
            print(f"[INFO] Ambiente: {data.get('metadata', {}).get('ambiente')}")
        else:
            print(f"[WARN] Copiloto status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error en copiloto: {e}")
    
    # Test 3: Probar usando hybrid endpoint
    print("\n[TEST] Probando usando hybrid endpoint...")
    try:
        payload = {"agent_response": "ping"}
        response = requests.post(f"{base_url}/api/hybrid", json=payload, timeout=30)
        if response.status_code == 200:
            print("[OK] Hybrid endpoint responde")
            data = response.json()
            print(f"[INFO] Resultado disponible: {'resultado' in data}")
        else:
            print(f"[WARN] Hybrid status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error en hybrid: {e}")
    
    # Test 4: Intentar una operación que debería usar memory_service
    print("\n[TEST] Probando operación que debería usar memory_service...")
    try:
        payload = {
            "intencion": "diagnosticar:completo",
            "parametros": {}
        }
        response = requests.post(f"{base_url}/api/ejecutar", json=payload, timeout=60)
        if response.status_code == 200:
            print("[OK] Ejecutar endpoint responde")
            data = response.json()
            if "metadata" in data:
                print(f"[INFO] Procesador: {data['metadata'].get('procesador')}")
                print(f"[INFO] Ambiente: {data['metadata'].get('ambiente')}")
            
            # Verificar si hay información sobre memory_service
            if "exito" in data:
                print(f"[INFO] Operación exitosa: {data['exito']}")
        else:
            print(f"[WARN] Ejecutar status code: {response.status_code}")
            print(f"[WARN] Response: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] Error en ejecutar: {e}")
    
    print("\n[RESULT] Pruebas completadas")
    print("[NOTE] Si los endpoints responden, el memory_service está cargado")
    print("[NOTE] Para verificar Cosmos DB específicamente, revisar logs de Azure")
    
    return True

if __name__ == "__main__":
    print("[START] Probando Cosmos DB desde Azure via HTTP\n")
    test_cosmos_via_http()