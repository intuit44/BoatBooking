# -*- coding: utf-8 -*-
"""
Test del sistema automático de memoria
"""
from dotenv import load_dotenv
load_dotenv()

import requests
import json
import time

def test_automatic_memory():
    print("TESTING SISTEMA AUTOMATICO DE MEMORIA")
    print("=" * 50)
    
    # Test con endpoint local (si está corriendo)
    base_url = "http://localhost:7071/api"
    
    print("\n1. Probando endpoint /status...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint local disponible")
        else:
            print("❌ Endpoint local no disponible, usando Azure")
            base_url = "https://copiloto-semantico-func-us2.azurewebsites.net/api"
    except:
        print("❌ Local no disponible, usando Azure")
        base_url = "https://copiloto-semantico-func-us2.azurewebsites.net/api"
    
    print(f"\n2. Usando base URL: {base_url}")
    
    # Test endpoints críticos
    endpoints_to_test = [
        {"url": "/verificar-sistema", "method": "GET"},
        {"url": "/verificar-cosmos", "method": "GET"},
        {"url": "/verificar-app-insights", "method": "GET"},
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n3. Probando {endpoint['url']}...")
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['url']}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint['url']}", 
                                       json={"test": "data"}, timeout=10)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Ejecutado - debería estar en memoria")
            else:
                print(f"   ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n4. Verificando memoria...")
    time.sleep(2)  # Esperar a que se procesen
    
    # Verificar que se guardaron en memoria
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        import os
        
        endpoint = os.environ.get('COSMOSDB_ENDPOINT')
        key = os.environ.get('COSMOSDB_KEY')
        
        if key:
            client = CosmosClient(endpoint, key)
        else:
            client = CosmosClient(endpoint, DefaultAzureCredential())
        
        db = client.get_database_client('agentMemory')
        container = db.get_container_client('memory')
        
        # Consultar últimas interacciones
        query = "SELECT TOP 5 c.id, c.agent_id, c.source, c.timestamp FROM c ORDER BY c._ts DESC"
        items = list(container.query_items(query, enable_cross_partition_query=True))
        
        print(f"\n5. Últimas {len(items)} interacciones en memoria:")
        for item in items:
            print(f"   - {item.get('source', 'N/A')} | {item.get('agent_id', 'N/A')} | {item.get('timestamp', 'N/A')}")
        
        # Buscar interacciones recientes (últimos 5 minutos)
        from datetime import datetime, timedelta
        cinco_min_atras = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        query_recent = f"SELECT * FROM c WHERE c.timestamp > '{cinco_min_atras}' ORDER BY c._ts DESC"
        recent_items = list(container.query_items(query_recent, enable_cross_partition_query=True))
        
        print(f"\n6. Interacciones recientes (últimos 5 min): {len(recent_items)}")
        for item in recent_items:
            source = item.get('source', 'N/A')
            agent = item.get('agent_id', 'N/A')
            timestamp = item.get('timestamp', 'N/A')
            print(f"   ✅ {source} | {agent} | {timestamp}")
        
        if len(recent_items) > 0:
            print("\n🎉 SISTEMA AUTOMÁTICO DE MEMORIA FUNCIONANDO!")
        else:
            print("\n⚠️ No se encontraron interacciones recientes")
            
    except Exception as e:
        print(f"\n❌ Error verificando memoria: {e}")

if __name__ == "__main__":
    test_automatic_memory()