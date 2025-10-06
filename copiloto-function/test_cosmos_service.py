# -*- coding: utf-8 -*-
"""
Test del servicio Cosmos DB
"""
from dotenv import load_dotenv
load_dotenv()

from services.cosmos_fixes_service import cosmos_fixes_service
from services.app_insights_logger import app_insights_logger
import json

def test_cosmos_service():
    if not cosmos_fixes_service:
        print("ERROR: Cosmos service not available")
        return
    
    # Test 1: Crear un fix
    fix_data = {
        "id": "test_fix_001",
        "estado": "pendiente",
        "accion": "update_config",
        "target": "app.json",
        "propuesta": "Update timeout to 30s",
        "tipo": "config_update",
        "prioridad": 8,
        "run_id": "test_run_001"
    }
    
    print("Testing upsert_fix...")
    result = cosmos_fixes_service.upsert_fix(fix_data)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Obtener fixes pendientes
    print("\nTesting get_pending_fixes...")
    pending = cosmos_fixes_service.get_pending_fixes()
    print(f"Pending fixes: {len(pending)}")
    
    # Test 3: Log evento semántico
    print("\nTesting log_semantic_event...")
    event_result = cosmos_fixes_service.log_semantic_event("test_event", {
        "message": "Test event from script",
        "run_id": "test_run_001"
    })
    print(f"Event result: {json.dumps(event_result, indent=2)}")
    
    # Test 4: App Insights logger
    print("\nTesting App Insights logger...")
    app_insights_logger.log_fix_event(
        "test_fix_created",
        "test_fix_001", 
        "test_run_001",
        "pendiente",
        "app.json",
        8
    )
    print("App Insights log sent")

if __name__ == "__main__":
    test_cosmos_service()