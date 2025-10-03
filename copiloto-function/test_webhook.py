#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar el endpoint autocorregir simulando un webhook de Azure Monitor
"""
import requests
import json
from datetime import datetime

def test_webhook():
    """Prueba el endpoint autocorregir simulando un webhook"""
    
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/autocorregir"
    
    # Simular payload de Azure Monitor
    webhook_payload = {
        "schemaId": "azureMonitorCommonAlertSchema",
        "data": {
            "essentials": {
                "alertId": "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/microsoft.insights/scheduledqueryrules/AppInsightsHttp500Alert",
                "alertRule": "AppInsightsHttp500Alert",
                "severity": "Sev2",
                "signalType": "Log",
                "monitorCondition": "Fired",
                "description": "Alerta exacta para HTTP 500 en App Insights",
                "firedDateTime": datetime.now().isoformat()
            },
            "alertContext": {
                "SearchQuery": "requests | where resultCode == '500'",
                "SearchIntervalStartTimeUtc": datetime.now().isoformat(),
                "SearchIntervalEndTimeUtc": datetime.now().isoformat(),
                "ResultCount": 1,
                "LinkToSearchResults": "https://portal.azure.com",
                "SeverityDescription": "Warning",
                "WorkspaceId": "test-workspace",
                "SearchIntervalInMinutes": 5,
                "AffectedConfigurationItems": ["copiloto-semantico-func-us2"],
                "SearchResult": {
                    "tables": [
                        {
                            "name": "PrimaryResult",
                            "columns": [
                                {"name": "timestamp", "type": "datetime"},
                                {"name": "resultCode", "type": "string"},
                                {"name": "name", "type": "string"}
                            ],
                            "rows": [
                                [datetime.now().isoformat(), "500", "POST /api/test500"]
                            ]
                        }
                    ]
                }
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Microsoft-Azure-Monitor/1.0"
        # Intencionalmente NO incluir X-Agent-Auth para simular webhook
    }
    
    print("Enviando webhook simulado a autocorregir...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(webhook_payload, indent=2)[:200]}...")
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers, timeout=30)
        
        print(f"\nRespuesta:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"Body (raw): {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error enviando webhook: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_webhook()
    print(f"\nPrueba {'exitosa' if success else 'fallida'}")