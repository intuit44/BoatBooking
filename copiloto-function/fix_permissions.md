# 🔧 Corrección de Permisos para Cosmos DB y App Insights

## 🎯 Problemas Identificados

### Cosmos DB

- **Error**: `Local Authorization is disabled. Use an AAD token to authorize all requests`
- **Causa**: El Cosmos DB tiene deshabilitada la autenticación por clave
- **Principal ID**: `16111244-a538-4a2f-9754-4be1d0a71dc8`

### App Insights

- **Error**: `InsufficientAccessError: The provided credentials have insufficient access`
- **Causa**: La Managed Identity no tiene permisos en Log Analytics

## 🚀 Soluciones

### Para Cosmos DB

#### Opción 1: Habilitar autenticación por clave (Más fácil)

```bash
az cosmosdb update \
  --name copiloto-cosmos \
  --resource-group boat-rental-app-group \
  --disable-local-auth false
```

#### Opción 2: Configurar RBAC (Más seguro)

```bash
# Asignar rol "Cosmos DB Built-in Data Contributor"
az cosmosdb sql role assignment create \
  --account-name copiloto-cosmos \
  --resource-group boat-rental-app-group \
  --scope "/" \
  --principal-id 16111244-a538-4a2f-9754-4be1d0a71dc8 \
  --role-definition-id 00000000-0000-0000-0000-000000000002
```

### Para App Insights

```bash
# Obtener el workspace ID y resource group
WORKSPACE_ID="3e355ae8-3dd7-44ad-b"  # Tu workspace ID completo
RESOURCE_GROUP="boat-rental-app-group"  # Ajustar si es diferente

# Asignar rol "Log Analytics Reader"
az role assignment create \
  --assignee 16111244-a538-4a2f-9754-4be1d0a71dc8 \
  --role "Log Analytics Reader" \
  --scope "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.OperationalInsights/workspaces/copiloto-workspace"
```

## 🔍 Verificar Permisos Actuales

### Cosmos DB

```bash
# Ver configuración actual
az cosmosdb show \
  --name copiloto-cosmos \
  --resource-group boat-rental-app-group \
  --query "{name:name, disableLocalAuth:disableLocalAuth}"

# Ver asignaciones de roles
az cosmosdb sql role assignment list \
  --account-name copiloto-cosmos \
  --resource-group boat-rental-app-group
```

### App Insights

```bash
# Ver asignaciones de roles en el workspace
az role assignment list \
  --assignee 16111244-a538-4a2f-9754-4be1d0a71dc8 \
  --scope "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group"
```

## 🎯 Comandos de Corrección Rápida

### Ejecutar todo de una vez

```bash
# 1. Habilitar autenticación local en Cosmos DB (más fácil)
az cosmosdb update \
  --name copiloto-cosmos \
  --resource-group boat-rental-app-group \
  --disable-local-auth false

# 2. Asignar permisos de Log Analytics
az role assignment create \
  --assignee 16111244-a538-4a2f-9754-4be1d0a71dc8 \
  --role "Log Analytics Reader" \
  --scope "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.OperationalInsights/workspaces/copiloto-workspace"

# 3. Verificar que los cambios se aplicaron
echo "✅ Verificando Cosmos DB..."
az cosmosdb show --name copiloto-cosmos --resource-group boat-rental-app-group --query "disableLocalAuth"

echo "✅ Verificando permisos Log Analytics..."
az role assignment list --assignee 16111244-a538-4a2f-9754-4be1d0a71dc8 --query "[?roleDefinitionName=='Log Analytics Reader']"
```

## 📋 Checklist Post-Corrección

- [ ] Cosmos DB permite autenticación local O tiene RBAC configurado
- [ ] Managed Identity tiene rol "Log Analytics Reader"
- [ ] Ejecutar `python debug_cosmos_appinsights.py` para verificar
- [ ] Probar endpoints: `/api/verificar-cosmos` y `/api/verificar-app-insights`

## 🔄 Si Persisten los Problemas

### Para Cosmos DB

- Verificar que el nombre del recurso sea correcto: `copiloto-cosmos`
- Verificar que el resource group sea correcto: `boat-rental-app-group`
- Esperar 5-10 minutos para que los cambios se propaguen

### Para App Insights

- Verificar el nombre exacto del workspace de Log Analytics
- Puede necesitar permisos a nivel de suscripción si el workspace está en otro RG
- Verificar que el workspace ID sea completo (no truncado)
