#!/usr/bin/env python3
"""
Scripts de prueba para endpoints desplegados
"""
import requests
import json

BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net/api"

def test_ejecutar_cli():
    """Prueba el endpoint ejecutar-cli mejorado"""
    print("[TEST] Probando ejecutar-cli...")
    
    url = f"{BASE_URL}/ejecutar-cli"
    payload = {"comando": "python -c \"import psutil; print('CPU:', psutil.cpu_percent())\""}
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            if data.get('exito'):
                output = data.get('output', {})
                print(f"[OUTPUT_TYPE] {output.get('type')}")
                print(f"[SUMMARY] {data.get('summary')}")
            else:
                print(f"[ERROR] {data.get('error')}")
        else:
            print(f"[HTTP_ERROR] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_verificar_sistema():
    """Prueba el endpoint verificar-sistema"""
    print("\n[TEST] Probando verificar-sistema...")
    
    url = f"{BASE_URL}/verificar-sistema"
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SISTEMA] {data.get('sistema')}")
            print(f"[CPU] {data.get('cpu_percent')}%")
            print(f"[MEMORIA] {data.get('memoria', {}).get('percent')}%")
            print(f"[AMBIENTE] {data.get('ambiente')}")
            print(f"[STORAGE] {data.get('storage_connected')}")
        else:
            print(f"[ERROR] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_verificar_app_insights():
    """Prueba el endpoint verificar-app-insights"""
    print("\n[TEST] Probando verificar-app-insights...")
    
    url = f"{BASE_URL}/verificar-app-insights"
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            print(f"[TELEMETRIA] {data.get('telemetria_activa')}")
            print(f"[APP_NAME] {data.get('app_name')}")
        else:
            print(f"[ERROR] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_verificar_cosmos():
    """Prueba el endpoint verificar-cosmos"""
    print("\n[TEST] Probando verificar-cosmos...")
    
    url = f"{BASE_URL}/verificar-cosmos"
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            print(f"[CONECTADO] {data.get('cosmos_conectado')}")
            print(f"[REGISTROS] {data.get('registros_encontrados')}")
            print(f"[ESTADO] {data.get('estado')}")
        else:
            print(f"[ERROR] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_dual_read():
    """Prueba el endpoint dual-read"""
    print("\n[TEST] Probando dual-read...")
    
    url = f"{BASE_URL}/dual-read"
    params = {"ruta": "boat-rental-project/copiloto-function/function_app.py"}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            print(f"[ORIGEN] {data.get('origen')}")
            print(f"[SIZE] {data.get('size')}")
        else:
            print(f"[ERROR] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("PRUEBAS DE ENDPOINTS DESPLEGADOS")
    print("=" * 60)
    
    test_ejecutar_cli()
    test_verificar_sistema()
    test_verificar_app_insights()
    test_verificar_cosmos()
    test_dual_read()
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()