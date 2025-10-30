# 🔍 Integración de Queries Dinámicas - Documentación Completa

## 📋 Resumen

Se ha integrado exitosamente la lógica de **queries dinámicas** del `semantic_query_builder` en todos los endpoints que requieren consultar el historial de interacciones en Cosmos DB.

---

## ✅ Endpoints Integrados

### 1. `/api/copiloto` ✅ COMPLETADO

**Motivo**: Cuando actúe como proxy o dispatcher del agente.

**Integración**:

- Detecta parámetros avanzados (`tipo`, `contiene`, `endpoint`, `exito`, `fecha_inicio`, `fecha_fin`)
- Usa `interpretar_intencion_agente()` para analizar la consulta
- Construye query SQL dinámica con `construir_query_dinamica()`
- Ejecuta contra Cosmos DB con `ejecutar_query_cosmos()`
- Retorna resultados filtrados y formateados

**Ubicación**: `function_app.py` líneas ~4620-4690

---

### 2. `/api/sugerencias` ✅ COMPLETADO

**Motivo**: Para generar sugerencias basadas en interacciones previas.

**Integración**:

- Reutiliza `semantic_query_builder` para consultas inteligentes
- Filtra por patrones de interacciones exitosas
- Genera sugerencias contextuales basadas en historial

**Ubicación**: `endpoints/sugerencias.py`

---

### 3. `/api/contexto-inteligente` ✅ COMPLETADO

**Motivo**: Para devolver contexto interpretado filtrado.

**Integración**:

- Usa queries dinámicas para obtener contexto relevante
- Filtra por sesión, agente y tipo de interacción
- Genera resumen semántico del contexto

**Ubicación**: `endpoints/contexto_inteligente.py`

---

### 4. `/api/memoria-global` ✅ COMPLETADO

**Motivo**: Si aplicas deduplicación o resumen sobre interacciones múltiples sesiones.

**Integración**:

- Consulta interacciones de múltiples sesiones
- Aplica deduplicación semántica
- Genera resumen global con estadísticas

**Ubicación**: `endpoints/memoria_global.py`

---

### 5. `/api/diagnostico` ✅ COMPLETADO

**Motivo**: Para analizar qué ocurrió en determinada sesión.

**Integración**:

- Analiza interacciones por sesión
- Detecta patrones de errores
- Genera diagnóstico con métricas

**Ubicación**: `endpoints/diagnostico.py`

---

### 6. `/api/buscar-interacciones` ✅ YA EXISTÍA

**Motivo**: Endpoint original que implementa queries dinámicas.

**Integración**: Ya implementado completamente.

**Ubicación**: `buscar_interacciones_endpoint.py`

---

### 7. `/api/msearch` ✅ YA EXISTÍA

**Motivo**: Búsqueda semántica avanzada en memoria.

**Integración**: Ya implementado completamente.

**Ubicación**: `endpoints/msearch.py`

---

## 🔧 Módulo Centralizado: `semantic_query_builder.py`

### Funciones Principales

#### 1. `interpretar_intencion_agente(mensaje, headers)`

Interpreta la intención del agente y extrae parámetros de consulta.

**Entrada**:

```python
mensaje = "muéstrame errores de los últimos 3 días"
headers = {"Session-ID": "abc123"}
```

**Salida**:

```python
{
    "session_id": "abc123",
    "tipo": "error",
    "fecha_inicio": "2025-01-05T00:00:00",
    "exito": False,
    "limite": 10
}
```

---

#### 2. `construir_query_dinamica(**params)`

Construye una query SQL dinámica para Cosmos DB.

**Parámetros**:

- `session_id`: Filtrar por sesión
- `tipo`: Tipo de interacción (error, consulta, comando)
- `contiene`: Texto a buscar en texto_semantico
- `endpoint`: Filtrar por endpoint específico
- `exito`: Filtrar por éxito (True/False)
- `fecha_inicio`: Fecha de inicio
- `fecha_fin`: Fecha de fin
- `orden`: Orden de resultados (desc/asc)
- `limite`: Límite de resultados

**Ejemplo**:

```python
query = construir_query_dinamica(
    session_id="abc123",
    tipo="error",
    fecha_inicio="2025-01-05",
    limite=20
)
```

**Salida**:

```sql
SELECT * FROM c 
WHERE c.session_id = 'abc123' 
AND c.tipo = 'error' 
AND c.timestamp >= '2025-01-05T00:00:00' 
ORDER BY c.timestamp DESC 
OFFSET 0 LIMIT 20
```

---

#### 3. `ejecutar_query_cosmos(query_sql, container)`

Ejecuta la query contra Cosmos DB y retorna resultados.

**Ejemplo**:

```python
from services.memory_service import memory_service

container = memory_service.memory_container
resultados = ejecutar_query_cosmos(query_sql, container)
```

---

## 📊 Flujo de Integración

```
┌─────────────────────────────────────────────────────────────┐
│  1. Agente envía request con parámetros avanzados           │
│     GET /api/copiloto?tipo=error&fecha_inicio=2025-01-05    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Endpoint detecta parámetros avanzados                   │
│     usar_query_dinamica = True                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. interpretar_intencion_agente()                          │
│     Analiza mensaje y headers                               │
│     Extrae parámetros estructurados                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. construir_query_dinamica()                              │
│     Genera SQL dinámico con filtros                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. ejecutar_query_cosmos()                                 │
│     Ejecuta contra Cosmos DB                                │
│     Retorna resultados filtrados                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Formatear y retornar respuesta                          │
│     JSON con interacciones filtradas                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Beneficios de la Integración

### ✅ Reducción de Errores

- **Antes**: Lógica duplicada en cada endpoint
- **Ahora**: Lógica centralizada en `semantic_query_builder.py`

### ✅ Facilita Mantenimiento

- **Antes**: Actualizar 7 archivos diferentes
- **Ahora**: Actualizar solo `semantic_query_builder.py`

### ✅ Mejora Rendimiento

- **Antes**: Queries no optimizadas
- **Ahora**: Queries optimizadas con índices y filtros

### ✅ Escalabilidad Inmediata

- **Antes**: Agregar filtros requería modificar múltiples endpoints
- **Ahora**: Agregar filtros solo en `construir_query_dinamica()`

### ✅ Seguridad y Consistencia

- **Antes**: Accesos directos a Cosmos DB sin validación
- **Ahora**: Capa bien definida con validación y sanitización

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Buscar errores recientes

```bash
curl -X GET "http://localhost:7071/api/copiloto?tipo=error&limite=5" \
  -H "Session-ID: abc123"
```

### Ejemplo 2: Buscar interacciones con texto específico

```bash
curl -X POST "http://localhost:7071/api/copiloto" \
  -H "Content-Type: application/json" \
  -H "Session-ID: abc123" \
  -d '{
    "contiene": "cosmos db",
    "fecha_inicio": "2025-01-05",
    "limite": 10
  }'
```

### Ejemplo 3: Buscar por endpoint específico

```bash
curl -X GET "http://localhost:7071/api/copiloto?endpoint=/api/ejecutar-cli&exito=false" \
  -H "Session-ID: abc123"
```

---

## 🔍 Detección Automática de Queries Dinámicas

Los endpoints detectan automáticamente cuando usar queries dinámicas basándose en:

1. **Parámetros explícitos**: `tipo`, `contiene`, `endpoint`, `exito`, `fecha_inicio`, `fecha_fin`
2. **Palabras clave en mensaje**: "historial", "buscar", "filtrar", "errores"
3. **Headers especiales**: `X-Query-Type: dynamic`

---

## 🧪 Testing

### Test Manual

```bash
# 1. Probar query dinámica básica
curl -X GET "http://localhost:7071/api/copiloto?tipo=error" \
  -H "Session-ID: test_session"

# 2. Probar con múltiples filtros
curl -X GET "http://localhost:7071/api/copiloto?tipo=error&fecha_inicio=2025-01-05&limite=20" \
  -H "Session-ID: test_session"

# 3. Probar búsqueda por contenido
curl -X POST "http://localhost:7071/api/copiloto" \
  -H "Content-Type: application/json" \
  -H "Session-ID: test_session" \
  -d '{"contiene": "cosmos", "limite": 10}'
```

### Test Automatizado

```python
# tests/test_queries_dinamicas.py
import pytest
from semantic_query_builder import construir_query_dinamica, interpretar_intencion_agente

def test_interpretar_intencion():
    resultado = interpretar_intencion_agente(
        "muéstrame errores de ayer",
        {"Session-ID": "test"}
    )
    assert resultado["tipo"] == "error"
    assert resultado["session_id"] == "test"

def test_construir_query():
    query = construir_query_dinamica(
        session_id="test",
        tipo="error",
        limite=10
    )
    assert "WHERE c.session_id = 'test'" in query
    assert "c.tipo = 'error'" in query
    assert "LIMIT 10" in query
```

---

## 📚 Documentación Adicional

- **Módulo principal**: `semantic_query_builder.py`
- **Endpoints integrados**: Ver sección "Endpoints Integrados"
- **Ejemplos de uso**: Ver carpeta `examples/`
- **Tests**: Ver carpeta `tests/`

---

## 🚀 Próximos Pasos

1. ✅ Integración completada en todos los endpoints
2. ⏳ Agregar más filtros avanzados (por agente, por duración, etc.)
3. ⏳ Implementar caché de queries frecuentes
4. ⏳ Agregar métricas de rendimiento
5. ⏳ Documentar patrones de uso comunes

---

## 📞 Soporte

Para preguntas o problemas:

- Revisar logs en `function_app.py`
- Verificar configuración de Cosmos DB
- Consultar ejemplos en `examples/`

---

**Última actualización**: 2025-01-08
**Versión**: 1.0.0
**Estado**: ✅ COMPLETADO
