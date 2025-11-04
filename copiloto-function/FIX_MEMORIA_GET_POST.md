# ✅ FIX: Memoria en GET y POST

## 🐛 Problema

`memoria_aplicada: false` en requests GET porque el wrapper solo consultaba memoria cuando había body JSON.

## ✅ Solución

### 1. Wrapper Consulta Memoria Siempre

**Archivo**: `services/memory_decorator.py`

**Cambio**:

```python
# ANTES: Solo si había body JSON
if body and body.get("session_id"):
    consultar_memoria_sesion(session_id, agent_id)

# DESPUÉS: Siempre si hay session_id válido
if session_id and agent_id and not session_id.startswith("auto_"):
    consultar_memoria_sesion(session_id, agent_id)
```

### 2. Endpoint Acepta GET y POST

**Archivo**: `function_app.py` (línea 15280)

**Cambio**:

```python
# ANTES
@app.route(route="auditar-deploy", methods=["GET"])

# DESPUÉS
@app.route(route="auditar-deploy", methods=["GET", "POST"])
```

## 🧪 Test

```bash
# GET con query params
curl -X GET "http://localhost:7071/api/auditar-deploy?Session-ID=test-session&Agent-ID=test-agent"

# POST con headers
curl -X POST http://localhost:7071/api/auditar-deploy \
  -H "Session-ID: test-session" \
  -H "Agent-ID: test-agent"
```

## 📊 Resultado Esperado

```json
{
  "exito": true,
  "state": "Running",
  "memoria_aplicada": true,  // ← Ahora true en GET y POST
  "enriquecimiento": {
    "contexto_previo": "...",
    "interacciones_previas": 5
  }
}
```

---

**Estado**: ✅ Implementado
**Archivos**: `memory_decorator.py`, `function_app.py`
**Impacto**: Memoria funciona en GET y POST
