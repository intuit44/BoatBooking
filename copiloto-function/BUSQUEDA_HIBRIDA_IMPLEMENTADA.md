# 🎯 Búsqueda Híbrida Implementada: Intención → event_type + Vector Search

**Fecha**: 2025-01-09  
**Solución**: Búsqueda híbrida que combina AI Search (vectorial) + Cosmos (estructurado)

---

## 🔄 Flujo Implementado

```
Usuario: "análisis semántico"
  ↓
1️⃣ interpretar_intencion_agente()
   → Detecta: "análisis" en texto
   → Deriva: tipo = "respuesta_semantica"
  ↓
2️⃣ AI Search (vectorial)
   → Query: "análisis semántico"
   → Embedding vectorial
   → Resultados: 20 docs similares
  ↓
3️⃣ Cosmos (estructurado)
   → WHERE (c.tipo = 'respuesta_semantica' OR c.event_type = 'respuesta_semantica')
   → Resultados: 15 docs filtrados
  ↓
4️⃣ Intersección
   → docs_vectoriales ∩ docs_estructurados
   → Resultado final: 10 docs (relevantes + correctos)
```

---

## ✅ Cambios Implementados

### 1. `function_app.py` - Búsqueda Híbrida

```python
# 🧠 INTERPRETAR INTENCIÓN PRIMERO
query_texto = body.get("tipo") or body.get("query") or ""
intencion_params = interpretar_intencion_agente(query_texto, dict(req.headers))

# 1️⃣ AI Search: Búsqueda vectorial semántica
docs_search = buscar_memoria_endpoint({
    "query": query_universal,
    "session_id": session_id,
    "top": 20
})

# 2️⃣ Cosmos: Filtro estructurado por event_type
if params_completos.get("tipo"):
    query_sql = construir_query_dinamica(**params_completos)
    resultados_cosmos = ejecutar_query_cosmos(query_sql, memory_service.memory_container)
    
    # 3️⃣ INTERSECCIÓN
    ids_cosmos = {d.get("id") for d in resultados_cosmos}
    docs_search = [d for d in docs_search if d.get("id") in ids_cosmos]
```

### 2. `semantic_query_builder.py` - Derivación de event_type

```python
# 🔥 DERIVAR event_type DESDE INTENCIÓN SEMÁNTICA
if any(x in msg_lower for x in ["análisis", "resumen", "contextual", "semántico"]):
    params["tipo"] = "respuesta_semantica"
elif any(x in msg_lower for x in ["diagnóstico", "diagnostico", "recursos"]):
    params["tipo"] = "diagnostico"
elif any(x in msg_lower for x in ["error", "fallo"]):
    params["tipo"] = "error"
```

### 3. Query Cosmos - Búsqueda en ambos campos

```python
# Filtro por tipo/event_type (buscar en ambos campos)
if tipo:
    condiciones.append(f"(c.tipo = '{tipo}' OR c.event_type = '{tipo}')")
```

---

## 📊 Casos de Uso

### Caso 1: "análisis semántico"

**Input**:
```json
{"tipo": "análisis semántico", "session_id": "assistant"}
```

**Procesamiento**:
```
interpretar_intencion_agente("análisis semántico")
  → tipo = "respuesta_semantica"

AI Search:
  → query vectorial: "análisis semántico"
  → 20 docs similares

Cosmos:
  → WHERE (c.tipo = 'respuesta_semantica' OR c.event_type = 'respuesta_semantica')
  → 15 docs estructurados

Intersección:
  → 10 docs finales (vectorial ∩ estructurado)
```

**Output**:
```json
{
  "exito": true,
  "interacciones": [
    {
      "texto_semantico": "ANÁLISIS CONTEXTUAL COMPLETO...",
      "tipo": "respuesta_semantica",
      "event_type": "respuesta_semantica"
    }
  ],
  "total": 10,
  "busqueda_hibrida_aplicada": true
}
```

### Caso 2: "diagnóstico de recursos"

**Input**:
```json
{"tipo": "diagnóstico", "session_id": "assistant"}
```

**Procesamiento**:
```
interpretar_intencion_agente("diagnóstico")
  → tipo = "diagnostico"

AI Search:
  → query vectorial: "diagnóstico"
  → 18 docs similares

Cosmos:
  → WHERE (c.tipo = 'diagnostico' OR c.event_type = 'diagnostico')
  → 12 docs estructurados

Intersección:
  → 8 docs finales
```

---

## 🎯 Ventajas de la Búsqueda Híbrida

| Aspecto | Solo Vectorial | Solo Estructurado | Híbrido ✅ |
|---------|---------------|-------------------|-----------|
| **Precisión semántica** | ✅ Alta | ❌ Baja | ✅ Alta |
| **Filtrado por tipo** | ❌ No | ✅ Sí | ✅ Sí |
| **Relevancia** | ✅ Alta | ⚠️ Media | ✅ Muy Alta |
| **Falsos positivos** | ⚠️ Algunos | ❌ Muchos | ✅ Pocos |

---

## 🧪 Validación

### Test 1: Análisis Semántico
```bash
curl -X POST http://localhost:7071/api/historial-interacciones \
  -H "Session-ID: assistant" \
  -H "Content-Type: application/json" \
  -d '{"tipo": "análisis semántico", "limit": 5}'
```

**Logs Esperados**:
```
🧠 HISTORIAL: Parámetros interpretados: {'tipo': 'respuesta_semantica', ...}
✅ AI Search: 20 docs vectoriales
✅ Cosmos: 15 docs estructurados (event_type filtrado)
🎯 Intersección: 10 docs (vectorial ∩ estructurado)
```

### Test 2: Diagnóstico
```bash
curl -X POST http://localhost:7071/api/historial-interacciones \
  -H "Session-ID: assistant" \
  -H "Content-Type: application/json" \
  -d '{"tipo": "diagnóstico", "limit": 3}'
```

**Logs Esperados**:
```
🧠 HISTORIAL: Parámetros interpretados: {'tipo': 'diagnostico', ...}
✅ AI Search: 18 docs vectoriales
✅ Cosmos: 12 docs estructurados (event_type filtrado)
🎯 Intersección: 8 docs (vectorial ∩ estructurado)
```

---

## 📝 Mapeo de Intenciones

| Intención del Usuario | event_type Derivado | Documentos Encontrados |
|----------------------|---------------------|------------------------|
| "análisis semántico" | `respuesta_semantica` | Análisis contextuales |
| "resumen" | `respuesta_semantica` | Resúmenes generados |
| "diagnóstico" | `diagnostico` | Diagnósticos de recursos |
| "error" | `error` | Eventos de error |
| "fallo" | `error` | Fallos del sistema |

---

## 🔍 Logs de Monitoreo

```bash
# Verificar interpretación de intención
grep "🧠 HISTORIAL: Parámetros interpretados" logs/*.log

# Verificar búsqueda híbrida
grep "🎯 Intersección" logs/*.log

# Verificar query con event_type
grep "🔍 Query generada con event_type" logs/*.log
```

---

## ✅ Beneficios

✅ **Intención real**: No depende de valores predefinidos  
✅ **Búsqueda semántica**: Usa embeddings vectoriales  
✅ **Filtrado estructurado**: Usa event_type para precisión  
✅ **Intersección inteligente**: Combina lo mejor de ambos mundos  
✅ **Extensible**: Fácil agregar más intenciones  
✅ **Trazable**: Logs claros en cada paso

---

**Estado**: ✅ Implementado y listo para validación  
**Archivos modificados**: 
- `function_app.py` (búsqueda híbrida)
- `semantic_query_builder.py` (derivación de event_type)

**Impacto**: 🟢 Solución basada en intención real, no en valores predefinidos
