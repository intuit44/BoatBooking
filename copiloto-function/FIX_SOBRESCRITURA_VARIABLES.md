# ✅ FIX: Sobrescritura de Variables de Entorno

## 🐛 Problema Original

Cuando el agente llamó `/api/configurar-app-settings` para agregar `AZURE_SEARCH_SKU`, **sobrescribió todas las variables** dejando solo:

```json
{
  "AZURE_SEARCH_SKU": "Standard S1"
}
```

**Causa**: El endpoint hacía `PUT` directo sin merge, reemplazando toda la configuración.

## ✅ Soluciones Implementadas

### 1. Robustecer el Endpoint (✅ COMPLETADO)

**Archivo**: `function_app.py` (función `set_app_settings_rest`, línea ~760)

**Cambio**:

```python
# ANTES (sobrescribía todo)
body = {"properties": normalized_settings}
_arm_put(path, body)

# DESPUÉS (hace merge seguro)
# 1. GET settings existentes
existing_settings = get_current_settings()

# 2. MERGE: existentes + nuevos
merged_settings = existing_settings.copy()
merged_settings.update(normalized_settings)

# 3. PUT con settings merged
body = {"properties": merged_settings}
_arm_put(path, body)
```

**Beneficio**: Ahora el endpoint **preserva** todas las variables existentes y solo actualiza/agrega las nuevas.

### 2. Recuperar Variables (✅ COMPLETADO)

**Script**: `recuperar_variables_portal.ps1`

**Resultado**:

- ✅ 46 variables recuperadas desde `local.settings.json`
- ✅ Subidas al portal en 5 lotes
- ✅ Todas las configuraciones restauradas

## 📊 Variables Recuperadas

| Categoría | Variables | Estado |
|-----------|-----------|--------|
| Azure Functions | AzureWebJobsStorage, FUNCTIONS_WORKER_RUNTIME, etc. | ✅ |
| OpenAI | AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT | ✅ |
| Search | AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY | ✅ |
| Cosmos DB | COSMOSDB_KEY, COSMOS_DATABASE | ✅ |
| Storage | AZURE_STORAGE_CONNECTION_STRING | ✅ |
| Bing | BING_SEARCH_KEY, BING_SEARCH_ENDPOINT | ✅ |
| App Insights | APPLICATIONINSIGHTS_CONNECTION_STRING | ✅ |
| **Total** | **46 variables** | **✅** |

## 🔒 Protección Implementada

### Merge Automático

El endpoint ahora:

1. **Lee** configuración actual
2. **Combina** con nuevos valores
3. **Actualiza** sin perder nada

### Logging Mejorado

```
🔍 Obteniendo settings existentes antes de actualizar...
✅ Settings existentes: 45 variables
🔄 Merge: 45 existentes + 1 nuevos = 46 total
```

## 🧪 Verificación

### Test del Endpoint Mejorado

```bash
# Agregar una variable sin perder las demás
curl -X POST http://localhost:7071/api/configurar-app-settings \
  -H "Content-Type: application/json" \
  -d '{
    "function_app": "copiloto-semantico-func-us2",
    "resource_group": "boat-rental-app-group",
    "settings": {
      "NEW_VARIABLE": "test_value"
    }
  }'
```

**Resultado esperado**:

```json
{
  "ok": true,
  "updated": ["NEW_VARIABLE"],
  "total_settings": 47,
  "merge_applied": true
}
```

### Verificar en Portal

```bash
az functionapp config appsettings list \
  -g boat-rental-app-group \
  -n copiloto-semantico-func-us2 \
  --query "length([?value != null])"
```

**Resultado esperado**: `46` (todas las variables presentes)

## 📝 Lecciones Aprendidas

### ❌ Antipatrón

```python
# NUNCA hacer esto
settings = {"NEW_VAR": "value"}
web_client.update_application_settings(rg, app, settings)  # ❌ Sobrescribe todo
```

### ✅ Patrón Correcto

```python
# SIEMPRE hacer merge
existing = web_client.list_application_settings(rg, app).properties
existing.update(new_settings)
web_client.update_application_settings(rg, app, existing)  # ✅ Preserva todo
```

## 🚀 Próximos Pasos

1. **Reiniciar Function App** para aplicar variables recuperadas
2. **Verificar** que todos los endpoints funcionan correctamente
3. **Documentar** este patrón para futuros endpoints

## 📊 Estado Final

- ✅ Endpoint robustecido con merge automático
- ✅ 46 variables recuperadas en el portal
- ✅ Protección contra sobrescrituras futuras
- ✅ Logging mejorado para debugging
- 🟡 Function App pendiente de reinicio

---

**Fecha**: 2025-11-02
**Archivos modificados**:

- `function_app.py` (set_app_settings_rest)
- `recuperar_variables_portal.ps1` (nuevo)
**Impacto**: Crítico - Previene pérdida de configuración
**Estado**: ✅ Resuelto y protegido
