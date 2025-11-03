# ✅ FIX: Campo Vectorial en Nuevo Índice

## 🐛 Problema

Al crear el nuevo servicio `boatrentalfoundrysearch-s1`, el índice se creó **sin el campo `vector`**:

```
Error: Cannot find nested property 'vector' on the resource type 'search.documentFields'
```

**Causa**: El script inicial (`index_schema.json`) solo incluía campos de texto, sin el campo vectorial necesario para embeddings.

## ✅ Solución Aplicada

### 1. Índice Recreado con Campo Vectorial

**Archivo**: `index_schema_con_vector.json`

**Campo agregado**:

```json
{
  "name": "vector",
  "type": "Collection(Edm.Single)",
  "searchable": true,
  "dimensions": 3072,
  "vectorSearchProfile": "vector-profile"
}
```

**Configuración vectorial**:

```json
{
  "vectorSearch": {
    "algorithms": [{
      "name": "hnsw-algorithm",
      "kind": "hnsw",
      "hnswParameters": {
        "metric": "cosine",
        "m": 4,
        "efConstruction": 400,
        "efSearch": 500
      }
    }],
    "profiles": [{
      "name": "vector-profile",
      "algorithm": "hnsw-algorithm"
    }]
  }
}
```

### 2. Comandos Ejecutados

```bash
# 1. Eliminar índice antiguo (sin vectores)
curl -X DELETE "https://boatrentalfoundrysearch-s1.search.windows.net/indexes/agent-memory-index?api-version=2023-11-01" \
  -H "api-key: [KEY]"

# 2. Crear índice nuevo (con vectores)
curl -X POST "https://boatrentalfoundrysearch-s1.search.windows.net/indexes?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: [KEY]" \
  -d @index_schema_con_vector.json
```

**Resultado**: ✅ Índice creado con campo vectorial de 3072 dimensiones

## 📊 Esquema Final del Índice

| Campo | Tipo | Dimensiones | Propósito |
|-------|------|-------------|-----------|
| id | String | - | Clave primaria |
| session_id | String | - | Filtro por sesión |
| agent_id | String | - | Filtro por agente |
| endpoint | String | - | Filtro por endpoint |
| texto_semantico | String | - | Búsqueda de texto |
| exito | Boolean | - | Filtro por éxito |
| tipo | String | - | Filtro por tipo |
| timestamp | DateTimeOffset | - | Ordenamiento temporal |
| **vector** | **Collection(Single)** | **3072** | **Búsqueda semántica** |

## 🔍 Verificación

### Test de Indexación

```bash
curl -X POST http://localhost:7071/api/indexar-memoria \
  -H "Content-Type: application/json" \
  -d '{
    "documentos": [{
      "id": "test-vector-1",
      "session_id": "test",
      "agent_id": "test-agent",
      "endpoint": "test",
      "texto_semantico": "Test con vectores",
      "exito": true,
      "tipo": "test",
      "timestamp": "2025-11-03T00:00:00Z"
    }]
  }'
```

**Resultado esperado**:

```json
{
  "exito": true,
  "documentos_indexados": 1,
  "mensaje": "Documentos indexados con embeddings"
}
```

**Sin errores de**:

```
❌ Cannot find nested property 'vector'
```

### Verificar Campo Vectorial

```bash
curl "https://boatrentalfoundrysearch-s1.search.windows.net/indexes/agent-memory-index?api-version=2023-11-01" \
  -H "api-key: [KEY]" | grep -A 5 "vector"
```

**Debe mostrar**:

```json
{
  "name": "vector",
  "type": "Collection(Edm.Single)",
  "dimensions": 3072,
  "vectorSearchProfile": "vector-profile"
}
```

## 🎯 Flujo Completo de Indexación

### 1. Backend Genera Embedding

```python
# En endpoints_search_memory.py
texto = doc["texto_semantico"]
vector = generar_embedding(texto)  # → [0.0243, -0.0178, ...] (3072 dims)
doc["vector"] = vector
```

### 2. Documento Completo

```json
{
  "id": "session_123_semantic_456",
  "texto_semantico": "Evento semantic en sesión 123",
  "vector": [0.0243, -0.0178, 0.0085, ...],  // ← 3072 dimensiones
  "timestamp": "2025-11-03T00:00:00Z"
}
```

### 3. Azure Search Acepta

```
✅ Documento indexado con búsqueda vectorial habilitada
```

## 📝 Configuración de Embeddings

**Modelo**: `text-embedding-3-large`
**Dimensiones**: 3072
**Endpoint**: Configurado en `AZURE_OPENAI_ENDPOINT`
**Deployment**: Configurado en `AZURE_OPENAI_DEPLOYMENT`

## 🚀 Beneficios

### Búsqueda Híbrida

Ahora el índice soporta:

- ✅ **Búsqueda de texto** (BM25)
- ✅ **Búsqueda vectorial** (HNSW cosine similarity)
- ✅ **Búsqueda híbrida** (combinación de ambas)

### Mejor Relevancia

```python
# Búsqueda semántica
resultado = search_service.search(
    query="problemas con memoria",
    top=10,
    use_vector_search=True  # ← Usa embeddings
)
# Encuentra documentos semánticamente similares aunque no tengan las palabras exactas
```

## 📊 Estado Final

- ✅ Índice recreado con campo vectorial
- ✅ 3072 dimensiones (text-embedding-3-large)
- ✅ Algoritmo HNSW configurado
- ✅ Búsqueda híbrida habilitada
- ✅ Backend puede indexar con vectores
- 🟡 Reiniciar Function App para aplicar

## 🔄 Próximo Paso

**Reiniciar Function App** para que use el nuevo índice:

```bash
# Detener (Ctrl+C)
# Reiniciar
func start --port 7071
```

---

**Fecha**: 2025-11-03
**Servicio**: boatrentalfoundrysearch-s1 (Standard)
**Índice**: agent-memory-index (con vectores)
**Estado**: ✅ Listo para indexación con embeddings
