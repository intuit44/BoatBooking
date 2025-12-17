#!/usr/bin/env python3
"""
Guía paso a paso para corregir Managed Identity en Azure Redis
"""
import json
import base64
from azure.identity import DefaultAzureCredential


def get_managed_identity_info():
    """Obtener información de la Managed Identity actual"""
    print("🔍 INFORMACIÓN DE MANAGED IDENTITY ACTUAL")
    print("=" * 70)

    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default")

        # Decodificar token JWT
        parts = token.token.split('.')
        if len(parts) >= 2:
            # Agregar padding necesario para base64
            payload_part = parts[1]
            payload_part += '=' * (4 - len(payload_part) % 4)

            decoded_bytes = base64.b64decode(payload_part)
            token_data = json.loads(decoded_bytes)

            object_id = token_data.get('oid', 'N/A')
            app_id = token_data.get('appid', 'N/A')
            tenant_id = token_data.get('tid', 'N/A')
            issuer = token_data.get('iss', 'N/A')

            print(f"✅ Managed Identity detectada:")
            print(f"   📋 Object ID (Principal ID): {object_id}")
            print(f"   🆔 Application ID: {app_id}")
            print(f"   🏢 Tenant ID: {tenant_id}")
            print(f"   🔗 Issuer: {issuer}")

            return {
                'object_id': object_id,
                'app_id': app_id,
                'tenant_id': tenant_id,
                'issuer': issuer
            }

    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")
        return None


def show_azure_portal_steps(identity_info):
    """Mostrar pasos específicos para configurar en Azure Portal"""
    print(f"\n🎯 PASOS PARA CORREGIR EN AZURE PORTAL")
    print("=" * 70)

    if not identity_info:
        print("❌ No se pudo obtener información de identidad")
        return

    object_id = identity_info['object_id']

    print(f"📍 PASO 1: VERIFICAR FUNCTION APP")
    print(f"   1. Ir a: Azure Portal > Function Apps > copiloto-semantico-func-us2")
    print(f"   2. Settings > Identity > System assigned")
    print(f"   3. Verificar que Status = ON")
    print(f"   4. Confirmar Object (principal) ID: {object_id}")

    print(f"\n📍 PASO 2: CONFIGURAR AZURE REDIS CACHE")
    print(f"   1. Ir a: Azure Portal > Azure Cache for Redis > Managed-redis-copiloto")
    print(f"   2. Settings > Authentication")
    print(f"   3. Configurar:")
    print(f"      ✅ Microsoft Entra authentication: ENABLED")
    print(f"      ✅ Access Keys authentication: ENABLED (para fallback)")

    print(f"\n📍 PASO 3: ASIGNAR ROLES DE ACCESO")
    print(f"   1. En Azure Redis > Access control (IAM)")
    print(f"   2. Clic en '+ Add' > Add role assignment")
    print(f"   3. Seleccionar role: 'Redis Cache Data Contributor'")
    print(f"   4. Assign access to: 'Managed Identity'")
    print(f"   5. Members > + Select members")
    print(f"   6. Subscription: Seleccionar subscription actual")
    print(f"   7. Managed Identity: Function App")
    print(f"   8. Buscar y seleccionar: copiloto-semantico-func-us2")
    print(
        f"   9. IMPORTANTE: Verificar que el Object ID coincida: {object_id}")
    print(f"   10. Save")

    print(f"\n📍 PASO 4: VERIFICAR CONFIGURACIÓN")
    print(f"   1. En Azure Redis > Access control (IAM) > Role assignments")
    print(f"   2. Buscar: 'Redis Cache Data Contributor'")
    print(f"   3. Confirmar que aparece: copiloto-semantico-func-us2")
    print(f"   4. Verificar Object ID: {object_id}")


def show_alternative_roles():
    """Mostrar roles alternativos si el principal no funciona"""
    print(f"\n🔧 ROLES ALTERNATIVOS (si 'Data Contributor' no funciona)")
    print("=" * 70)

    print(f"Intentar en este orden:")
    print(f"   1️⃣ Redis Cache Data Owner")
    print(f"   2️⃣ Redis Cache Contributor")
    print(f"   3️⃣ Redis Cache Data Reader (solo para lectura)")

    print(f"\n⚠️  NOTAS IMPORTANTES:")
    print(f"   - Los cambios pueden tomar 5-10 minutos en propagarse")
    print(f"   - Reiniciar la Function App después de cambios de roles")
    print(f"   - Verificar que Redis tenga AAD habilitado en 'Authentication'")


def show_testing_commands():
    """Mostrar comandos para verificar después de los cambios"""
    print(f"\n🧪 COMANDOS PARA VERIFICAR DESPUÉS DE CAMBIOS")
    print("=" * 70)

    print(f"1️⃣ Reiniciar Function App:")
    print(f"   az functionapp restart --name copiloto-semantico-func-us2 --resource-group boat-rental-app-group")

    print(f"\n2️⃣ Volver a ejecutar validación:")
    print(f"   python validate_redis_managed_identity.py")

    print(f"\n3️⃣ Verificar logs en Function App:")
    print(f"   - Portal > Function App > Monitor > Live metrics")
    print(f"   - Buscar logs de conexión Redis")

    print(f"\n4️⃣ Test manual de token:")
    print(f"   python -c \"from azure.identity import DefaultAzureCredential; c=DefaultAzureCredential(); t=c.get_token('https://redis.azure.com/.default'); print('✅ Token OK:', len(t.token), 'chars')\"")


if __name__ == "__main__":
    print("🚀 GUÍA DE CONFIGURACIÓN: MANAGED IDENTITY + AZURE REDIS")
    print("=" * 80)

    # Obtener información de identidad
    identity_info = get_managed_identity_info()

    # Mostrar pasos específicos
    show_azure_portal_steps(identity_info)

    # Mostrar roles alternativos
    show_alternative_roles()

    # Mostrar comandos de testing
    show_testing_commands()

    print(f"\n" + "=" * 80)
    print(f"🎯 RESUMEN:")
    print(f"   Problem: Managed Identity sin permisos en Redis")
    print(f"   Solution: Asignar role 'Redis Cache Data Contributor'")
    print(
        f"   Key Info: Object ID {identity_info['object_id'] if identity_info else 'N/A'}")
    print("=" * 80)
