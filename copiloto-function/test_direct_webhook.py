#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar directamente si el parche funciona enviando un webhook simple
"""
import requests
import json

def test_simple_webhook():
    """Prueba con un webhook muy simple"""
    
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/autocorregir"
    
    # Payload muy simple
    simple_payload = {
        "test": "webhook",
        "source": "azure_monitor_simulation"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Azure-Monitor-Test/1.0"
        # Sin X-Agent-Auth para activar el parche
    }
    
    print("Enviando webhook simple...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(simple_payload, indent=2)}")
    
    try:
        response = requests.post(url, json=simple_payload, headers=headers, timeout=30)
        
        print(f"\nRespuesta:")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            
            # Verificar si el parche funcionó
            if response_json.get("mensaje") == "Webhook procesado automáticamente":
                print("\n✅ PARCHE FUNCIONÓ!")
                return True
            else:
                print("\n❌ Parche no funcionó - respuesta inesperada")
                return False
                
        except:
            print(f"Body (raw): {response.text}")
            return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_webhook()
    if success:
        print("\n🎉 El parche está funcionando correctamente!")
    else:
        print("\n🔧 El parche necesita ajustes")