# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar configuración de Cosmos DB y App Insights
"""
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

import os
import json
from datetime import datetime

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno estén configuradas"""
    variables_requeridas = {
        'COSMOSDB_ENDPOINT': os.environ.get('COSMOSDB_ENDPOINT'),
        'COSMOSDB_KEY': os.environ.get('COSMOSDB_KEY'),
        'COSMOSDB_DATABASE': os.environ.get('COSMOSDB_DATABASE', 'copiloto-db'),
        'COSMOSDB_CONTAINER': os.environ.get('COSMOSDB_CONTAINER', 'memory'),
        'APPINSIGHTS_WORKSPACE_ID': os.environ.get('APPINSIGHTS_WORKSPACE_ID'),
        'APPLICATIONINSIGHTS_CONNECTION_STRING': os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
    }
    
    print("🔍 VERIFICACIÓN DE VARIABLES DE ENTORNO:")
    print("=" * 50)
    
    for var, valor in variables_requeridas.items():
        estado = "✅ CONFIGURADA" if valor else "❌ FALTANTE"
        valor_mostrar = valor[:20] + "..." if valor and len(valor) > 20 else valor or "No configurada"
        print(f"{var}: {estado} ({valor_mostrar})")
    
    return variables_requeridas

def test_cosmos_connection():
    """Prueba la conexión a Cosmos DB"""
    print("\n🔍 PRUEBA DE CONEXIÓN COSMOS DB:")
    print("=" * 50)
    
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        
        endpoint = os.environ.get('COSMOSDB_ENDPOINT')
        key = os.environ.get('COSMOSDB_KEY')
        database = os.environ.get('COSMOSDB_DATABASE', 'copiloto-db')
        container_name = os.environ.get('COSMOSDB_CONTAINER', 'memory')
        
        if not endpoint:
            print("❌ COSMOSDB_ENDPOINT no configurado")
            return False
        
        # Intentar con clave primero
        if key:
            try:
                print("🔑 Intentando conexión con clave...")
                client = CosmosClient(endpoint, key)
                db = client.get_database_client(database)
                container = db.get_container_client(container_name)
                
                # Verificar que el container existe
                container_props = container.read()
                print(f"✅ Container '{container_name}' encontrado con clave")
                
                # Intentar query simple
                items = list(container.query_items("SELECT TOP 1 * FROM c", enable_cross_partition_query=True))
                print(f"✅ Query exitosa, {len(items)} items encontrados")
                return True
                
            except Exception as e:
                print(f"❌ Error con clave: {str(e)}")
        
        # Intentar con Managed Identity
        try:
            print("🔐 Intentando conexión con Managed Identity...")
            credential = DefaultAzureCredential()
            client = CosmosClient(endpoint, credential)
            db = client.get_database_client(database)
            container = db.get_container_client(container_name)
            
            # Verificar que el container existe
            container_props = container.read()
            print(f"✅ Container '{container_name}' encontrado con MI")
            
            # Intentar query simple
            items = list(container.query_items("SELECT TOP 1 * FROM c", enable_cross_partition_query=True))
            print(f"✅ Query exitosa con MI, {len(items)} items encontrados")
            return True
            
        except Exception as e:
            print(f"❌ Error con Managed Identity: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando librerías: {str(e)}")
        return False

def test_appinsights_connection():
    """Prueba la conexión a Application Insights"""
    print("\n🔍 PRUEBA DE CONEXIÓN APP INSIGHTS:")
    print("=" * 50)
    
    try:
        from azure.monitor.query import LogsQueryClient
        from azure.identity import DefaultAzureCredential
        from datetime import timedelta
        
        workspace_id = os.environ.get('APPINSIGHTS_WORKSPACE_ID')
        
        if not workspace_id:
            print("❌ APPINSIGHTS_WORKSPACE_ID no configurado")
            return False
        
        try:
            print("🔐 Intentando conexión con Managed Identity...")
            credential = DefaultAzureCredential()
            client = LogsQueryClient(credential)
            
            # Query simple para verificar conectividad
            query = "union * | take 1"
            response = client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timedelta(hours=1)
            )
            
            print(f"✅ Conexión exitosa a workspace: {workspace_id}")
            
            # Verificar si hay datos
            has_data = False
            eventos_count = 0
            
            if hasattr(response, 'tables') and getattr(response, 'tables', None):
                tables = getattr(response, 'tables')
                for table in tables:
                    if hasattr(table, 'rows') and getattr(table, 'rows', None):
                        eventos_count += len(getattr(table, 'rows'))
                has_data = eventos_count > 0
            
            if has_data:
                print(f"✅ Datos encontrados: {eventos_count} eventos")
            else:
                print("⚠️ Conexión exitosa pero sin datos recientes")
            
            return True
            
        except Exception as e:
            print(f"❌ Error con Managed Identity: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando librerías: {str(e)}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO DE COSMOS DB Y APP INSIGHTS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Verificar variables de entorno
    variables = verificar_variables_entorno()
    
    # Probar conexiones
    cosmos_ok = test_cosmos_connection()
    appinsights_ok = test_appinsights_connection()
    
    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print("=" * 50)
    print(f"Cosmos DB: {'✅ OK' if cosmos_ok else '❌ FALLO'}")
    print(f"App Insights: {'✅ OK' if appinsights_ok else '❌ FALLO'}")
    
    if not cosmos_ok:
        print("\n💡 SUGERENCIAS PARA COSMOS DB:")
        print("- Verificar que COSMOSDB_ENDPOINT esté configurado")
        print("- Verificar permisos de Managed Identity en Cosmos DB")
        print("- Verificar que la base de datos y container existan")
    
    if not appinsights_ok:
        print("\n💡 SUGERENCIAS PARA APP INSIGHTS:")
        print("- Verificar que APPINSIGHTS_WORKSPACE_ID esté configurado")
        print("- Verificar permisos de Managed Identity en Log Analytics")
        print("- Verificar que el workspace ID sea correcto")

if __name__ == "__main__":
    main()