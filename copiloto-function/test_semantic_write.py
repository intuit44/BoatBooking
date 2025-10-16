#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test directo de escritura de memoria semántica
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_semantic_write():
    """Prueba directa de escritura semántica"""
    print("Probando escritura de memoria semantica...")
    
    try:
        from services.semantic_memory import registrar_snapshot_semantico
        
        # Test 1: Registrar snapshot
        resultado = registrar_snapshot_semantico(
            session_id="test-write-direct",
            agent_id="TestAgent",
            tipo="test_snapshot",
            contenido={
                "mensaje": "Test de escritura directa",
                "timestamp": "2025-01-14T12:00:00Z"
            },
            metadata={"test": True}
        )
        
        print(f"Resultado escritura: {resultado}")
        
        if resultado.get("exito"):
            print("OK Escritura semantica exitosa")
            
            # Test 2: Verificar que se escribió
            from services.cosmos_store import CosmosMemoryStore
            cosmos = CosmosMemoryStore()
            
            if cosmos.enabled and cosmos.container:
                # Buscar el documento recién creado
                query = "SELECT * FROM c WHERE c.session_id = 'test-write-direct' ORDER BY c.timestamp DESC"
                items = list(cosmos.container.query_items(query, enable_cross_partition_query=True))
                
                print(f"Documentos encontrados: {len(items)}")
                for i, item in enumerate(items[:3]):
                    print(f"  {i+1}. ID: {item.get('id')}, Tipo: {item.get('tipo')}, Categoria: {item.get('categoria')}")
                
                if items:
                    print("OK Verificacion exitosa: documento encontrado en Cosmos DB")
                    return True
                else:
                    print("ERROR: documento no encontrado en Cosmos DB")
                    return False
            else:
                print("WARNING: Cosmos DB no habilitado, no se puede verificar")
                return False
        else:
            print(f"ERROR en escritura: {resultado.get('error')}")
            return False
            
    except Exception as e:
        print(f"ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cosmos_connection():
    """Prueba la conexión a Cosmos DB"""
    print("\nProbando conexion a Cosmos DB...")
    
    try:
        from services.cosmos_store import CosmosMemoryStore
        
        cosmos = CosmosMemoryStore()
        print(f"Cosmos habilitado: {cosmos.enabled}")
        print(f"Endpoint: {cosmos.endpoint}")
        print(f"Database: {cosmos.database_name}")
        print(f"Container: {cosmos.container_name}")
        
        if cosmos.enabled and cosmos.container:
            # Probar query simple
            query = "SELECT TOP 1 * FROM c"
            items = list(cosmos.container.query_items(query, enable_cross_partition_query=True))
            print(f"Query test exitoso: {len(items)} items")
            return True
        else:
            print("ERROR: Cosmos DB no esta habilitado o configurado")
            return False
            
    except Exception as e:
        print(f"ERROR probando Cosmos: {e}")
        return False

if __name__ == "__main__":
    print("=== TEST DE MEMORIA SEMÁNTICA ===")
    
    # Test 1: Conexión
    conexion_ok = test_cosmos_connection()
    
    # Test 2: Escritura (solo si conexión OK)
    if conexion_ok:
        escritura_ok = test_semantic_write()
        
        if escritura_ok:
            print("\nTODOS LOS TESTS PASARON")
            print("La memoria semantica esta funcionando correctamente")
        else:
            print("\nFALLO EN ESCRITURA")
            print("La memoria semantica no se esta persistiendo")
    else:
        print("\nFALLO EN CONEXION")
        print("No se puede conectar a Cosmos DB")