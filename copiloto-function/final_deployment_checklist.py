#!/usr/bin/env python3
"""
Script final para deployar y validar el fix de Managed Identity
"""
import os
import json


def create_deployment_package():
    """Preparar información para deployment"""
    print("📦 PREPARACIÓN PARA DEPLOYMENT")
    print("=" * 50)

    print("✅ Archivos modificados para el fix:")
    print("   📄 services/redis_buffer_service.py")
    print("      - Prioriza ManagedIdentityCredential en Azure Functions")
    print("      - Excluye AzureCliCredential en Azure")
    print("      - Usa token como username para Redis AAD")

    print("\n✅ Role assignments realizados:")
    print("   🔐 Principal ID: 0bc92586-b230-4882-a91c-6c5293cde921")
    print("   🎭 Role: Redis Cache Contributor")
    print("   🎯 Scope: /subscriptions/.../Microsoft.Cache/redisEnterprise/Managed-redis-copiloto")

    print("\n✅ Expected behavior en Azure Functions:")
    print("   1. Detecta entorno Azure Functions ✓")
    print("   2. Usa ManagedIdentityCredential prioritario ✓")
    print("   3. Obtiene token Redis AAD ✓")
    print("   4. Se conecta a Redis con token como username ✓")
    print("   5. Cache hits/misses funcionan ✓")


def show_monitoring_commands():
    """Comandos para monitorear después del deployment"""
    print(f"\n📊 COMANDOS DE MONITOREO POST-DEPLOYMENT")
    print("=" * 60)

    print("🔍 1. Verificar logs de Function App:")
    print("   az webapp log tail --name copiloto-semantico-func-us2 --resource-group boat-rental-app-group")

    print("\n🔍 2. Verificar role assignments:")
    print("   az role assignment list --assignee 0bc92586-b230-4882-a91c-6c5293cde921")

    print("\n🔍 3. Buscar logs específicos:")
    print(
        "   Buscar en logs: '[RedisBuffer] 🏢 Detectado entorno Azure Functions'")
    print(
        "   Esperado: '[RedisBuffer] ✅ Conectado usando ManagedIdentityCredential'")

    print("\n🔍 4. Test MCP server:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -H 'Accept: text/event-stream, application/json' \\")
    print("        -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"1.0\"}}}' \\")
    print("        https://copiloto-semantico-func-us2.azurewebsites.net:8000/mcp")


def show_success_indicators():
    """Indicadores de éxito después del deployment"""
    print(f"\n🎯 INDICADORES DE ÉXITO")
    print("=" * 40)

    print("✅ Logs esperados en Azure Functions:")
    print(
        "   [RedisBuffer] 🏢 Detectado entorno Azure Functions - priorizando ManagedIdentity")
    print("   [RedisBuffer] 🔐 Intentando ManagedIdentityCredential...")
    print(
        "   [RedisBuffer] ✅ Token obtenido para ManagedIdentityCredential: XXXX chars")
    print(
        "   [RedisBuffer] ✅ ManagedIdentityCredential - Conectado como RedisCluster")
    print("   [RedisBuffer] ✅ Conectado usando ManagedIdentityCredential: Managed-redis-copiloto...")

    print("\n✅ MCP Server funcionando:")
    print("   [MCP-RedisCache] ✅ CACHE HIT! Source: session")
    print("   [MCP-RedisCache] ✅ CACHE MISS - calling OpenAI model")
    print("   [MCP] Cache Hit: True/False | Duration: XXXms")


def show_troubleshooting():
    """Pasos de troubleshooting si algo falla"""
    print(f"\n🔧 TROUBLESHOOTING SI FALLA")
    print("=" * 40)

    print("❌ Si sigue usando AzureCliCredential:")
    print("   - Verificar variables: WEBSITE_INSTANCE_ID, WEBSITE_SITE_NAME")
    print("   - Restart Function App")

    print("\n❌ Si ManagedIdentity falla autenticación:")
    print("   - Verificar role assignment está aplicado")
    print("   - Wait 5-10 minutos para propagación")
    print("   - Verificar Redis Enterprise tiene AAD habilitado")

    print("\n❌ Si Redis rechaza conexión:")
    print("   - Verificar que Redis Enterprise soporta AAD")
    print("   - Considerar crear Redis Cache (no Enterprise) para testing")
    print("   - Verificar access keys funcionan como fallback")


def create_final_validation_script():
    """Crear script para validar en producción"""
    validation_script = '''#!/usr/bin/env python3
"""
Script de validación para ejecutar EN AZURE FUNCTIONS (producción)
"""
import os
import logging
from services.redis_buffer_service import redis_buffer

# Configurar logging
logging.basicConfig(level=logging.INFO)

def main():
    print("🔍 VALIDACIÓN EN PRODUCCIÓN - AZURE FUNCTIONS")
    print("=" * 60)
    
    # Verificar entorno
    is_azure = bool(os.environ.get('WEBSITE_SITE_NAME'))
    print(f"🏢 Entorno Azure Functions: {is_azure}")
    print(f"📍 Site Name: {os.environ.get('WEBSITE_SITE_NAME', 'N/A')}")
    
    # Test Redis connection
    print("\\n🔴 Testing Redis connection...")
    is_connected = redis_buffer.is_enabled
    
    if is_connected:
        print("✅ Redis conectado exitosamente!")
        
        # Test cache operation
        success = redis_buffer.cache_llm_response(
            agent_id="ProductionTest",
            session_id="prod_test_session", 
            message="Test message for production validation",
            model="gpt-4o-mini",
            response_data={"status": "production_test_success"}
        )
        
        if success:
            print("✅ Cache WRITE exitoso en producción")
            
            cached = redis_buffer.get_llm_cached_response(
                agent_id="ProductionTest",
                session_id="prod_test_session",
                message="Test message for production validation", 
                model="gpt-4o-mini"
            )
            
            if cached:
                print("✅ Cache READ exitoso en producción")
                print("🎉 MANAGED IDENTITY FIX FUNCIONANDO EN PRODUCCIÓN!")
            else:
                print("❌ Cache READ falló")
        else:
            print("❌ Cache WRITE falló")
    else:
        print("❌ Redis connection falló")
        print("🔍 Revisar logs para detalles de autenticación")

if __name__ == "__main__":
    main()
'''

    with open('production_validation.py', 'w', encoding='utf-8') as f:
        f.write(validation_script)

    print("📄 Creado: production_validation.py")
    print("   - Subir a Function App")
    print("   - Ejecutar para validar Managed Identity en producción")


if __name__ == "__main__":
    print("🚀 MANAGED IDENTITY FIX - DEPLOYMENT READY")
    print("=" * 80)

    create_deployment_package()
    show_monitoring_commands()
    show_success_indicators()
    show_troubleshooting()
    create_final_validation_script()

    print(f"\n" + "=" * 80)
    print("🎯 RESUMEN FINAL:")
    print("   ✅ Código modificado y listo para deployment")
    print("   ✅ Role assignments configurados")
    print("   ✅ Monitoring commands preparados")
    print("   ✅ Validation script creado")
    print("   🚀 LISTO PARA DEPLOYMENT Y TESTING EN AZURE!")
    print("=" * 80)
