# 🔐 Migración a Managed Identity para Azure AI Search

## ✅ Cambios Realizados

### 1. Script de Configuración

**Archivo**: `setup_managed_identity_search.ps1`

Configura automáticamente:

- ✅ Obtiene Managed Identity de Function App
- ✅ Asigna rol `Search Index Data Contributor`
- ✅ Asigna rol `Search Service Contributor`
- ✅ Remueve `AZURE_SEARCH_KEY` de variables de entorno
- ✅ Actualiza `local.settings.json`

### 2. Cliente Azure Search

**Archivo**: `services/azure_search_client.py`

```python
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

# Detecta automáticamente:
# - Managed Identity en Azure
# - API Key en desarrollo local
```

### 3. Dependencias

**Archivo**: `requirements.txt`

```txt
azure-search-documents>=11.4.0
```

## 🚀 Pasos de Implementación

### Paso 1: Ejecutar Script de Configuración

```powershell
cd copiloto-function
.\setup_managed_identity_search.ps1
```

**Qué hace:**

1. Configura permisos de Managed Identity
2. Remueve claves de variables de entorno
3. Actualiza configuración local

### Paso 2: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 3: Usar el Cliente

```python
from services.azure_search_client import AzureSearchService

# Inicializar (detecta automáticamente el método de autenticación)
search = AzureSearchService()

# Buscar
resultado = search.search("query text", top=10)

# Subir documentos
docs = [{"id": "1", "texto_semantico": "contenido"}]
search.upload_documents(docs)
```

## 🔒 Seguridad Mejorada

### Antes (con API Key)

```python
# ❌ Clave expuesta en logs
api_key = "kyfYT1Pr..."
headers = {"api-key": api_key}
```

### Después (con Managed Identity)

```python
# ✅ Sin claves, token automático
credential = DefaultAzureCredential()
client = SearchClient(endpoint, index, credential)
```

## 🎯 Beneficios

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Claves** | Expuestas en logs | No existen |
| **Rotación** | Manual | Automática |
| **Seguridad** | Media | Alta |
| **Complejidad** | Alta | Baja |
| **Logs** | Claves truncadas | Sin claves |

## 🧪 Validación

### Desarrollo Local

```bash
# Usa AZURE_SEARCH_KEY de local.settings.json
func start
```

### Azure (Producción)

```bash
# Usa Managed Identity automáticamente
# No requiere AZURE_SEARCH_KEY
```

## 📊 Variables de Entorno

### Requeridas

```json
{
  "AZURE_SEARCH_ENDPOINT": "https://boatrentalfoundrysearch.search.windows.net"
}
```

### Opcionales (solo desarrollo local)

```json
{
  "AZURE_SEARCH_KEY": "tu-clave-local"
}
```

## 🔄 Rollback (si es necesario)

Si necesitas volver a API Key:

```powershell
# Obtener clave
$key = az search admin-key show --name boatrentalfoundrysearch --resource-group boat-rental-app-group --query primaryKey -o tsv

# Configurar en Function App
az functionapp config appsettings set `
  --name copiloto-semantico-func-us2 `
  --resource-group boat-rental-app-group `
  --settings AZURE_SEARCH_KEY=$key
```

## ✅ Checklist de Migración

- [ ] Ejecutar `setup_managed_identity_search.ps1`
- [ ] Instalar `azure-search-documents>=11.4.0`
- [ ] Actualizar código para usar `AzureSearchService`
- [ ] Probar en desarrollo local
- [ ] Desplegar a Azure
- [ ] Validar funcionamiento en producción
- [ ] Remover referencias a `AZURE_SEARCH_KEY` del código

## 🎉 Resultado Final

**Sin claves expuestas, sin logs truncados, autenticación automática y segura.**
