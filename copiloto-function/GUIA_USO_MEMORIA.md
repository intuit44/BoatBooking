# 📘 Guía de Uso Correcto - Sistema de Memoria

## 🎯 Endpoint Principal: `/api/copiloto`

### ✅ Uso Correcto

```json
POST /api/copiloto
Headers:
  Session-ID: assistant-xxxxx
  Agent-ID: foundry-autopilot
  Content-Type: application/json

Body:
{
  "mensaje": "qué hemos hablado"
}
```

**Respuesta esperada:**
```json
{
  "exito": true,
  "respuesta_usuario": "Narrativa enriquecida desde threads + Cosmos + AI Search...",
  "accion": "narrativa_enriquecida",
  "metadata": {
    "fuentes": ["threads", "cosmos", "ai_search"],
    "sin_embeddings_adicionales": true
  }
}
```

### ❌ Uso Incorrecto

**NO usar `/api/historial-interacciones` con filtros:**
```json
GET /api/historial-interacciones?session_id=xxx&limit=10
```
Esto devuelve eventos crudos, no la narrativa enriquecida.

## 🔑 Headers Requeridos

| Header | Descripción | Ejemplo |
|--------|-------------|---------|
| `Session-ID` | ID de sesión/thread | `assistant-2YzP3PSn...` |
| `Agent-ID` | ID del agente | `foundry-autopilot` |
| `Thread-ID` | (Opcional) ID explícito de thread | `assistant-xxxxx` |

## 📝 Campos de Respuesta

### Campos que Foundry debe consumir:

1. **`respuesta_usuario`**: Narrativa principal enriquecida
2. **`texto_semantico`**: Resumen corto (500 chars)
3. **`accion`**: Tipo de acción ejecutada
4. **`metadata.fuentes`**: Fuentes de datos usadas

### ❌ NO consumir:

- `interacciones` (array crudo de eventos)
- `resultado.mensaje` (solo si no hay `respuesta_usuario`)

## 🧵 Guardado de Threads

Los threads se guardan automáticamente en:
- **Blob Storage**: `threads/{thread_id}.json`
- **Naming**: `thread_{session_id}_{timestamp}` si no hay Thread-ID

### Para que se guarden correctamente:

1. Enviar `Thread-ID` en headers (preferido)
2. O usar `Session-ID` que empiece con `assistant-`
3. Dejar que el flujo complete (no cortar con early returns)

## 🔍 Verificar Threads Guardados

```bash
GET /api/listar-blobs?prefix=threads/&top=10
```

## 🧪 Testing

Ejecutar script de prueba:
```bash
cd copiloto-function
python test_foundry_flows.py
```

Esto simula los payloads exactos que Foundry envía.

## 📊 Flujo Completo

```
Usuario → /api/copiloto (mensaje)
  ↓
Detectar comando no reconocido
  ↓
Pipeline: threads + Cosmos + AI Search
  ↓
Generar narrativa enriquecida
  ↓
Return directo (sin embeddings adicionales)
  ↓
Guardar thread en Blob Storage
```

## ⚡ Optimizaciones

- **Sin embeddings adicionales**: Cuando `accion == "narrativa_enriquecida"`, no se ejecutan consultas vectoriales
- **Cache inteligente**: Threads recientes se cachean
- **Guardado automático**: Threads se persisten antes de cada respuesta

## 🚨 Troubleshooting

### Problema: "No reconozco ese comando"
**Solución**: Verificar que el mensaje llegue en el campo `mensaje` del body

### Problema: Threads no se guardan
**Solución**: Enviar `Thread-ID` en headers o `Session-ID` con formato `assistant-*`

### Problema: Respuesta genérica en vez de narrativa
**Solución**: Verificar que Foundry consuma `respuesta_usuario` en vez de `interacciones`
