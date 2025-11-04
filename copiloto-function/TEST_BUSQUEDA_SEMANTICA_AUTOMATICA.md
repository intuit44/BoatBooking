# ✅ TEST: Búsqueda Semántica Automática sin Body

## 🎯 Objetivo

Validar que el wrapper realiza búsqueda semántica automática basándose **solo en endpoint + session_id/agent_id**, sin depender del body JSON (que Foundry envía vacío).

## 🔧 Implementación

### Ubicación

**Archivo**: `memory_decorator.py`  
**Línea**: Después de consultar memoria global, antes de ejecutar función original

### Lógica Implementada

```python
# 1. Extraer session_id y agent_id de headers/params (NO del body)
session_id = req.headers.get("Session-ID") or req.params.get("session_id")
agent_id = req.headers.get("Agent-ID") or req.params.get("agent_id") or "GlobalAgent"

# 2. Detectar endpoint desde URL
endpoint_detectado = url.split('/')[-1]

# 3. Query semántica a Cosmos DB
query = """
SELECT TOP 10 c.texto_semantico, c.endpoint, c.timestamp, c.data.respuesta_resumen
FROM c
WHERE c.agent_id = @agent_id
  AND (c.endpoint = @endpoint OR CONTAINS(c.endpoint, @endpoint))
  AND IS_DEFINED(c.texto_semantico)
  AND LENGTH(c.texto_semantico) > 30
ORDER BY c._ts DESC
"""

# 4. Inyectar contexto en req.contexto_semantico
setattr(req, "contexto_semantico", contexto_semantico)
```

## 🧪 Tests de Validación

### Test 1: GET con Headers (Foundry simulation)

```bash
curl -X GET "http://localhost:7071/api/auditar-deploy" \
  -H "Session-ID: test-session-123" \
  -H "Agent-ID: agent-foundry-001"
```

**Resultado Esperado**:

```json
{
  "exito": true,
  "state": "Running",
  "metadata": {
    "busqueda_semantica": {
      "aplicada": true,
      "interacciones_encontradas": 5,
      "endpoint_buscado": "auditar-deploy",
      "resumen_contexto": "Ejecutó 'auditar-deploy' con éxito..."
    },
    "memoria_aplicada": true
  }
}
```

### Test 2: POST con Body Vacío (Foundry real)

```bash
curl -X POST "http://localhost:7071/api/diagnostico-recursos" \
  -H "Session-ID: foundry-session-456" \
  -H "Agent-ID: copilot-agent-002" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Resultado Esperado**:

```json
{
  "ok": true,
  "ambiente": "Azure",
  "metadata": {
    "busqueda_semantica": {
      "aplicada": true,
      "interacciones_encontradas": 3,
      "endpoint_buscado": "diagnostico-recursos",
      "resumen_contexto": "Diagnóstico completado..."
    },
    "memoria_aplicada": true,
    "memoria_global": true
  }
}
```

### Test 3: Sin Session ID (Nueva sesión)

```bash
curl -X GET "http://localhost:7071/api/auditar-deploy"
```

**Resultado Esperado**:

```json
{
  "exito": true,
  "metadata": {
    "busqueda_semantica": {
      "aplicada": false,
      "razon": "sin_session_id_o_sin_resultados"
    },
    "memoria_aplicada": false,
    "nueva_sesion": true
  }
}
```

## 📊 Logs Esperados

### Búsqueda Exitosa

```
[wrapper] 🔍 Búsqueda semántica: 5 interacciones similares en 'auditar-deploy' para agent-foundry-001
[wrapper] 🧠 Contexto semántico aplicado: 5 interacciones
[wrapper] 💾 Interacción registrada en memoria global para agente agent-foundry-001
```

### Sin Resultados

```
[wrapper] 🔍 Sin memoria semántica previa para 'nuevo-endpoint'
[wrapper] 💾 Interacción registrada en memoria global para agente GlobalAgent
```

### Sin Session ID

```
[wrapper] ⏭️ Sin session_id/agent_id válidos, búsqueda semántica omitida
```

## 🎯 Ventajas de la Implementación

1. ✅ **No depende del body JSON** - Funciona con Foundry que envía `{}`
2. ✅ **Búsqueda por endpoint** - Encuentra interacciones similares automáticamente
3. ✅ **Contexto enriquecido** - Inyecta resumen de interacciones previas
4. ✅ **Metadata transparente** - El agente ve qué memoria se aplicó
5. ✅ **Fallback seguro** - Si falla, continúa sin bloquear

## 🔄 Flujo Completo

```
1. Request llega → Wrapper intercepta
2. Extrae session_id/agent_id de headers/params
3. Detecta endpoint desde URL
4. Query semántica a Cosmos DB (TOP 10 interacciones similares)
5. Inyecta contexto en req.contexto_semantico
6. Ejecuta función original (con contexto disponible)
7. Enriquece respuesta con metadata de búsqueda
8. Registra nueva interacción en memoria
```

## 🚀 Próximos Pasos

1. Ejecutar tests de validación
2. Verificar logs en Application Insights
3. Confirmar que `memoria_aplicada: true` en respuestas
4. Validar con agente real de Foundry

---

**Estado**: ✅ Implementado  
**Archivos**: `memory_decorator.py`  
**Impacto**: Memoria semántica funciona sin depender del body JSON
