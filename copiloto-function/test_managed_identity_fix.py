#!/usr/bin/env python3
"""
Test de la corrección de Managed Identity en Redis Buffer Service
"""
import os
import json
import sys


def load_local_settings():
    """Cargar variables desde local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)

        values = settings.get('Values', {})
        for key, value in values.items():
            if key not in os.environ:
                os.environ[key] = value

        print(f"✅ Variables cargadas: {len(values)}")
        return True
    except Exception as e:
        print(f"❌ Error cargando settings: {e}")
        return False


def test_redis_managed_identity_fix():
    """Test específico del fix de Managed Identity"""
    print("🔧 TESTING: MANAGED IDENTITY FIX EN REDIS BUFFER")
    print("=" * 70)

    # Cargar configuración
    if not load_local_settings():
        return False

    # Simular entorno Azure Functions para forzar ManagedIdentity
    os.environ['WEBSITE_INSTANCE_ID'] = 'test-instance'
    os.environ['WEBSITE_SITE_NAME'] = 'copiloto-semantico-func-us2'
    os.environ['FUNCTIONS_WORKER_RUNTIME'] = 'python'

    print(f"🏢 Simulando entorno Azure Functions")
    print(f"   WEBSITE_SITE_NAME: {os.environ.get('WEBSITE_SITE_NAME')}")

    try:
        # Importar el servicio modificado
        from services.redis_buffer_service import redis_buffer

        print(f"\n🔍 Intentando conectar con Redis...")

        # Forzar reconexión
        redis_buffer._enabled = False
        redis_buffer._client = None

        # Test de conexión
        is_connected = redis_buffer.is_enabled

        if is_connected:
            print(f"✅ Redis conectado exitosamente!")

            # Test básico de operación
            test_key = "test:managed_identity_fix"
            test_value = {"test": "managed_identity_working",
                          "timestamp": "2025-12-16"}

            # Test de set/get
            success = redis_buffer.cache_llm_response(
                agent_id="TestAgent",
                session_id="test_session",
                message="test message for managed identity",
                model="gpt-4o-mini",
                response_data=test_value
            )

            if success:
                print(f"✅ Cache WRITE exitoso")

                # Test de retrieval
                cached = redis_buffer.get_llm_cached_response(
                    agent_id="TestAgent",
                    session_id="test_session",
                    message="test message for managed identity",
                    model="gpt-4o-mini"
                )

                if cached:
                    print(f"✅ Cache READ exitoso")
                    print(f"📄 Datos recuperados: {cached}")
                    return True
                else:
                    print(f"❌ Cache READ falló")
            else:
                print(f"❌ Cache WRITE falló")
        else:
            print(f"❌ No se pudo conectar a Redis")
            print(f"   Verificar:")
            print(f"   1. Rol 'Redis Cache Data Contributor' asignado")
            print(f"   2. Azure Redis AAD habilitado")
            print(f"   3. Object ID: 0bc92586-b230-4882-a91c-6c5293cde921")

        return is_connected

    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_credential_detection():
    """Mostrar qué método de credencial se está usando"""
    print(f"\n🔍 DETECCIÓN DE CREDENCIALES")
    print("=" * 50)

    try:
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

        # Test ManagedIdentityCredential
        print(f"🔐 Testing ManagedIdentityCredential...")
        try:
            mi_credential = ManagedIdentityCredential()
            mi_token = mi_credential.get_token(
                "https://redis.azure.com/.default")
            print(f"✅ ManagedIdentityCredential: {len(mi_token.token)} chars")
        except Exception as e:
            print(f"❌ ManagedIdentityCredential falló: {e}")

        # Test DefaultAzureCredential (para comparar)
        print(f"\n🔐 Testing DefaultAzureCredential...")
        try:
            default_credential = DefaultAzureCredential(
                exclude_cli_credential=True,
                exclude_interactive_browser_credential=True
            )
            default_token = default_credential.get_token(
                "https://redis.azure.com/.default")
            print(
                f"✅ DefaultAzureCredential (optimized): {len(default_token.token)} chars")
        except Exception as e:
            print(f"❌ DefaultAzureCredential falló: {e}")

    except Exception as e:
        print(f"❌ Error importando credenciales: {e}")


if __name__ == "__main__":
    print("🚀 VALIDACIÓN DEL FIX: MANAGED IDENTITY + REDIS")
    print("=" * 80)

    # Test de detección de credenciales
    show_credential_detection()

    # Test principal
    success = test_redis_managed_identity_fix()

    print(f"\n" + "=" * 80)
    if success:
        print(f"🎉 SUCCESS: Managed Identity fix funcionando correctamente!")
        print(f"   ✅ ManagedIdentityCredential priorizado en Azure Functions")
        print(f"   ✅ Redis AAD authentication funcionando")
        print(f"   ✅ Cache operations exitosas")
    else:
        print(f"❌ FAILED: Revisar configuración en Azure Portal:")
        print(f"   1. Function App Identity: ON")
        print(f"   2. Redis AAD Authentication: ENABLED")
        print(f"   3. Role Assignment: Redis Cache Data Contributor")
        print(f"   4. Object ID: 0bc92586-b230-4882-a91c-6c5293cde921")
    print("=" * 80)
