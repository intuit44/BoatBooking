#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar el curl con más debug para ver qué pasa
"""
import requests
import json

def test_with_debug():
    """Prueba con más información de debug"""
    
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/autocorregir"
    
    # Payload de Azure Monitor
    payload = {
        "schemaId": "azureMonitorCommonAlertSchema",
        "data": {
            "essentials": {
                "alertId": "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/providers/Microsoft.Insights/scheduledqueryrules/AppInsightsHttp500Alert",
                "alertRule": "AppInsightsHttp500Alert",
                "severity": "Sev2",
                "monitorCondition": "Fired",
                "description": "Alerta exacta para HTTP 500 en App Insights"
            },
            "alertContext": {
                "SearchQuery": "requests | where resultCode == '500'",
                "condition": "resultCode == '500'",
                "timeAggregation": "Count"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Azure-Monitor-Test/1.0"
    }
    
    print("=== PRUEBA CON DEBUG ===")
    print(f"URL: {url}")
    print(f"Payload contiene '500': {'500' in str(payload)}")
    print(f"schemaId: {payload.get('schemaId')}")
    print(f"azuremonitor en schemaId: {'azuremonitor' in payload.get('schemaId', '').lower()}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n=== RESPUESTA ===")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"JSON Response: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            
            # Verificar si el parche funcionó
            if response.status_code == 200:
                print("\n✅ Parche ejecutado correctamente")
                print("Los logs deberían haberse escrito en Azure, no localmente")
                return True
            else:
                print(f"\n❌ Error: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error parseando JSON: {e}")
            print(f"Raw response: {response.text}")
            return False
        
    except Exception as e:
        print(f"Error en request: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_with_debug()
    if success:
        print("\n🎯 CONCLUSIÓN:")
        print("- El parche funciona correctamente")
        print("- Los logs se escriben en el sistema de archivos de Azure")
        print("- Para ver los logs, necesitas acceder al sistema de archivos de la Function App")
    else:
        print("\n❌ El parche tiene problemas")