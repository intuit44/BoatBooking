#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoint HTTP para probar memory_service en Azure
"""
import azure.functions as func
import json
import logging
from datetime import datetime

def test_memory_azure_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para probar memory_service en Azure"""
    
    try:
        # Importar memory service
        from services.memory_service import memory_service
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "Azure",
            "tests": {}
        }
        
        # Test 1: Verificar memory_service
        if memory_service is None:
            results["tests"]["memory_service"] = {
                "status": "FAIL",
                "error": "memory_service es None"
            }
            return func.HttpResponse(
                json.dumps(results, indent=2),
                mimetype="application/json",
                status_code=500
            )
        
        results["tests"]["memory_service"] = {
            "status": "OK",
            "type": str(type(memory_service))
        }
        
        # Test 2: Verificar Cosmos Store
        cosmos_enabled = memory_service.cosmos_store.enabled
        results["tests"]["cosmos_store"] = {
            "status": "OK" if cosmos_enabled else "DISABLED",
            "enabled": cosmos_enabled,
            "endpoint": memory_service.cosmos_store.endpoint,
            "database": memory_service.cosmos_store.database_name,
            "container": memory_service.cosmos_store.container_name
        }
        
        # Test 3: Prueba de log_event
        test_session = f"azure_test_{int(datetime.now().timestamp())}"
        log_result = memory_service.log_event("azure_test", {
            "mensaje": "Prueba desde Azure Function",
            "timestamp": datetime.now().isoformat(),
            "test_data": {"environment": "azure", "test_id": test_session}
        }, session_id=test_session)
        
        results["tests"]["log_event"] = {
            "status": "OK" if log_result else "FAIL",
            "result": log_result,
            "session_id": test_session
        }
        
        # Test 4: Prueba de consulta (solo si Cosmos está habilitado)
        if cosmos_enabled:
            try:
                history = memory_service.get_session_history(test_session, limit=1)
                results["tests"]["query_history"] = {
                    "status": "OK",
                    "items_found": len(history),
                    "first_item": history[0] if history else None
                }
            except Exception as e:
                results["tests"]["query_history"] = {
                    "status": "FAIL",
                    "error": str(e)
                }
        else:
            results["tests"]["query_history"] = {
                "status": "SKIPPED",
                "reason": "Cosmos DB not enabled"
            }
        
        # Test 5: Prueba directa de Cosmos
        if cosmos_enabled:
            try:
                direct_data = {
                    "session_id": "direct_azure_test",
                    "event_type": "direct_test",
                    "message": "Prueba directa desde Azure",
                    "timestamp": datetime.now().isoformat()
                }
                
                upsert_result = memory_service.cosmos_store.upsert(direct_data)
                results["tests"]["cosmos_direct"] = {
                    "status": "OK" if upsert_result else "FAIL",
                    "upsert_result": upsert_result
                }
                
                if upsert_result:
                    query_items = memory_service.cosmos_store.query("direct_azure_test", limit=1)
                    results["tests"]["cosmos_direct"]["query_items"] = len(query_items)
                    
            except Exception as e:
                results["tests"]["cosmos_direct"] = {
                    "status": "FAIL",
                    "error": str(e)
                }
        
        # Resumen final
        all_tests = results["tests"]
        passed = sum(1 for test in all_tests.values() if test.get("status") == "OK")
        total = len([t for t in all_tests.values() if t.get("status") not in ["SKIPPED"]])
        
        results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "overall_status": "SUCCESS" if passed == total else "PARTIAL" if passed > 0 else "FAILED"
        }
        
        status_code = 200 if results["summary"]["overall_status"] == "SUCCESS" else 206
        
        return func.HttpResponse(
            json.dumps(results, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=status_code
        )
        
    except Exception as e:
        logging.exception("Error en test_memory_azure_http")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )