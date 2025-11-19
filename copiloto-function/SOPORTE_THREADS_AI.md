# 🧵 Soporte para Threads de Azure AI Foundry

**Fecha**: 2025-01-XX  
**Estado**: ✅ IMPLEMENTADO

---

## 🎯 Problema Resuelto

El agente intentaba leer threads de Azure AI Foundry (formato `assistant-XXXXX`) como si fueran archivos normales, causando errores "Archivo no encontrado".

### Threads vs Archivos

| Tipo | Formato | Ubicación | Contenido |
|------|---------|-----------|-----------|
| **Thread** | `assistant-Nbor8irDK5vsnVuKUJEmtS` | Blob Storage | Conversación completa (JSON) |
| **Archivo** | `scripts/deploy.sh` | Blob Storage / Local | Código, texto, etc. |

---

## ✅ Solución Implementada

### 1. Detección Automática de Threads

```python
def detect_request_type(path: str) -> str:
    # Detectar threads de Azure AI Foundry
    if path.startswith("assistant-") or path.startswith("thread_"):
        return "ai_thread"
    
    # ... otros tipos
```

### 2. Handler Específico para Threads

```python
def handle_ai_thread_request_dict(thread_id: str, run_id: str) -> dict:
    """Lee y parsea threads de Azure AI Foundry desde Blob Storage"""
    
    # 1. Leer desde Blob Storage
    blob_result = fa.leer_archivo_blob(thread_id)
    
    # 2. Parsear JSON
    thread_data = json.loads(contenido_raw)
    
    # 3. Extraer mensajes
    mensajes = thread_data.get("messages", [])
    
    # 4. Formatear conversación
    conversacion = []
    for msg in mensajes:
        role = msg.get("role")
        content = msg.get("content")
        conversacion.append(f"[{role}] {content}")
    
    # 5. Generar resumen
    resumen = f"Thread {thread_id}: {len(mensajes)} mensajes\n\n"
    resumen += "\n".join(conversacion[:10])
    
    return {
        "exito": True,
        "thread_data": thread_data,
        "mensajes": mensajes,
        "total_mensajes": len(mensajes),
        "respuesta_usuario": resumen  # Para el agente
    }
```

---

## 📋 Estructura de un Thread

### JSON Típico

```json
{
  "id": "assistant-Nbor8irDK5vsnVuKUJEmtS",
  "object": "thread",
  "created_at": 1700000000,
  "metadata": {},
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "dame un resumen de lo que estuvimos haciendo",
      "created_at": 1700000001
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Aquí tienes un resumen...",
      "created_at": 1700000002
    }
  ]
}
```

### Campos Extraídos

- `messages`: Array de mensajes
- `role`: "user" o "assistant"
- `content`: Texto del mensaje
- `created_at`: Timestamp
- `metadata`: Información adicional

---

## 🔄 Flujo de Lectura

```
Usuario: "lee assistant-Nbor8irDK5vsnVuKUJEmtS"
    ↓
detect_request_type()
    ↓ "ai_thread"
handle_ai_thread_request_dict()
    ↓
1. Leer desde Blob Storage
2. Parsear JSON
3. Extraer mensajes
4. Formatear conversación
5. Generar resumen
    ↓
Respuesta con conversación formateada
```

---

## 📊 Respuesta del Endpoint

### Éxito

```json
{
  "exito": true,
  "contenido": "{...}",  // JSON raw
  "thread_data": {...},  // Objeto parseado
  "mensajes": [...],     // Array de mensajes
  "total_mensajes": 15,
  "tipo": "ai_thread",
  "ruta": "blob://boat-rental-project/assistant-XXX",
  "fuente": "Azure Blob Storage (Thread)",
  "mensaje": "Thread leído: assistant-XXX (15 mensajes)",
  "texto_semantico": "Thread assistant-XXX: 15 mensajes...",
  "respuesta_usuario": "Thread assistant-XXX: 15 mensajes\n\n[user] mensaje 1\n[assistant] respuesta 1\n..."
}
```

### Error

```json
{
  "exito": false,
  "error": "Thread no encontrado: assistant-XXX",
  "mensaje": "No se pudo leer el thread assistant-XXX desde Blob Storage",
  "sugerencias": [
    "Verificar que el thread existe con /api/listar-blobs",
    "Confirmar el ID del thread",
    "Usar historial-interacciones para ver conversaciones"
  ]
}
```

---

## 🎯 Casos de Uso

### 1. Leer Thread Específico

```bash
GET /api/leer-archivo?ruta=assistant-Nbor8irDK5vsnVuKUJEmtS
```

**Respuesta**:

```
Thread assistant-Nbor8irDK5vsnVuKUJEmtS: 15 mensajes

[user] dame un resumen de lo que estuvimos haciendo
[assistant] Aquí tienes un resumen de las interacciones...
[user] ¿qué archivos leímos?
[assistant] Leímos los siguientes archivos...
...
```

### 2. Listar Threads Disponibles

```bash
GET /api/listar-blobs?prefix=assistant-
```

**Respuesta**:

```json
{
  "blobs": [
    "assistant-Nbor8irDK5vsnVuKUJEmtS",
    "assistant-6zhUdqth9vby29nNrzSpYS",
    "assistant-7VYUcBmeU5KNdXYyjLgsmC"
  ]
}
```

### 3. Comparar con Historial

```bash
# Thread: Conversación completa guardada
GET /api/leer-archivo?ruta=assistant-XXX

# Historial: Interacciones con endpoints
GET /api/historial-interacciones
```

---

## 🔍 Diferencias: Thread vs Historial

| Aspecto | Thread | Historial |
|---------|--------|-----------|
| **Contenido** | Conversación user-assistant | Llamadas a endpoints |
| **Formato** | JSON de Azure AI Foundry | Eventos de Cosmos DB |
| **Ubicación** | Blob Storage | Cosmos DB |
| **Propósito** | Contexto conversacional | Memoria de acciones |
| **Lectura** | `/api/leer-archivo` | `/api/historial-interacciones` |

---

## 🚀 Mejoras Futuras (Opcional)

### 1. Búsqueda en Threads

```python
GET /api/buscar-threads?query=deployment&limit=10
```

### 2. Resumen Automático

```python
GET /api/resumir-thread?thread_id=assistant-XXX
```

### 3. Exportar Thread

```python
GET /api/exportar-thread?thread_id=assistant-XXX&format=markdown
```

---

## 📁 Archivo Modificado

```
copiloto-function/
└── endpoints/
    └── leer_archivo.py          ✅ ACTUALIZADO
        ├── detect_request_type()         → Detecta threads
        ├── handle_ai_thread_request_dict() → Lee y parsea threads
        └── Flujo actualizado
```

---

## ✅ Verificación

### Antes del Fix

```
Usuario: "lee assistant-Nbor8irDK5vsnVuKUJEmtS"
Agente: ❌ "Archivo no encontrado: assistant-Nbor8irDK5vsnVuKUJEmtS"
```

### Después del Fix

```
Usuario: "lee assistant-Nbor8irDK5vsnVuKUJEmtS"
Agente: ✅ "Thread assistant-Nbor8irDK5vsnVuKUJEmtS: 15 mensajes

[user] dame un resumen...
[assistant] Aquí tienes un resumen...
..."
```

---

## 🎓 Recomendaciones

### Para el Agente

1. **Usar historial-interacciones** para resúmenes de acciones
2. **Usar leer-archivo con thread_id** para ver conversaciones completas
3. **Listar threads** con `/api/listar-blobs?prefix=assistant-`

### Para el Usuario

1. Los threads son **conversaciones guardadas** de Azure AI Foundry
2. El **historial** son **acciones ejecutadas** (leer archivos, ejecutar comandos, etc.)
3. Ambos son complementarios y útiles para diferentes propósitos

---

**Estado**: ✅ Threads de Azure AI Foundry ahora se pueden leer correctamente
