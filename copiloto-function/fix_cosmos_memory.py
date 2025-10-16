"""
Fix Cosmos DB Memory - Diagnóstico y corrección de configuración
"""

import os
import logging
from azure.cosmos import CosmosClient, exceptions

def diagnosticar_cosmos_db():
    """Diagnostica la configuración de Cosmos DB"""
    
    print("Diagnosticando configuracion de Cosmos DB...")
    
    # Variables de entorno
    endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
    key = os.environ.get("COSMOSDB_KEY")
    database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
    
    print(f"Endpoint: {endpoint}")
    print(f"Key configurada: {'Si' if key else 'No'}")
    print(f"Database: {database_name}")
    
    if not key:
        print("❌ COSMOSDB_KEY no está configurada")
        return False
    
    try:
        # Conectar a Cosmos DB
        client = CosmosClient(endpoint, key)
        print("Conexion a Cosmos DB exitosa")
        
        # Verificar base de datos
        try:
            database = client.get_database_client(database_name)
            db_properties = database.read()
            print(f"Base de datos '{database_name}' existe")
        except exceptions.CosmosResourceNotFoundError:
            print(f"Base de datos '{database_name}' NO existe")
            return False
        
        # Verificar contenedores
        containers_requeridos = ["memory", "fixes", "redirections"]
        
        for container_name in containers_requeridos:
            try:
                container = database.get_container_client(container_name)
                container_properties = container.read()
                print(f"Contenedor '{container_name}' existe")
            except exceptions.CosmosResourceNotFoundError:
                print(f"Contenedor '{container_name}' NO existe")
                return False
        
        print("Configuracion de Cosmos DB correcta")
        return True
        
    except Exception as e:
        print(f"Error conectando a Cosmos DB: {e}")
        return False

def crear_recursos_cosmos():
    """Crea los recursos faltantes en Cosmos DB"""
    
    print("Creando recursos faltantes en Cosmos DB...")
    
    endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
    key = os.environ.get("COSMOSDB_KEY")
    database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
    
    if not key:
        print("No se puede crear recursos sin COSMOSDB_KEY")
        return False
    
    try:
        client = CosmosClient(endpoint, key)
        
        # Crear base de datos si no existe
        try:
            database = client.create_database_if_not_exists(id=database_name)
            print(f"Base de datos '{database_name}' creada/verificada")
        except Exception as e:
            print(f"Error creando base de datos: {e}")
            return False
        
        # Crear contenedores
        containers_config = {
            "memory": "/session_id",
            "fixes": "/id", 
            "redirections": "/session_id"
        }
        
        for container_name, partition_key in containers_config.items():
            try:
                container = database.create_container_if_not_exists(
                    id=container_name,
                    partition_key={"paths": [partition_key], "kind": "Hash"}
                )
                print(f"Contenedor '{container_name}' creado/verificado")
            except Exception as e:
                print(f"Error creando contenedor '{container_name}': {e}")
                return False
        
        print("Todos los recursos de Cosmos DB creados exitosamente")
        return True
        
    except Exception as e:
        print(f"Error general creando recursos: {e}")
        return False

def probar_memoria_basica():
    """Prueba básica del sistema de memoria"""
    
    print("Probando sistema de memoria...")
    
    endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
    key = os.environ.get("COSMOSDB_KEY")
    database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
    
    try:
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client("memory")
        
        # Insertar interacción de prueba
        test_item = {
            "id": "test_memory_001",
            "session_id": "test_session_fix",
            "timestamp": "2025-01-14T06:30:00Z",
            "endpoint": "/api/test",
            "consulta": "Prueba de memoria",
            "respuesta": "Respuesta de prueba",
            "exito": True,
            "tipo": "test"
        }
        
        container.upsert_item(test_item)
        print("Interaccion de prueba insertada")
        
        # Consultar interacción
        query = "SELECT * FROM c WHERE c.session_id = 'test_session_fix'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            print(f"Consulta exitosa: {len(items)} items encontrados")
            return True
        else:
            print("No se encontraron items en la consulta")
            return False
            
    except Exception as e:
        print(f"Error probando memoria: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando diagnostico y correccion de Cosmos DB Memory")
    
    # Paso 1: Diagnosticar
    if diagnosticar_cosmos_db():
        print("Configuracion correcta, probando memoria...")
        probar_memoria_basica()
    else:
        print("Configuracion incorrecta, intentando crear recursos...")
        if crear_recursos_cosmos():
            print("Recursos creados, probando memoria...")
            probar_memoria_basica()
        else:
            print("No se pudieron crear los recursos necesarios")