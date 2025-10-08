# 📋 SOLUCION_TEMPORAL.md - Sistema de Autorreparación CLI

## 🎯 IMPLEMENTADO: Memoria antes de error

### ✅ Cambios realizados

1. **Hook de autorreparación** en `/api/ejecutar-cli`:
   - Detecta errores `MissingParameter` automáticamente
   - Busca valores en memoria (CosmosDB) antes de fallar
   - Sugiere endpoints alternativos si no encuentra en memoria
   - Devuelve código 422 (procesable) en lugar de 400 (error final)

2. **Funciones auxiliares agregadas**:
   - `_analizar_error_cli()`: Detecta parámetros faltantes en stderr
   - `_reparar_comando_con_memoria()`: Agrega parámetros desde memoria
   - `_ejecutar_comando_reparado()`: Reintenta comando reparado

3. **Esquema OpenAPI extendido**:
   - Documenta respuesta 422 con `tipo_error`, `campo_faltante`, `endpoint_alternativo`
   - Permite al agente actuar automáticamente sobre errores estructurados

### 🔄 Flujo de autorreparación

```
Usuario: "ejecutá el despliegue del template"
↓
Agente: az deployment group create --template-file template.json
↓
Backend: ERROR - falta --resource-group
↓
Backend: Busca "resourceGroup" en memoria → encuentra "boat-rental-rg"
↓
Backend: Reintenta con --resource-group boat-rental-rg
↓
Backend: ✅ ÉXITO - comando reparado automáticamente
```

### 🤖 Para el agente (AI Foundry)

El agente ahora debe:

1. **Interpretar código 422** como "puedo autorreparar esto"
2. **Usar `endpoint_alternativo`** si no tiene memoria local
3. **Reintentar** con valores obtenidos
4. **No preguntar** cosas que puede resolver automáticamente

### 🔧 Endpoints auxiliares disponibles

- `/api/verificar-cosmos` → resourceGroup, subscriptionId
- `/api/status` → location, estado general  
- `/api/listar-blobs` → storageAccount
- `/api/verificar-app-insights` → appName

### ⚠️ TEMP WEB FIX aplicado

- Código marcado con comentarios `// TEMP WEB FIX`
- Cambios reversibles y documentados
- No afecta funcionalidad nativa existente
