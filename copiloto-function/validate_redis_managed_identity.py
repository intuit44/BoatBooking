#!/usr/bin/env python3
"""
Script para cargar variables de local.settings.json y validar Redis específicamente
"""
import json
import os
from azure.identity import DefaultAzureCredential
import redis
import ssl


def load_local_settings():
    """Cargar variables desde local.settings.json"""
    print("📂 CARGANDO LOCAL.SETTINGS.JSON")
    print("=" * 50)

    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)

        values = settings.get('Values', {})
        loaded_count = 0

        for key, value in values.items():
            if key not in os.environ:
                os.environ[key] = value
                loaded_count += 1
                if 'KEY' in key:
                    print(f"✅ {key}: {value[:8]}...{value[-8:]}")
                else:
                    print(f"✅ {key}: {value}")

        print(f"\n📊 Total variables cargadas: {loaded_count}")
        return True

    except FileNotFoundError:
        print("❌ local.settings.json no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error cargando settings: {e}")
        return False


def test_redis_with_managed_identity():
    """Probar conexión específica a Redis con Managed Identity"""
    print(f"\n🔴 TEST ESPECÍFICO DE REDIS CON MANAGED IDENTITY")
    print("=" * 60)

    redis_host = os.environ.get('REDIS_HOST')
    redis_port = int(os.environ.get('REDIS_PORT', '10000'))

    if not redis_host:
        print("❌ REDIS_HOST no definido")
        return False

    print(f"🎯 Target: {redis_host}:{redis_port}")

    try:
        # 1. Obtener token para Redis
        credential = DefaultAzureCredential()
        token = credential.get_token("https://redis.azure.com/.default")

        print(f"✅ Token obtenido: {len(token.token)} chars")

        # 2. Configurar SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        print(f"🔐 SSL context configurado")

        # 3. Intentar conexión con Managed Identity
        # En Redis con AAD, el username es el token y password vacío
        print(f"🔌 Intentando conexión con token como username...")

        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            username=token.token,  # Token como username
            password="",           # Password vacío
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            socket_timeout=10,
            decode_responses=True
        )

        # Test de ping
        result = client.ping()
        print(f"✅ Redis PING exitoso: {result}")

        # Test básico de operación
        test_key = "test:managed_identity"
        client.set(test_key, "test_value", ex=60)
        value = client.get(test_key)

        print(f"✅ Redis SET/GET exitoso: {value}")

        client.delete(test_key)
        print(f"✅ Redis DELETE exitoso")

        return True

    except redis.AuthenticationError as auth_err:
        print(f"❌ AUTHENTICATION ERROR: {auth_err}")
        print(f"   🔍 Esto indica problema de roles/permisos en Azure")
        return False
    except redis.ConnectionError as conn_err:
        print(f"❌ CONNECTION ERROR: {conn_err}")
        return False
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        return False


def test_redis_with_key():
    """Probar conexión con REDIS_KEY tradicional para comparar"""
    print(f"\n🔑 TEST COMPARATIVO CON REDIS_KEY")
    print("=" * 50)

    redis_host = os.environ.get('REDIS_HOST')
    redis_port = int(os.environ.get('REDIS_PORT', '10000'))
    redis_key = os.environ.get('REDIS_KEY')

    if not redis_key:
        print("❌ REDIS_KEY no definido")
        return False

    try:
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_key,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            socket_timeout=10,
            decode_responses=True
        )

        result = client.ping()
        print(f"✅ Redis Key auth PING exitoso: {result}")

        return True

    except Exception as e:
        print(f"❌ Redis Key auth falló: {e}")
        return False


def validate_azure_redis_config():
    """Mostrar información para validar configuración en Portal"""
    print(f"\n🔍 INFORMACIÓN PARA VALIDAR EN AZURE PORTAL")
    print("=" * 60)

    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default")

        # Decodificar token para obtener IDs
        import base64
        parts = token.token.split('.')
        if len(parts) >= 2:
            payload = parts[1] + '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            token_data = json.loads(decoded)

            object_id = token_data.get('oid')
            app_id = token_data.get('appid')
            tenant_id = token_data.get('tid')

            print(f"📋 IDENTIDAD ACTUAL:")
            print(f"   Object ID (Principal ID): {object_id}")
            print(f"   Application ID: {app_id}")
            print(f"   Tenant ID: {tenant_id}")

            print(f"\n🎯 VERIFICACIONES EN PORTAL:")
            print(f"1. Azure Redis Cache > Access Control (IAM)")
            print(f"   - Buscar role assignment para Object ID: {object_id}")
            print(
                f"   - Debe tener rol: 'Redis Cache Contributor' o 'Redis Cache Data Contributor'")

            print(f"\n2. Azure Redis Cache > Authentication")
            print(f"   - Microsoft Entra authentication: ENABLED")
            print(f"   - Access keys authentication: ENABLED (opcional)")

            print(f"\n3. Function App > Identity")
            print(f"   - System assigned: ON")
            print(f"   - Object (principal) ID debe coincidir: {object_id}")

    except Exception as e:
        print(f"❌ Error obteniendo información de identidad: {e}")


if __name__ == "__main__":
    print("🔧 VALIDACIÓN ESPECÍFICA DE REDIS + MANAGED IDENTITY")
    print("=" * 80)

    # 1. Cargar settings locales
    load_local_settings()

    # 2. Test con Managed Identity
    mi_success = test_redis_with_managed_identity()

    # 3. Test comparativo con Key
    key_success = test_redis_with_key()

    # 4. Información para portal
    validate_azure_redis_config()

    print(f"\n" + "=" * 80)
    print(f"📊 RESUMEN:")
    print(f"   Managed Identity Auth: {'✅' if mi_success else '❌'}")
    print(f"   Redis Key Auth: {'✅' if key_success else '❌'}")

    if not mi_success and key_success:
        print(f"\n🎯 CONCLUSIÓN: Managed Identity no tiene permisos correctos en Redis")
        print(f"   - Redis funciona con access key")
        print(f"   - Managed Identity requiere configuración de roles")
    elif mi_success:
        print(f"\n🎯 CONCLUSIÓN: Managed Identity funcionando correctamente")
    else:
        print(f"\n🎯 CONCLUSIÓN: Problemas generales de conectividad a Redis")

    print("=" * 80)
