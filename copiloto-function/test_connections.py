# -*- coding: utf-8 -*-
"""
Test simple de conexiones sin emojis
"""
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta

def test_cosmos():
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        
        endpoint = os.environ.get('COSMOSDB_ENDPOINT')
        key = os.environ.get('COSMOSDB_KEY')
        database = os.environ.get('COSMOSDB_DATABASE', 'agentMemory')
        container_name = os.environ.get('COSMOSDB_CONTAINER', 'memory')
        
        print(f"Testing Cosmos DB: {endpoint}")
        
        # Test con clave
        if key:
            print("Testing with key...")
            client = CosmosClient(endpoint, key)
            db = client.get_database_client(database)
            container = db.get_container_client(container_name)
            items = list(container.query_items("SELECT TOP 1 * FROM c", enable_cross_partition_query=True))
            print(f"SUCCESS: Found {len(items)} items with key")
            return True
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_appinsights():
    try:
        from azure.monitor.query import LogsQueryClient
        from azure.identity import DefaultAzureCredential
        
        workspace_id = os.environ.get('APPINSIGHTS_WORKSPACE_ID')
        print(f"Testing App Insights: {workspace_id}")
        
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        
        response = client.query_workspace(
            workspace_id=workspace_id,
            query="Usage | take 1",
            timespan=timedelta(hours=1)
        )
        
        print("SUCCESS: App Insights connected")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("TESTING CONNECTIONS")
    print("=" * 50)
    
    cosmos_ok = test_cosmos()
    appinsights_ok = test_appinsights()
    
    print("\nRESULTS:")
    print(f"Cosmos DB: {'OK' if cosmos_ok else 'FAILED'}")
    print(f"App Insights: {'OK' if appinsights_ok else 'FAILED'}")