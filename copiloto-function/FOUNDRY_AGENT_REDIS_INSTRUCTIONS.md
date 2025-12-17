# 🚀 Instrucciones Redis para Agentes Foundry

## 🎯 Reglas de Uso de Herramientas MCP

### 1. **Para Diagnóstico Básico: "¿Está funcionando Redis?"**

```
USAR: redis_health_check
CUÁNDO: Usuario pregunta si Redis responde, está conectado o disponible
RESULTADO: status "healthy", "no_data" o "error"
```

### 2. **Para Métricas Detalladas: "¿Cómo está el rendimiento?"**

```
USAR: redis_cache_monitor  
CUÁNDO: Usuario quiere estadísticas, hit ratio, memoria usada, efectividad
RESULTADO: hit_ratio, key_counts, memory_info, cache_effectiveness
```

### 3. **Para Buscar Contenido: "¿Qué hay en cache?"**

```
USAR: redis_buscar_memoria
CUÁNDO: Usuario quiere ver qué datos están guardados o buscar por término
PARÁMETROS: query (opcional), limit (default: 10)
RESULTADO: Lista de entradas de cache con contenido real
```

### 4. **Para Responder Preguntas: Cualquier consulta del usuario**

```
USAR: redis_cached_chat
CUÁNDO: Usuario hace preguntas que requieren respuesta de IA
PARÁMETROS: mensaje (requerido), session_id, agent_id
RESULTADO: Respuesta de IA + metadata de cache (hit/miss)
```

### 5. **Para Troubleshooting: Si redis_health_check falla**

```
USAR: verificar_health_cache
CUÁNDO: Como backup si redis_health_check no responde
RESULTADO: Mismo que redis_health_check pero diferente implementación
```

## 🚨 NO HAGAS ESTO

❌ **NO uses solo redis_health_check repetitivamente**
❌ **NO ignores las otras herramientas disponibles**
❌ **NO uses /api/ejecutar-cli con redis-cli en desarrollo local**

## ✅ FLUJO RECOMENDADO

### Cuando usuario pregunta sobre Redis

1. **Paso 1**: `redis_health_check` (status básico)
2. **Paso 2**: `redis_cache_monitor` (métricas detalladas)  
3. **Paso 3**: `redis_buscar_memoria` (contenido actual)
4. **Paso 4**: Resumen consolidado para el usuario

### Cuando usuario hace una pregunta normal

1. **Directo**: `redis_cached_chat` con la pregunta
2. **Mostrar**: Si fue cache hit o miss en la respuesta

## 📊 Ejemplos Prácticos

### Usuario: "¿Cómo está Redis?"

```python
# 1. Check básico
health = await redis_health_check()
# 2. Métricas detalladas  
metrics = await redis_cache_monitor()
# 3. Contenido actual
content = await redis_buscar_memoria(limit=5)
# 4. Respuesta consolidada
```

### Usuario: "¿Qué es un barco?"

```python
# Directo a chat con cache
response = await redis_cached_chat("¿Qué es un barco?")
# La respuesta incluirá [cache_hit=true/false]
```

### Usuario: "Busca conversaciones sobre motores"

```python
# Buscar en memoria
results = await redis_buscar_memoria("motores", limit=10)
```

## 🎯 Objetivo Final

**USAR TODAS LAS HERRAMIENTAS** para dar respuestas completas, no solo una herramienta repetitivamente.

**DIVERSIFICAR** el uso según el contexto de la pregunta del usuario.

**EXPLICAR** al usuario qué herramienta se usó y por qué.
