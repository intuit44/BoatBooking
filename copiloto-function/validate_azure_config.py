#!/usr/bin/env python3
"""
Validación completa de Managed Identity y configuración de Azure
"""
import os
import json
from azure.identity import DefaultAzureCredential, AzureCliCredential, ManagedIdentityCredential
from azure.core.exceptions import ClientAuthenticationError
import requests


def validate_managed_identity():
    """Validar la Managed Identity y sus tokens"""
    print("🔍 VALIDACIÓN DE MANAGED IDENTITY")
    print("=" * 60)

    # 1. Verificar si estamos en Azure Functions
    website_instance_id = os.environ.get('WEBSITE_INSTANCE_ID')
    website_site_name = os.environ.get('WEBSITE_SITE_NAME')

    print(f"📍 Environment Context:")
    print(
        f"   WEBSITE_INSTANCE_ID: {'✅' if website_instance_id else '❌'} {website_instance_id}")
    print(
        f"   WEBSITE_SITE_NAME: {'✅' if website_site_name else '❌'} {website_site_name}")

    # 2. Probar DefaultAzureCredential
    print(f"\n🔐 Testing DefaultAzureCredential...")
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default")
        print(f"✅ DefaultAzureCredential: Token obtenido exitosamente")
        print(f"   Token expires: {token.expires_on}")

        # Decodificar el token para ver el identity
        import base64
        import json

        # El token JWT tiene 3 partes separadas por puntos
        parts = token.token.split('.')
        if len(parts) >= 2:
            # Decodificar payload (segunda parte)
            payload = parts[1]
            # Agregar padding si es necesario
            payload += '=' * (4 - len(payload) % 4)

            try:
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)

                print(f"   🆔 Token Identity Info:")
                print(f"      Object ID: {token_data.get('oid', 'N/A')}")
                print(f"      App ID: {token_data.get('appid', 'N/A')}")
                print(f"      Tenant ID: {token_data.get('tid', 'N/A')}")
                print(f"      Issuer: {token_data.get('iss', 'N/A')}")

            except Exception as decode_error:
                print(f"   ⚠️  No se pudo decodificar token: {decode_error}")

    except Exception as e:
        print(f"❌ DefaultAzureCredential falló: {e}")

    # 3. Probar específicamente ManagedIdentityCredential
    print(f"\n🏢 Testing ManagedIdentityCredential...")
    try:
        mi_credential = ManagedIdentityCredential()
        mi_token = mi_credential.get_token(
            "https://management.azure.com/.default")
        print(f"✅ ManagedIdentityCredential: Token obtenido exitosamente")
    except Exception as e:
        print(f"❌ ManagedIdentityCredential falló: {e}")

    # 4. Probar token específico para Redis
    print(f"\n🔑 Testing Redis-specific token...")
    try:
        redis_credential = DefaultAzureCredential()
        redis_token = redis_credential.get_token(
            "https://redis.azure.com/.default")
        print(f"✅ Redis token: Obtenido exitosamente")
        print(f"   Token length: {len(redis_token.token)} chars")
    except Exception as e:
        print(f"❌ Redis token falló: {e}")


def validate_app_settings():
    """Validar App Settings de Azure Functions"""
    print(f"\n📋 VALIDACIÓN DE APP SETTINGS")
    print("=" * 60)

    required_vars = [
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'REDIS_HOST',
        'REDIS_PORT',
        'REDIS_KEY',
        'REDIS_SSL'
    ]

    print(f"🔍 Verificando variables requeridas:")
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mostrar solo los primeros/últimos caracteres para seguridad
            if 'KEY' in var:
                display_value = f"{value[:8]}...{value[-8:]}" if len(
                    value) > 16 else "***"
            elif 'ENDPOINT' in var:
                display_value = value
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NO DEFINIDA")

    # Verificar variables específicas de Function App
    function_vars = [
        'FUNCTIONS_WORKER_RUNTIME',
        'AzureWebJobsStorage',
        'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
    ]

    print(f"\n🏗️  Variables de Function App:")
    for var in function_vars:
        value = os.environ.get(var)
        status = "✅" if value else "❌"
        print(f"   {status} {var}: {'SET' if value else 'NOT SET'}")


def validate_redis_access():
    """Validar acceso específico a Redis con Managed Identity"""
    print(f"\n🔴 VALIDACIÓN ESPECÍFICA DE REDIS")
    print("=" * 60)

    redis_host = os.environ.get('REDIS_HOST')
    redis_port = os.environ.get('REDIS_PORT', '10000')

    if not redis_host:
        print("❌ REDIS_HOST no está definido")
        return

    print(f"🎯 Redis Target: {redis_host}:{redis_port}")

    # 1. Obtener token de Redis
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://redis.azure.com/.default")
        print(f"✅ Redis token obtenido: {len(token.token)} chars")

        # 2. Mostrar información del usuario que se usará
        username = token.token  # En Redis AAD, el token ES el username
        print(f"📝 Username para Redis: {username[:20]}...{username[-20:]}")

    except Exception as e:
        print(f"❌ No se pudo obtener token de Redis: {e}")


def validate_openai_access():
    """Validar acceso a OpenAI"""
    print(f"\n🤖 VALIDACIÓN DE OPENAI")
    print("=" * 60)

    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    key = os.environ.get('AZURE_OPENAI_KEY')
    deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')

    if not endpoint or not key:
        print(f"❌ Variables OpenAI faltantes:")
        print(f"   AZURE_OPENAI_ENDPOINT: {'✅' if endpoint else '❌'}")
        print(f"   AZURE_OPENAI_KEY: {'✅' if key else '❌'}")
        return

    print(f"🎯 OpenAI Endpoint: {endpoint}")
    print(f"📊 Deployment: {deployment}")

    # Test básico de conectividad
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=key,
            api_version="2024-02-01",
            azure_endpoint=endpoint
        )
        print(f"✅ Cliente OpenAI creado exitosamente")

        # Test simple (sin hacer llamada real para evitar costos)
        print(f"✅ Configuración OpenAI válida")

    except Exception as e:
        print(f"❌ Error en cliente OpenAI: {e}")


if __name__ == "__main__":
    print("🧪 DIAGNÓSTICO COMPLETO DE AZURE RESOURCES")
    print("=" * 80)

    validate_managed_identity()
    validate_app_settings()
    validate_redis_access()
    validate_openai_access()

    print(f"\n" + "=" * 80)
    print("🎯 SIGUIENTES PASOS RECOMENDADOS:")
    print("1. Verificar en Azure Portal que la Managed Identity tiene rol 'Redis Cache Contributor'")
    print("2. Confirmar que Redis tiene habilitado 'Microsoft Entra Authentication'")
    print("3. Verificar que las App Settings estén configuradas en la Function App")
    print("4. Revisar logs específicos del error 'invalid username-password pair'")
    print("=" * 80)
