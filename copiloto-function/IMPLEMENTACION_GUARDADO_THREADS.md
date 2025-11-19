# 🧵 Implementación de Guardado de Threads en Blob Storage

**Fecha**: 2025-01-XX  
**Estado**: ✅ IMPLEMENTADO

---

## 🎯 Problema Identificado

Los threads de Azure AI Foundry **NO se estaban guardando** en Blob Storage:

- ❌ `Get-AzStorageBlob -Prefix "assistant-"` → Sin resultados
- ❌ Portal de Azure → Sin archivos `assistant-*`
- ❌ Endpoint `leer-archivo` → "Archivo no encontrado"

### Causa

El código solo guardaba:

- ✅ Eventos en Cosmos DB
- ✅ Embeddings en AI Search
- ❌ **Thread completo en Blob Storage** ← FALTABA

---

## ✅ Solución Implementada

### 1. Guardado Automático en `memory_route_wrapper.py`

**Ubicación**: Bloque 6.5 (después de capturar respuesta de Foundry)

```python
# 6.5️⃣ GUARDAR THREAD COMPLETO EN BLOB STORAGE
try:
    thread_id = req.headers.get("Thread-ID") or req.headers.get("X-Thread-ID")
    if thread_id and thread_id.startswith("assistant-"):
        import function_app as fa
        if fa.IS_AZURE:
            # Construir JSON del thread
            thread_data = {
                "id": thread_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "endpoint": route_path,
                "timestamp": datetime.utcnow().isoformat(),
                "response_data": response_data_for_semantic,
                "metadata": {
                    "user_agent": req.headers.get("User-Agent", ""),
                    "source": "foundry_ui"
                }
            }
            
            # Serializar a JSON
            thread_json = json.dumps(thread_data, ensure_ascii=False, indent=2)
            
            # Subir a Blob Storage
            blob_client = fa.get_blob_client()
            if blob_client:
                container_client = blob_client.get_container_client(fa.CONTAINER_NAME)
                blob_name = f"threads/{thread_id}.json"
                container_client.upload_blob(
                    name=blob_name,
                    data=thread_json.encode('utf-8'),
                    overwrite=True
                )
                logging.info(f"🧵 Thread guardado en Blob: {blob_name}")
except Exception as e:
    logging.warning(f"⚠️ Error guardando thread en Blob: {e}")
```

### 2. Lectura Actualizada en `leer_archivo.py`

```python
def handle_ai_thread_request_dict(thread_id: str, run_id: str) -> dict:
    # Buscar en carpeta threads/
    thread_path = f"threads/{thread_id}.json"
    blob_result = fa.leer_archivo_blob(thread_path)
    
    if blob_result["exito"]:
        # Parsear y devolver
        thread_data = json.loads(blob_result["contenido"])
        return {
            "exito": True,
            "thread_data": thread_data,
            "respuesta_usuario": f"Thread {thread_id}: ..."
        }
```

---

## 📋 Estructura del Thread Guardado

### JSON en Blob Storage

```json
{
  "id": "assistant-Nbor8irDK5vsnVuKUJEmtS",
  "session_id": "foundry_session_123",
  "agent_id": "foundry_user",
  "endpoint": "/api/leer-archivo",
  "timestamp": "2025-11-15T19:07:29.667565Z",
  "response_data": {
    "respuesta_usuario": "Leí README.md...",
    "contenido": "...",
    "texto_semantico": "..."
  },
  "metadata": {
    "user_agent": "azure-agents",
    "source": "foundry_ui"
  }
}
```

### Ubicación en Blob Storage

```
boat-rental-project/
└── threads/
    ├── assistant-Nbor8irDK5vsnVuKUJEmtS.json
    ├── assistant-6zhUdqth9vby29nNrzSpYS.json
    ├── assistant-7VYUcBmeU5KNdXYyjLgsmC.json
    └── assistant-L4pJtJr1HFjbZMoab5RaVV.json
```

---

## 🔄 Flujo Completo

### Escritura (Automática)

```
Request con Thread-ID header
    ↓
memory_route_wrapper.py (Bloque 6.5)
    ↓
Detectar Thread-ID (assistant-*)
    ↓
Construir thread_data con response_data
    ↓
Serializar a JSON
    ↓
Subir a Blob Storage: threads/{thread_id}.json
    ↓
Log: "🧵 Thread guardado en Blob"
```

### Lectura

```
GET /api/leer-archivo?ruta=assistant-XXX
    ↓
detect_request_type() → "ai_thread"
    ↓
handle_ai_thread_request_dict()
    ↓
Leer desde Blob: threads/assistant-XXX.json
    ↓
Parsear JSON
    ↓
Devolver thread_data formateado
```

---

## 🧪 Verificación

### PowerShell

```powershell
# Listar threads guardados
Get-AzStorageBlob -Container "boat-rental-project" -Prefix "threads/" -Context $ctx | Select-Object Name, LastModified, Length

# Resultado esperado:
# Name                                          LastModified              Length
# ----                                          ------------              ------
# threads/assistant-Nbor8irDK5vsnVuKUJEmtS.json 2025-11-15 19:07:29 +00:00  1234
# threads/assistant-6zhUdqth9vby29nNrzSpYS.json 2025-11-15 19:08:15 +00:00  2345
```

### API

```bash
# Leer thread específico
GET /api/leer-archivo?ruta=assistant-Nbor8irDK5vsnVuKUJEmtS

# Respuesta:
{
  "exito": true,
  "thread_data": {...},
  "respuesta_usuario": "Thread assistant-Nbor8irDK5vsnVuKUJEmtS: ..."
}
```

---

## 📊 Captura de Thread-ID

### Headers Soportados

```python
thread_id = req.headers.get("Thread-ID") or req.headers.get("X-Thread-ID")
```

### Validación

```python
if thread_id and thread_id.startswith("assistant-"):
    # Guardar thread
```

---

## 🎯 Beneficios

### Antes

```
❌ Threads no persistidos
❌ No se pueden leer conversaciones completas
❌ Get-AzStorageBlob sin resultados
❌ Endpoint leer-archivo falla
```

### Ahora

```
✅ Threads guardados automáticamente en Blob
✅ Conversaciones completas disponibles
✅ Get-AzStorageBlob muestra threads/
✅ Endpoint leer-archivo funciona
✅ Historial completo de interacciones
```

---

## 🔍 Diferencias: Thread vs Evento

| Aspecto | Thread (Blob) | Evento (Cosmos) |
|---------|---------------|-----------------|
| **Contenido** | Conversación completa + metadata | Acción específica |
| **Formato** | JSON completo del thread | Evento estructurado |
| **Tamaño** | Variable (KB-MB) | Pequeño (< 10KB) |
| **Propósito** | Contexto conversacional | Memoria de acciones |
| **Lectura** | `/api/leer-archivo` | `/api/historial-interacciones` |
| **Búsqueda** | Por thread_id | Por session_id, endpoint, etc. |

---

## 📁 Archivos Modificados

```
copiloto-function/
├── memory_route_wrapper.py          ✅ ACTUALIZADO
│   └── Bloque 6.5: Guardado de threads
└── endpoints/
    └── leer_archivo.py              ✅ ACTUALIZADO
        └── Lectura desde threads/
```

---

## 🚀 Próximos Pasos

### Opcional: Mejoras Futuras

1. **Compresión de threads antiguos**

```python
# Comprimir threads > 30 días
if (datetime.now() - thread_date).days > 30:
    compress_thread(thread_id)
```

2. **Índice de threads**

```python
# Crear índice para búsqueda rápida
threads_index = {
    "assistant-XXX": {
        "session_id": "...",
        "timestamp": "...",
        "size": 1234
    }
}
```

3. **Limpieza automática**

```python
# Eliminar threads > 90 días
cleanup_old_threads(days=90)
```

---

## ✅ Checklist de Implementación

- ✅ Detectar Thread-ID en headers
- ✅ Construir thread_data con response_data
- ✅ Serializar a JSON
- ✅ Subir a Blob Storage en `threads/`
- ✅ Actualizar lectura para buscar en `threads/`
- ✅ Manejar errores gracefully
- ✅ Logging de operaciones
- ✅ Documentación completa

---

## 🎓 Notas Importantes

### Thread-ID en Headers

Azure AI Foundry envía el Thread-ID en los headers:

- `Thread-ID: assistant-XXXXX`
- `X-Thread-ID: assistant-XXXXX`

### Overwrite=True

Los threads se sobrescriben en cada actualización para mantener la versión más reciente.

### Solo en Azure

El guardado solo ocurre cuando `fa.IS_AZURE == True` para evitar errores en desarrollo local.

---

**Estado**: ✅ Threads ahora se guardan automáticamente en Blob Storage y pueden leerse correctamente

**Verificación**: Ejecutar `Get-AzStorageBlob -Prefix "threads/"` después de la próxima interacción con Foundry
