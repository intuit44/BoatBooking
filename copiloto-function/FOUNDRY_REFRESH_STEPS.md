# 🔄 Pasos para Actualizar OpenAPI en Azure AI Foundry

## 🎯 Problema
```
Error: openapi_function_not_found
No function call found for: CopilotoFunctionApp_probarEndpoint
```

**Causa**: Foundry tiene cacheada una versión antigua del OpenAPI que incluía endpoints eliminados.

## ✅ Solución en 3 Pasos

### 1️⃣ Verificar que el OpenAPI local está limpio

```powershell
# Verificar que NO existen referencias a probar-endpoint
cd c:\ProyectosSimbolicos\boat-rental-app\copiloto-function
findstr /i "probar-endpoint" openapi.yaml
findstr /i "invocar" openapi.yaml

# Resultado esperado: Solo menciones en la descripción como "deprecado"
```

### 2️⃣ Actualizar la conexión en Azure AI Foundry

**Opción A: Desde el Portal Web**

1. Ir a https://ai.azure.com
2. Navegar a tu proyecto → **Settings** → **Connections**
3. Buscar la conexión que apunta a tu Function App
4. Click en **Edit** o **Delete + Recreate**
5. Si editas: Click en **Refresh Schema** o **Re-import OpenAPI**
6. Si recreas: Usar la URL:
   ```
   https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi
   ```

**Opción B: Recrear el Agente**

Si la opción A no funciona:

1. **Eliminar el agente actual** (agent975 o el que uses)
2. **Crear nuevo agente** con configuración fresca
3. **Importar OpenAPI** desde:
   ```
   https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi
   ```

### 3️⃣ Validar que funcionó

**Test 1: Verificar endpoints disponibles**

En Foundry, el agente debe ver SOLO estos endpoints:
- ✅ `/api/copiloto` (router semántico)
- ✅ `/api/diagnostico-recursos`
- ✅ `/api/crear-contenedor`
- ✅ `/api/ejecutar-cli`
- ✅ `/api/bridge-cli`
- ✅ `/api/agent-output`
- ❌ `/api/probar-endpoint` (NO debe aparecer)
- ❌ `/api/invocar` (NO debe aparecer)

**Test 2: Invocar diagnostico-recursos**

En el chat del agente:
```
Ejecuta un diagnóstico de recursos Azure
```

**Resultado esperado**:
```json
{
  "exito": true,
  "timestamp": "2025-01-XX...",
  "recursos": {...},
  "metricas": {...}
}
```

## 🔧 Si el problema persiste

### Limpiar caché del navegador
```
Ctrl + Shift + R (hard refresh en el portal de Foundry)
```

### Verificar versión del OpenAPI
```powershell
curl https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi | ConvertFrom-Json | Select-Object -ExpandProperty info
```

Debe mostrar:
```json
{
  "title": "Copiloto Function Gateway",
  "version": "3.5",
  "description": "...los endpoints legacy /api/probar-endpoint e /api/invocar fueron retirados..."
}
```

## 📊 Checklist Final

- [ ] OpenAPI local NO contiene `/api/probar-endpoint`
- [ ] OpenAPI local NO contiene `/api/invocar`
- [ ] Foundry ha refrescado el catálogo de herramientas
- [ ] Test de `/api/diagnostico-recursos` exitoso
- [ ] NO aparecen errores `openapi_function_not_found`
- [ ] El agente puede invocar endpoints correctamente

## 🎯 Nota Importante

**El OpenAPI NO es un endpoint HTTP**, es la **especificación de herramientas** que Foundry usa para saber qué funciones puede invocar. Cuando eliminas endpoints del código, debes actualizar el OpenAPI Y forzar que Foundry lo recargue.

---

**Última actualización**: Enero 2025  
**Estado**: Pendiente de refresh en Foundry
