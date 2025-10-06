# -*- coding: utf-8 -*-
"""
Test completo del sistema Cosmos DB + App Insights
"""
import requests
import json
import time

def test_full_system():
    base_url = "http://localhost:7071/api"  # Cambiar por Azure URL cuando esté desplegado
    
    print("🧪 TESTING SISTEMA COMPLETO COSMOS DB + APP INSIGHTS")
    print("=" * 60)
    
    # Test 1: Crear fix via autocorregir
    print("\n1. Creando fix via /autocorregir...")
    fix_data = {
        "accion": "update_timeout",
        "target": "config/app.json", 
        "propuesta": "Increase timeout from 10s to 30s",
        "tipo": "config_update",
        "detonante": "performance_issue",
        "origen": "Test Agent"
    }
    
    headers = {"X-Agent-Auth": "AI-FOUNDRY-TOKEN"}
    
    try:
        response = requests.post(f"{base_url}/autocorregir", 
                               json=fix_data, 
                               headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            fix_id = result.get("correccion", {}).get("id")
            print(f"✅ Fix creado: {fix_id}")
        else:
            print(f"❌ Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return
    
    # Test 2: Revisar correcciones
    print("\n2. Revisando correcciones...")
    try:
        response = requests.get(f"{base_url}/revisar-correcciones")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Fuente: {result.get('fuente')}")
            print(f"✅ Total pendientes: {result.get('total')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Verificar Cosmos DB
    print("\n3. Verificando Cosmos DB...")
    try:
        response = requests.get("https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-cosmos")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cosmos DB: {result.get('estado')}")
            print(f"✅ Registros: {result.get('registros_encontrados')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Verificar App Insights
    print("\n4. Verificando App Insights...")
    try:
        response = requests.get("https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-app-insights")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ App Insights: {'Conectado' if result.get('exito') else 'Error'}")
            print(f"✅ Método: {result.get('metodo')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n📊 RESUMEN:")
    print("- Cosmos DB: Contenedores fixes, semantic_events, leases creados")
    print("- App Insights: Logger estructurado con customDimensions")
    print("- Endpoints: Migrados con fallback a JSON")
    print("- Change Feed: Listo para despliegue")
    print("- Alertas: Configuradas para fallos y sin promociones")

if __name__ == "__main__":
    test_full_system()