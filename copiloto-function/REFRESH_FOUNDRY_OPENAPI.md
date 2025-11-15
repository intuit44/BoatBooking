# 🔄 Forzar Actualización del OpenAPI en Azure AI Foundry

## 🚨 Problema Detectado

```
Error: openapi_function_not_found
No function call found for: CopilotoFunctionApp_probarEndpoint
```

**Causa**: Foundry tiene cacheada una versión antigua del OpenAPI que incluía `/api/probar-endpoint`.

## ✅ Solución: Refrescar Catálogo de Herramientas

### Opción 1: Actualizar desde Azure Portal (Recomendado)

1. **Ir a Azure AI Foundry Portal**
   - URL: https://ai.azure.com
   - Navegar a tu proyecto

2. **Actualizar la Conexión de API**
   ```
   Settings → Connections → [Tu conexión OpenAPI]
   → Edit → Re-import OpenAPI Spec
   ```

3. **Forzar Re-validación**
   - Eliminar la conexión existente
   - Crear nueva conexión apuntando a:
     ```
     https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi
     ```

4. **Verificar Endpoints Disponibles**
   - Debe mostrar SOLO estos endpoints:
     - ✅ `/api/copiloto` (router semántico)
     - ✅ `/api/diagnostico-recursos`
     - ✅ `/api/crear-contenedor`
     - ✅ `/api/ejecutar-cli`
     - ✅ `/api/bridge-cli`
     - ✅ `/api/agent-output`
     - ❌ `/api/probar-endpoint` (NO debe aparecer)
     - ❌ `/api/invocar` (NO debe aparecer)

### Opción 2: Actualizar vía Azure CLI

```bash
# 1. Obtener el ID de la conexión
az ml connection list --resource-group <tu-rg> --workspace-name <tu-workspace>

# 2. Actualizar la conexión
az ml connection update \
  --name copiloto-openapi \
  --resource-group <tu-rg> \
  --workspace-name <tu-workspace> \
  --file updated-connection.yaml

# 3. Verificar
az ml connection show \
  --name copiloto-openapi \
  --resource-group <tu-rg> \
  --workspace-name <tu-workspace>
```

### Opción 3: Recrear el Agente en Foundry

Si las opciones anteriores no funcionan:

1. **Eliminar el agente actual** (agent975 o el que estés usando)
2. **Crear nuevo agente** con la configuración actualizada
3. **Importar el OpenAPI fresco** desde:
   ```
   https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi
   ```

## 🧪 Validación Post-Actualización

### Test 1: Verificar que `probarEndpoint` NO existe

```bash
# Desde PowerShell
curl https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi | ConvertFrom-Json | Select-String "probar"

# Resultado esperado: Solo debe aparecer en la descripción como "deprecado"
```

### Test 2: Invocar `/api/diagnostico-recursos` desde Foundry

En el chat del agente:
```
Ejecuta un diagnóstico de recursos Azure
```

**Resultado esperado**:
- ✅ El agente invoca `/api/diagnostico-recursos` correctamente
- ❌ NO intenta invocar `probarEndpoint`

### Test 3: Usar el Router Semántico

En el chat del agente:
```
Valida si diagnostico_recursos está en correcto funcionamiento
```

**Resultado esperado**:
```json
{
  "exito": true,
  "accion": "diagnostico",
  "endpoint_invocado": "/api/diagnostico-recursos",
  "resultado": { ... }
}
```

## 📋 Checklist de Verificación

- [ ] OpenAPI local NO contiene definición de `/api/probar-endpoint`
- [ ] OpenAPI local NO contiene definición de `/api/invocar`
- [ ] Foundry ha refrescado el catálogo de herramientas
- [ ] Test de invocación a `/api/diagnostico-recursos` exitoso
- [ ] NO aparecen errores `openapi_function_not_found`
- [ ] El agente usa `/api/copiloto` como router cuando es necesario

## 🔧 Troubleshooting

### Si sigue apareciendo el error:

1. **Verificar caché del navegador**
   - Ctrl + Shift + R para hard refresh en Foundry Portal

2. **Verificar versión del OpenAPI**
   ```bash
   curl https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi | jq '.info.version'
   # Debe ser "3.5" o superior
   ```

3. **Verificar logs de Foundry**
   - Azure Portal → AI Foundry → Logs
   - Buscar: `openapi_function_not_found`

4. **Último recurso: Limpiar caché de Foundry**
   ```bash
   # Eliminar todas las conexiones OpenAPI
   az ml connection delete --name copiloto-openapi --yes
   
   # Recrear desde cero
   az ml connection create --file fresh-connection.yaml
   ```

## 📊 Estado Actual del Sistema

| Componente | Estado | Acción Requerida |
|------------|--------|------------------|
| `openapi.yaml` local | ✅ Limpio | Ninguna |
| `function_app.py` | ✅ Sin proxies | Ninguna |
| Foundry Caché | ❌ Desactualizado | **Refrescar** |
| Tests locales | ✅ Pasando | Ninguna |

## 🎯 Próximos Pasos

1. ✅ Refrescar OpenAPI en Foundry (este documento)
2. ⏭️ Validar que `/api/diagnostico-recursos` funciona desde Foundry
3. ⏭️ Confirmar que el router `/api/copiloto` maneja correctamente las peticiones
4. ⏭️ Documentar el flujo final en `README.md`

---

**Última actualización**: Enero 2025  
**Versión OpenAPI**: 3.5  
**Estado**: Pendiente de refresh en Foundry
