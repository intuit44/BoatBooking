#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar memory_service antes del despliegue
"""
import os
import sys
import json
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_memory_service():
    """Prueba básica del memory service"""
    print("[TEST] Iniciando pruebas del memory_service...")
    
    try:
        # Importar memory service
        from services.memory_service import memory_service
        print("[OK] memory_service importado correctamente")
        
        # Verificar que existe
        if memory_service is None:
            print("[ERROR] memory_service es None")
            return False
            
        print(f"[OK] memory_service inicializado: {type(memory_service)}")
        
        # Verificar Cosmos Store
        print(f"[INFO] Cosmos Store habilitado: {memory_service.cosmos_store.enabled}")
        if memory_service.cosmos_store.enabled:
            print(f"[INFO] Endpoint: {memory_service.cosmos_store.endpoint}")
            print(f"[INFO] Database: {memory_service.cosmos_store.database_name}")
            print(f"[INFO] Container: {memory_service.cosmos_store.container_name}")
        
        # Prueba de logging básico
        test_session = f"test_{int(datetime.now().timestamp())}"
        
        print(f"[TEST] Probando log_event con session_id: {test_session}")
        result = memory_service.log_event("test_event", {
            "mensaje": "Prueba desde test_memory_service.py",
            "timestamp": datetime.now().isoformat(),
            "test_data": {"key": "value", "number": 42}
        }, session_id=test_session)
        
        print(f"[OK] log_event resultado: {result}")
        
        # Prueba de consulta si Cosmos está habilitado
        if memory_service.cosmos_store.enabled:
            print("[TEST] Probando consulta de historial...")
            history = memory_service.get_session_history(test_session, limit=5)
            print(f"[INFO] Historial obtenido: {len(history)} elementos")
            if history:
                print(f"[INFO] Primer elemento: {json.dumps(history[0], indent=2)}")
        
        print("[OK] Todas las pruebas básicas completadas exitosamente")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Error de importación: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cosmos_connection():
    """Prueba específica de conexión a Cosmos DB"""
    print("\n[TEST] Probando conexión directa a Cosmos DB...")
    
    try:
        from services.cosmos_store import CosmosMemoryStore
        
        # Crear instancia directa
        cosmos = CosmosMemoryStore()
        
        print(f"[INFO] Cosmos habilitado: {cosmos.enabled}")
        
        if cosmos.enabled:
            # Prueba de escritura directa
            test_data = {
                "session_id": "direct_test",
                "event_type": "connection_test",
                "message": "Prueba directa de Cosmos DB",
                "timestamp": datetime.now().isoformat()
            }
            
            print("[TEST] Probando upsert directo...")
            result = cosmos.upsert(test_data)
            print(f"[OK] Upsert resultado: {result}")
            
            if result:
                print("[TEST] Probando query directo...")
                items = cosmos.query("direct_test", limit=1)
                print(f"[INFO] Query resultado: {len(items)} elementos")
                if items:
                    print(f"[INFO] Elemento: {json.dumps(items[0], indent=2)}")
        else:
            print("[WARN] Cosmos DB no está habilitado - verificar configuración")
            
    except Exception as e:
        print(f"[ERROR] Error en prueba de Cosmos: {e}")
        import traceback
        traceback.print_exc()

def check_environment():
    """Verifica las variables de entorno necesarias"""
    print("\n[CHECK] Verificando variables de entorno...")
    
    required_vars = [
        "COSMOSDB_ENDPOINT",
        "COSMOSDB_DATABASE", 
        "COSMOSDB_CONTAINER"
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"[OK] {var}: {value}")
        else:
            print(f"[WARN] {var}: No configurado (usando default)")
    
    # Verificar Azure SDK
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        print("[OK] Azure SDK disponible")
    except ImportError as e:
        print(f"[ERROR] Azure SDK no disponible: {e}")

if __name__ == "__main__":
    print("[START] Iniciando pruebas completas del memory_service\n")
    
    # Verificar entorno
    check_environment()
    
    # Prueba básica del memory service
    success = test_memory_service()
    
    # Prueba específica de Cosmos
    test_cosmos_connection()
    
    print(f"\n[RESULT] Resultado final: {'EXITO' if success else 'FALLO'}")
    print("[NOTE] Si las pruebas son exitosas, proceder con el despliegue")