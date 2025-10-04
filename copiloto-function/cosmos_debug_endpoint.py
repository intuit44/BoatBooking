import azure.functions as func
import json
import os
from datetime import datetime

@func.route(route="cosmos-debug", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def cosmos_debug_http(req: func.HttpRequest) -> func.HttpResponse:
    """Diagnóstico de Cosmos DB"""
    try:
        results = {"timestamp": datetime.now().isoformat(), "debug": {}}
        
        results["debug"]["env_vars"] = {
            "COSMOSDB_ENDPOINT": os.environ.get("COSMOSDB_ENDPOINT"),
            "COSMOSDB_DATABASE": os.environ.get("COSMOSDB_DATABASE"),
            "COSMOSDB_CONTAINER": os.environ.get("COSMOSDB_CONTAINER")
        }
        
        try:
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential
            results["debug"]["azure_imports"] = "OK"
        except ImportError as e:
            results["debug"]["azure_imports"] = f"FAIL: {e}"
        
        try:
            from services.cosmos_store import COSMOS_AVAILABLE
            results["debug"]["COSMOS_AVAILABLE"] = COSMOS_AVAILABLE
        except Exception as e:
            results["debug"]["COSMOS_AVAILABLE"] = f"ERROR: {e}"
        
        try:
            from services.memory_service import memory_service
            if memory_service:
                results["debug"]["memory_service"] = {
                    "loaded": True,
                    "cosmos_enabled": memory_service.cosmos_store.enabled,
                    "cosmos_endpoint": memory_service.cosmos_store.endpoint
                }
            else:
                results["debug"]["memory_service"] = {"loaded": False}
        except Exception as e:
            results["debug"]["memory_service"] = f"ERROR: {e}"
        
        return func.HttpResponse(json.dumps(results, indent=2), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}, indent=2), mimetype="application/json", status_code=500)