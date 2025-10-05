#!/usr/bin/env python3
"""
Prueba de la corrección de verificar_app_insights
"""
import requests
import json

def test_app_insights_endpoint():
    """Prueba el endpoint corregido"""
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-app-insights"
    
    print("[TEST] Probando verificar-app-insights corregido...")
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"[STATUS] {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] {data.get('exito')}")
            print(f"[APP_NAME] {data.get('app_name')}")
            print(f"[METODO] {data.get('metodo')}")
            print(f"[TELEMETRIA] {data.get('telemetria_activa')}")
            
            if data.get('error'):
                print(f"[ERROR] {data.get('error')}")
            if data.get('mensaje'):
                print(f"[MENSAJE] {data.get('mensaje')}")
                
            # Verificar que ya no da PathNotFoundError
            if "PathNotFoundError" in str(data.get('error', '')):
                print("❌ PROBLEMA PERSISTE: PathNotFoundError aún presente")
            else:
                print("✅ CORRECCIÓN EXITOSA: PathNotFoundError eliminado")
                
        else:
            print(f"[HTTP_ERROR] {response.status_code}")
            print(f"[RESPONSE] {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE CORRECCIÓN: VERIFICAR-APP-INSIGHTS")
    print("=" * 60)
    
    test_app_insights_endpoint()
    
    print("\n" + "=" * 60)
    print("RESULTADO ESPERADO:")
    print("• exito: true (siempre)")
    print("• metodo: az_cli, az_cli_raw, o fallback")
    print("• telemetria_activa: true/false")
    print("• Sin PathNotFoundError")
    print("=" * 60)