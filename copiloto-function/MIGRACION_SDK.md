# 🔄 Migración de CLI a SDK - Endpoint /api/crear-contenedor

## ❌ Problema Identificado

El endpoint `/api/crear-contenedor` usa `subprocess.run(["az", ...])` que falla con:

```
FileNotFoundError: [WinError 2] El sistema no puede encontrar el archivo especificado
```

**Causa**: Azure CLI (`az`) no está disponible en el PATH de Azure Functions.

## ✅ Solución Implementada

Se creó una versión usando **Azure SDK** en:

```
copiloto-function/endpoints/crear_contenedor_sdk.py
```

### Ventajas del SDK

- ✅ No depende de binarios externos
- ✅ Managed Identity nativa
- ✅ Más rápido (sin subprocess)
- ✅ Mejor manejo de errores
- ✅ Funciona en cualquier entorno

## 📋 Pasos para Aplicar la Migración

### 1. Instalar dependencias (si no están)

```bash
pip install azure-mgmt-storage azure-identity
```

### 2. Reemplazar en function_app.py

**Buscar** (línea ~12260):

```python
@app.function_name(name="crear_contenedor_http")
@app.route(route="crear-contenedor", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_contenedor_http(req: func.HttpRequest) -> func.HttpResponse:
    # ... código que usa subprocess.run(["az", ...])
```

**Reemplazar con**:

```python
@app.function_name(name="crear_contenedor_http")
@app.route(route="crear-contenedor", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_contenedor_http(req: func.HttpRequest) -> func.HttpResponse:
    from endpoints.crear_contenedor_sdk import crear_contenedor_sdk
    return crear_contenedor_sdk(req)
```

### 3. Configurar permisos de Managed Identity

La función necesita permisos para crear Storage Accounts:

```bash
# Obtener el Principal ID de la función
az functionapp identity show \
  --name copiloto-semantico-func-us2 \
  --resource-group boat-rental-app-group \
  --query principalId -o tsv

# Asignar rol (usar el Principal ID obtenido)
az role assignment create \
  --assignee 16111244-a538-4a2f-9754-4be1d0a71dc8 \
  --role "Storage Account Contributor" \
  --scope "/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group"
```

## 🧪 Probar el Endpoint

```bash
curl -X POST https://copiloto-func.ngrok.app/api/crear-contenedor \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "test-storage-validacion",
    "location": "eastus",
    "sku": "Standard_LRS",
    "kind": "StorageV2",
    "resource_group": "boat-rental-app-group"
  }'
```

## 📊 Comparación CLI vs SDK

| Aspecto | CLI (subprocess) | SDK (nativo) |
|---------|------------------|--------------|
| Dependencias | Requiere `az` instalado | Solo paquetes Python |
| Velocidad | ~2-3s | ~1-2s |
| Errores | Texto plano | Excepciones tipadas |
| Autenticación | Requiere `az login` | Managed Identity automática |
| Portabilidad | Solo donde esté `az` | Cualquier entorno Python |
| Mantenimiento | Depende de CLI | API estable |

## 🔄 Otros Endpoints a Migrar

Estos endpoints también usan `subprocess.run()` y deberían migrarse:

1. `/api/ejecutar-cli` - **Ya migrado** (acepta cualquier comando)
2. `/api/configurar-cors` - Usar `WebSiteManagementClient`
3. `/api/configurar-app-settings` - Usar `WebSiteManagementClient`
4. `/api/escalar-plan` - Usar `WebSiteManagementClient`

## 📝 Notas Adicionales

- El SDK maneja automáticamente reintentos y throttling
- Los errores son más descriptivos y estructurados
- No hay problemas de PATH o permisos de ejecución
- Funciona igual en local y en Azure

---

**Fecha**: 2025-01-12
**Estado**: ✅ Solución lista para aplicar
