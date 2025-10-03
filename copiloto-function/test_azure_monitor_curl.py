#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar el curl exacto que mencionaste para Azure Monitor
"""
import requests
import json

def test_azure_monitor_curl():
    """Prueba el curl exacto de Azure Monitor"""
    
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/autocorregir"
    
    # Payload exacto de Azure Monitor
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
    
    print("Enviando curl de Azure Monitor...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nRespuesta:")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            
            # Verificar si es la respuesta esperada
            if response.status_code == 200 and response_json.get("exito") == True:
                if "Alerta de Azure Monitor procesada" in response_json.get("mensaje", ""):
                    print("\n✅ PARCHE FUNCIONÓ CORRECTAMENTE!")
                    return True
                else:
                    print("\n⚠️ Respuesta exitosa pero mensaje inesperado")
                    return False
            else:
                print("\n❌ Respuesta no exitosa")
                return False
                
        except:
            print(f"Body (raw): {response.text}")
            return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_azure_monitor_curl()
    if success:
        print("\n🎉 El parche de Azure Monitor funciona!")
        print("Ahora verifica los archivos de logs...")
    else:
        print("\n🔧 El parche necesita ajustes")