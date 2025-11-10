# 🎯 Mapeo Intencional Implementado en `/api/historial-interacciones`

**Fecha**: 2025-01-09  
**Problema**: El agente enviaba `tipo: "análisis semántico"` pero ese campo no existe en Cosmos DB  
**Solución**: Mapeo intencional que traduce intenciones del usuario a tipos reales de documentos

---

## 🔍 Problema Identificado

### Request del Agente:
```json
{
  "Session-ID": "assistant",
  "Agent-ID": "assistant",
  "limit": 1,
  "tipo": "análisis semántico"
}
```

### Query Generada (ANTES):
```sql
SELECT * FROM c 
WHERE c.session_id = 'assistant' 
  AND c.tipo = 'análisis semántico'  -- ❌ Este valor NO EXISTE
```

### Resultado:
```json
{
  "exito": True,
  "interacciones": [],  // ❌ 0 resultados
  "total": 0
}
```

---

## ✅ Solución Implementada

### Mapeo Intencional Agregado:

```python
# 🔥 MAPEO INTENCIONAL: Traducir intenciones a tipos reales
mapeo_intencional = {
    "análisis semántico": "respuesta_semantica",
    "analisis semantico": "respuesta_semantica",
    "semantic analysis": "respuesta_semantica",
    "análisis contextual": "respuesta_semantica",
    "resumen": "respuesta_semantica",
    "diagnóstico": "diagnostico",
    "diagnostico": "diagnostico",
    "error": "error",
    "fallo": "error"
}

# Aplicar mapeo si existe
tipo_mapeado = mapeo_intencional.get(tipo_val.lower(), tipo_val)
```

### Query Generada (DESPUÉS):
```sql
SELECT * FROM c 
WHERE c.session_id = 'assistant' 
  AND c.tipo = 'respuesta_semantica'  -- ✅ Valor real que SÍ EXISTE
```

### Resultado Esperado:
```json
{
  "exito": True,
  "interacciones": [
    {
      "texto_semantico": "ANÁLISIS CONTEXTUAL COMPLETO...",
      "tipo": "respuesta_semantica",
      "timestamp": "2025-01-09T14:32:47Z"
    }
  ],
  "total": 5
}
```

---

## 📊 Casos de Uso Cubiertos

| Intención del Usuario | Tipo Mapeado | Documentos Encontrados |
|----------------------|--------------|------------------------|
| "análisis semántico" | `respuesta_semantica` | ✅ Análisis contextuales |
| "resumen" | `respuesta_semantica` | ✅ Resúmenes generados |
| "diagnóstico" | `diagnostico` | ✅ Diagnósticos de recursos |
| "error" | `error` | ✅ Eventos de error |
| "fallo" | `error` | ✅ Fallos del sistema |

---

## 🧪 Validación

### Test 1: Análisis Semántico
```bash
curl -X POST http://localhost:7071/api/historial-interacciones \
  -H "Session-ID: assistant" \
  -H "Agent-ID: assistant" \
  -H "Content-Type: application/json" \
  -d '{"tipo": "análisis semántico", "limit": 5}'
```

**Resultado Esperado**: 5+ interacciones con `tipo: "respuesta_semantica"`

### Test 2: Diagnóstico
```bash
curl -X POST http://localhost:7071/api/historial-interacciones \
  -H "Session-ID: assistant" \
  -H "Content-Type: application/json" \
  -d '{"tipo": "diagnóstico", "limit": 3}'
```

**Resultado Esperado**: 3+ interacciones con `tipo: "diagnostico"`

### Test 3: Errores
```bash
curl -X POST http://localhost:7071/api/historial-interacciones \
  -H "Session-ID: assistant" \
  -H "Content-Type: application/json" \
  -d '{"tipo": "error", "limit": 10}'
```

**Resultado Esperado**: Interacciones con `tipo: "error"` o `categoria: "error"`

---

## 🔄 Flujo Completo

### Antes (Sin Mapeo):
```
Usuario: "análisis semántico"
  ↓
Query: tipo = "análisis semántico"
  ↓
Cosmos DB: 0 resultados (no existe ese tipo)
  ↓
Agente: "No se encontraron interacciones"
```

### Después (Con Mapeo):
```
Usuario: "análisis semántico"
  ↓
Mapeo Intencional: "análisis semántico" → "respuesta_semantica"
  ↓
Query: tipo = "respuesta_semantica"
  ↓
Cosmos DB: 5 resultados encontrados
  ↓
Agente: "Encontré 5 análisis semánticos previos..."
```

---

## 📝 Logs de Validación

```bash
# Buscar logs de mapeo intencional
grep "🎯 Mapeo intencional" logs/*.log

# Ejemplo de salida esperada:
# 🎯 Mapeo intencional: 'análisis semántico' → 'respuesta_semantica'
# 🎯 Mapeo intencional: 'diagnóstico' → 'diagnostico'
```

---

## 🚀 Próximos Pasos

1. **Reiniciar el servidor** para aplicar cambios
2. **Probar desde Foundry** con la misma pregunta
3. **Validar logs** para confirmar el mapeo
4. **Expandir mapeo** si se detectan más intenciones comunes

---

## 🎯 Beneficios

✅ **Intenciones naturales**: El usuario puede usar lenguaje natural  
✅ **Sin cambios en Cosmos**: No requiere modificar documentos existentes  
✅ **Extensible**: Fácil agregar más mapeos según necesidad  
✅ **Retrocompatible**: Si no hay mapeo, usa el valor original  
✅ **Trazabilidad**: Logs claros de cada mapeo aplicado

---

**Estado**: ✅ Implementado y listo para validación  
**Ubicación**: `function_app.py` línea ~4490  
**Impacto**: 🟢 Bajo riesgo, alta efectividad
