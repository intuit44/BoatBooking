#!/usr/bin/env python3
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
    print("\n🔴 Testing Redis connection...")
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
