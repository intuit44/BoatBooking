# -*- coding: utf-8 -*-
"""
Script para configurar alertas en Application Insights
"""
import os
import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient

def setup_alerts():
    subscription_id = "380fa841-83f3-42fe-adc4-582a5ebe139b"
    resource_group = "boat-rental-app-group"
    workspace_name = "DefaultWorkspace-380fa841-83f3-42fe-adc4-582a5ebe139b-EUS2"
    
    credential = DefaultAzureCredential()
    monitor_client = MonitorManagementClient(credential, subscription_id)
    
    workspace_id = f"/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-EUS2/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}"
    
    # Alerta 1: Fallos en promoción
    alert1_config = {
        "location": "East US 2",
        "properties": {
            "displayName": "Fixes - Fallos en Promoción",
            "description": "Alerta cuando hay fallos en la promoción de fixes",
            "severity": 2,
            "enabled": True,
            "evaluationFrequency": "PT5M",
            "windowSize": "PT5M",
            "criteria": {
                "allOf": [
                    {
                        "query": """
                        traces
                        | where timestamp > ago(5m)
                        | where customDimensions.tipo == "promocion_batch"
                        | extend fallidos = toint(customDimensions.fallidos_count)
                        | where fallidos > 0
                        | summarize total_fallidos = sum(fallidos)
                        | where total_fallidos > 0
                        """,
                        "timeAggregation": "Count",
                        "operator": "GreaterThan",
                        "threshold": 0
                    }
                ]
            },
            "actions": [
                {
                    "actionGroupId": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Insights/actionGroups/fixes-alerts"
                }
            ]
        }
    }
    
    # Alerta 2: Sin promociones por tiempo prolongado
    alert2_config = {
        "location": "East US 2", 
        "properties": {
            "displayName": "Fixes - Sin Promociones",
            "description": "Alerta cuando no hay promociones por 30 minutos",
            "severity": 3,
            "enabled": True,
            "evaluationFrequency": "PT30M",
            "windowSize": "PT30M",
            "criteria": {
                "allOf": [
                    {
                        "query": """
                        traces
                        | where timestamp > ago(30m)
                        | where customDimensions.tipo == "promocion_batch"
                        | extend promovidos = toint(customDimensions.promovidos_count)
                        | summarize total_promovidos = sum(promovidos)
                        | where total_promovidos == 0
                        """,
                        "timeAggregation": "Count",
                        "operator": "GreaterThan", 
                        "threshold": 0
                    }
                ]
            }
        }
    }
    
    print("Configuración de alertas preparada:")
    print("1. Fallos en promoción - cada 5 minutos")
    print("2. Sin promociones - cada 30 minutos")
    print("\nPara aplicar, ejecutar comandos Azure CLI correspondientes")

if __name__ == "__main__":
    setup_alerts()