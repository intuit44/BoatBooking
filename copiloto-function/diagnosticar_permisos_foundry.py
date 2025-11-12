"""
Script de diagnóstico completo para permisos de Azure AI Foundry
Identifica el problema exacto de por qué los roles no se asignan correctamente
"""
import subprocess
import json
import os
from datetime import datetime


def run_command(cmd):
    """Ejecuta comando y retorna resultado"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_json_output(output):
    """Intenta parsear JSON de forma segura"""
    try:
        return json.loads(output) if output else None
    except:
        return None


print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO DE PERMISOS AZURE AI FOUNDRY")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# 1. Verificar cuenta actual
print("1️⃣ CUENTA ACTUAL DE AZURE CLI")
print("-" * 80)
account = run_command("az account show")
if account["success"]:
    acc_data = parse_json_output(account["stdout"])
    if acc_data:
        print(f"✅ Usuario: {acc_data.get('user', {}).get('name', 'N/A')}")
        print(f"✅ Tipo: {acc_data.get('user', {}).get('type', 'N/A')}")
        print(f"✅ Subscription: {acc_data.get('name', 'N/A')}")
        print(f"✅ Subscription ID: {acc_data.get('id', 'N/A')}")
        print(f"✅ Tenant ID: {acc_data.get('tenantId', 'N/A')}")
else:
    print(f"❌ Error: {account.get('stderr', 'Unknown')}")

# 2. Verificar Service Principal
print("\n2️⃣ SERVICE PRINCIPAL (Function App Identity)")
print("-" * 80)
sp_id = "6c04cf21-3f90-48fc-945e-cd9268ffd30e"
sp_info = run_command(f"az ad sp show --id {sp_id}")
if sp_info["success"]:
    sp_data = parse_json_output(sp_info["stdout"])
    if sp_data:
        print(f"✅ Display Name: {sp_data.get('displayName', 'N/A')}")
        print(f"✅ App ID: {sp_data.get('appId', 'N/A')}")
        print(f"✅ Object ID: {sp_data.get('id', 'N/A')}")
        print(
            f"✅ Service Principal Type: {sp_data.get('servicePrincipalType', 'N/A')}")
else:
    print(
        f"❌ Service Principal NO encontrado: {sp_info.get('stderr', 'Unknown')}")

# 3. Verificar recurso Azure AI
print("\n3️⃣ RECURSO AZURE AI (AgenteOpenAi)")
print("-" * 80)
resource_info = run_command(
    "az cognitiveservices account show "
    "--name AgenteOpenAi "
    "--resource-group boat-rental-app-group"
)
if resource_info["success"]:
    res_data = parse_json_output(resource_info["stdout"])
    if res_data:
        print(f"✅ Nombre: {res_data.get('name', 'N/A')}")
        print(f"✅ Tipo: {res_data.get('kind', 'N/A')}")
        print(f"✅ Location: {res_data.get('location', 'N/A')}")
        print(f"✅ Resource ID: {res_data.get('id', 'N/A')}")
        resource_id = res_data.get('id', '')
else:
    print(f"❌ Recurso NO encontrado: {resource_info.get('stderr', 'Unknown')}")
    resource_id = ""

# 4. Listar TODOS los roles asignados al Service Principal
print("\n4️⃣ ROLES ASIGNADOS AL SERVICE PRINCIPAL")
print("-" * 80)
roles = run_command(f"az role assignment list --assignee {sp_id} --all")
if roles["success"]:
    roles_data = parse_json_output(roles["stdout"])
    if roles_data and len(roles_data) > 0:
        print(f"✅ Total de roles asignados: {len(roles_data)}\n")
        for idx, role in enumerate(roles_data, 1):
            print(f"  {idx}. Rol: {role.get('roleDefinitionName', 'N/A')}")
            print(f"     Scope: {role.get('scope', 'N/A')}")
            print(f"     Principal Type: {role.get('principalType', 'N/A')}")
            print(f"     Created: {role.get('createdOn', 'N/A')}")
            print()
    else:
        print("❌ NO HAY ROLES ASIGNADOS AL SERVICE PRINCIPAL")
        print("   Esto explica por qué falla la autenticación")
else:
    print(f"❌ Error listando roles: {roles.get('stderr', 'Unknown')}")

# 5. Verificar roles específicos necesarios
print("\n5️⃣ VERIFICACIÓN DE ROLES NECESARIOS")
print("-" * 80)
required_roles = [
    "Cognitive Services OpenAI Contributor",
    "Azure AI Developer",
    "Cognitive Services User"
]

for role_name in required_roles:
    check = run_command(
        f"az role assignment list "
        f"--assignee {sp_id} "
        f"--role \"{role_name}\" "
        f"--scope \"{resource_id}\""
    )
    if check["success"]:
        check_data = parse_json_output(check["stdout"])
        if check_data and len(check_data) > 0:
            print(f"✅ {role_name}: ASIGNADO")
        else:
            print(f"❌ {role_name}: NO ASIGNADO")
    else:
        print(f"⚠️ {role_name}: ERROR AL VERIFICAR")

# 6. Verificar permisos del usuario actual
print("\n6️⃣ PERMISOS DEL USUARIO ACTUAL")
print("-" * 80)
user_roles = run_command(
    f"az role assignment list "
    f"--scope \"{resource_id}\" "
    f"--include-inherited"
)
if user_roles["success"]:
    user_data = parse_json_output(user_roles["stdout"])
    if user_data:
        print(f"✅ Total de asignaciones en el recurso: {len(user_data)}")
        # Verificar si el usuario tiene permisos para asignar roles
        can_assign = any(
            "Owner" in r.get("roleDefinitionName", "") or
            "User Access Administrator" in r.get("roleDefinitionName", "")
            for r in user_data
        )
        if can_assign:
            print("✅ El usuario TIENE permisos para asignar roles")
        else:
            print("❌ El usuario NO TIENE permisos para asignar roles")
            print("   Necesitas rol 'Owner' o 'User Access Administrator'")

# 7. Intentar asignar rol y capturar error detallado
print("\n7️⃣ INTENTO DE ASIGNACIÓN DE ROL")
print("-" * 80)
print("Intentando asignar 'Azure AI Developer'...")
assign = run_command(
    f"az role assignment create "
    f"--assignee {sp_id} "
    f"--role \"Azure AI Developer\" "
    f"--scope \"{resource_id}\""
)
if assign["success"]:
    print("✅ Rol asignado exitosamente")
    assign_data = parse_json_output(assign["stdout"])
    if assign_data:
        print(f"   Assignment ID: {assign_data.get('id', 'N/A')}")
else:
    print(f"❌ Error asignando rol:")
    print(f"   {assign.get('stderr', 'Unknown')}")

# 8. Verificar si hay múltiples cuentas/tenants
print("\n8️⃣ VERIFICACIÓN DE MÚLTIPLES CUENTAS")
print("-" * 80)
accounts = run_command("az account list")
if accounts["success"]:
    acc_list = parse_json_output(accounts["stdout"])
    if acc_list and len(acc_list) > 1:
        print(f"⚠️ MÚLTIPLES CUENTAS DETECTADAS: {len(acc_list)}")
        print("   Esto puede causar conflictos de permisos\n")
        for idx, acc in enumerate(acc_list, 1):
            is_default = "✓" if acc.get("isDefault") else " "
            print(f"  [{is_default}] {idx}. {acc.get('name', 'N/A')}")
            print(f"      User: {acc.get('user', {}).get('name', 'N/A')}")
            print(f"      Tenant: {acc.get('tenantId', 'N/A')}")
            print()
    else:
        print("✅ Solo una cuenta configurada")

# 9. Verificar variables de entorno
print("\n9️⃣ VARIABLES DE ENTORNO RELEVANTES")
print("-" * 80)
env_vars = [
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TENANT_ID",
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_AI_ENDPOINT"
]
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Ocultar secretos
        if "SECRET" in var or "KEY" in var:
            display = f"{value[:8]}...{value[-4:]}" if len(
                value) > 12 else "***"
        else:
            display = value
        print(f"✅ {var}: {display}")
    else:
        print(f"❌ {var}: NO CONFIGURADO")

# 10. Recomendaciones
print("\n" + "=" * 80)
print("📋 RECOMENDACIONES")
print("=" * 80)

if not roles["success"] or (roles_data and len(roles_data) == 0):
    print("""
❌ PROBLEMA IDENTIFICADO: El Service Principal NO tiene roles asignados

SOLUCIONES POSIBLES:

1. Verificar que estás usando la cuenta correcta:
   az account show
   
2. Si tienes múltiples cuentas, cambiar a la correcta:
   az account set --subscription <SUBSCRIPTION_ID>
   
3. Asignar rol con cuenta que tenga permisos de Owner:
   az role assignment create \\
     --assignee 6c04cf21-3f90-48fc-945e-cd9268ffd30e \\
     --role "Azure AI Developer" \\
     --scope "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.CognitiveServices/accounts/AgenteOpenAi"

4. Si el problema persiste, usar Azure Portal:
   - Ir a recurso AgenteOpenAi
   - Access Control (IAM)
   - Add role assignment
   - Buscar el Service Principal por App ID: 04dcd80d-30fe-4895-b199-26bb4e291663
   - Asignar rol "Azure AI Developer"
""")
else:
    print("✅ El Service Principal tiene roles asignados")
    print("   Si aún falla, espera 5-10 minutos para propagación")

print("\n" + "=" * 80)
print("Diagnóstico completado")
print("=" * 80)
