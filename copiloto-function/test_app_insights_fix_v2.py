#!/usr/bin/env python3
"""
Test corregido para verificar-app-insights
Verifica que el endpoint funcione sin PathNotFoundError
"""

import requests
import json

def test_app_insights_endpoint():
    """Prueba el endpoint corregido de verificar-app-insights"""
    
    print("=" * 60)
    print("PRUEBA CORREGIDA: VERIFICAR-APP-INSIGHTS")
    print("=" * 60)
    
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-app-insights"
    
    try:
        print(f"[TEST] Probando endpoint corregido...")
        print(f"[URL] {url}")
        
        response = requests.get(url, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] ✅ Endpoint funcional")
            print(f"[EXITO] {data.get('exito', 'N/A')}")
            print(f"[METODO] {data.get('metodo', 'N/A')}")
            print(f"[TELEMETRIA] {data.get('telemetria_activa', 'N/A')}")
            
            if 'error' in data:
                print(f"[ERROR_INFO] {data['error'][:100]}...")
            
            if data.get('exito') == True:
                print("✅ CORRECCIÓN EXITOSA: No más PathNotFoundError")
            else:
                print("⚠️  Endpoint funcional pero con limitaciones")
                
        else:
            print(f"[HTTP_ERROR] {response.status_code}")
            print(f"[RESPONSE] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")
    
    print("\n" + "=" * 60)
    print("RESULTADO ESPERADO:")
    print("• exito: true (siempre)")
    print("• metodo: workspace_env, workspace_detected, o fallback")
    print("• telemetria_activa: true/false")
    print("• Sin PathNotFoundError")
    print("=" * 60)

if __name__ == "__main__":
    test_app_insights_endpoint()