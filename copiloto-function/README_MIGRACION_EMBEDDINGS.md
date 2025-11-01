# 🔄 Migración de Embeddings Reales

## Problema Identificado

Azure AI Search está funcional pero con embeddings sintéticos (0.1, 0.2) de prueba.
Esto impide búsquedas semánticas reales y el sintetizador no recibe contexto vectorial.

## Solución

Migración completa desde Cosmos DB → Embeddings reales → Azure AI Search

## 📋 Pasos de Ejecución

### 1. Configurar Variables de Entorno

```powershell
# OpenAI (requerido para embeddings)
$env:OPENAI_API_KEY = "sk-..."

# Cosmos DB
$env:COSMOS_ENDPOINT = "https://boatrentalfoundry.documents.azure.com:443/"
$env:COSMOS_KEY = "tu-cosmos-key"
$env:COSMOS_DATABASE_NAME = "agentMemory"
$env:COSMOS_CONTAINER_NAME = "memory"

# Azure Search
$env:AZURE_SEARCH_ENDPOINT = "https://boatrentalfoundrysearch.search.windows.net"
$env:AZURE_SEARCH_KEY = "kyfYT1Proxvt9fT4ZBmWPcppUkvjK0rxBuEB7prkxYAzSeCmpM7L"
$env:AZURE_SEARCH_INDEX_NAME = "agent-memory-index"
```

### 2. Ejecutar Migración

```powershell
cd copiloto-function
.\run_migration.ps1
```

O directamente:

```powershell
python migrate_embeddings.py
```

### 3. Verificar Resultados

```bash
# Verificar documentos indexados
curl -X GET "https://boatrentalfoundrysearch.search.windows.net/indexes/agent-memory-index/docs?\$count=true&api-version=2023-11-01" \
  -H "api-key: kyfYT1Proxvt9fT4ZBmWPcppUkvjK0rxBuEB7prkxYAzSeCmpM7L"

# Buscar semánticamente
curl -X POST "https://boatrentalfoundrysearch.search.windows.net/indexes/agent-memory-index/docs/search?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: kyfYT1Proxvt9fT4ZBmWPcppUkvjK0rxBuEB7prkxYAzSeCmpM7L" \
  -d '{
    "search": "*",
    "vectors": [{"value": [0.1, 0.2, ...], "fields": "vector", "k": 5}],
    "select": "id,texto_semantico,endpoint"
  }'
```

## 📊 Resultados Esperados

### Antes de la Migración

```json
{
  "exito": true,
  "total": 2,
  "documentos": [
    {
      "id": "test_foundry_20251030_214454",
      "vector": [0.1, 0.1, 0.1, ...],  // ❌ Sintético
      "texto_semantico": "Test de indexación..."
    }
  ]
}
```

### Después de la Migración

```json
{
  "exito": true,
  "total": 150,
  "documentos": [
    {
      "id": "real_interaction_20251030_120000",
      "vector": [0.0234, -0.0891, 0.1234, ...],  // ✅ Real
      "texto_semantico": "Usuario ejecutó az storage list con éxito",
      "@search.score": 0.89  // ✅ Score semántico real
    }
  ]
}
```

## 🎯 Impacto en el Sistema

### Antes

- ❌ Búsquedas devuelven 0 documentos relevantes
- ❌ Sintetizador solo usa Cosmos DB (sin contexto vectorial)
- ❌ Respuestas genéricas sin enriquecimiento semántico

### Después

- ✅ Búsquedas devuelven 3-5 documentos relevantes por similitud
- ✅ Sintetizador combina Cosmos + Azure Search vectorial
- ✅ Respuestas contextuales inteligentes

## 🔧 Mantenimiento Futuro

El indexador automático (`indexador_semantico.py`) ya está actualizado para:

- ✅ Generar embeddings reales con `text-embedding-3-large`
- ✅ Soportar Azure OpenAI y OpenAI directo
- ✅ Indexar automáticamente cada nueva interacción

No se requiere migración manual nuevamente.

## 📈 Métricas de Validación

```python
# Test de búsqueda semántica
python test_search_endpoints.py

# Esperado:
# ✅ Azure Search: 4 docs relevantes encontrados
# ✅ Sintetizador generó resumen enriquecido
# ✅ Score promedio: 0.85+
```

## 🚨 Troubleshooting

### Error: "OPENAI_API_KEY not found"

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

### Error: "Cosmos connection failed"

Verifica que `COSMOS_ENDPOINT` y `COSMOS_KEY` sean correctos.

### Error: "Search indexing failed"

Verifica que el índice `agent-memory-index` exista y tenga el campo `vector` configurado.

## ✅ Checklist de Migración

- [ ] Variables de entorno configuradas
- [ ] Script `migrate_embeddings.py` ejecutado sin errores
- [ ] Verificación en Azure Portal: documentos indexados > 0
- [ ] Test de búsqueda semántica exitoso
- [ ] `/api/historial-interacciones` devuelve documentos relevantes
- [ ] Sintetizador genera respuestas enriquecidas
