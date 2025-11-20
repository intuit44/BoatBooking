# 🔧 FIX: Memoria Inconsistente en Cosmos DB

## 🐛 Problema

Consultar la misma `session_id` devuelve resultados diferentes:

- Primera consulta: 50 interacciones
- Segunda consulta: 1 interacción

## 🔍 Causa Raíz

En `cosmos_memory_direct.py` línea 270, la función `_recuperar_interacciones_prioritarias` usa estrategias progresivas que prueban múltiples filtros y retorna el primero que tenga resultados.

Esto causa inconsistencia porque:

1. Primera vez: puede usar estrategia "session+agent" → 50 resultados
2. Segunda vez: puede usar estrategia "solo_session" → 1 resultado
3. Tercera vez: puede usar estrategia "fallback_global" → resultados aleatorios

## ✅ Solución

Cuando `session_override` está presente, usar query directa sin fallbacks:

```python
# En consultar_memoria_cosmos_directo(), línea 270:

# ✅ FIX: Query directa si hay session_override
if session_override:
    query = """
    SELECT TOP 150 c.id, c.agent_id, c.session_id, c.endpoint, c.timestamp,
                   c.event_type, c.texto_semantico, c.contexto_conversacion,
                   c.metadata, c.resumen_conversacion, c.data.respuesta_resumen,
                   c.data.interpretacion_semantica, c.data.contexto_inteligente,
                   c.data.response_data.respuesta_usuario, c._ts
    FROM c
    WHERE c.session_id = @session_id
      AND IS_DEFINED(c.texto_semantico) 
      AND LENGTH(c.texto_semantico) > 30
    ORDER BY c._ts DESC
    """
    raw_items = list(container.query_items(
        query=query,
        parameters=[{"name": "@session_id", "value": session_override}],
        enable_cross_partition_query=True
    ))
    session_id = session_override
    agent_id = agent_filter or "GlobalAgent"
else:
    # Sin session_override, usar estrategia progresiva
    raw_items = _recuperar_interacciones_prioritarias(
        container, session_id_hint, agent_filter)
    agent_id = agent_filter
    session_id = session_id_hint or (raw_items[0].get(
        "session_id") if raw_items else None)
    if not session_id:
        session_id = "fallback_session"
```

## 🎯 Resultado Esperado

```bash
# Primera consulta
curl -X POST "http://localhost:7071/api/precalentar-memoria" \
  -H "Session-ID: session_1759821004" \
  -d '{}'
# → {"interacciones_cacheadas": 50}

# Segunda consulta (misma sesión)
curl -X POST "http://localhost:7071/api/precalentar-memoria" \
  -H "Session-ID: session_1759821004" \
  -d '{}'
# → {"interacciones_cacheadas": 50}  ✅ CONSISTENTE
```

## 📝 Archivo a Modificar

`cosmos_memory_direct.py` - función `consultar_memoria_cosmos_directo` - líneas 270-279
