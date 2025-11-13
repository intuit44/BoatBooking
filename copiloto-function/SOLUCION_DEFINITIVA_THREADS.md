# SOLUCIÓN DEFINITIVA: Captura de Threads de Foundry

## ❌ PROBLEMA REAL

Foundry **NO envía thread_id** en:

- Headers
- Query params  
- Body JSON

El payload que llega es:

```json
{
  "id": "call_XXX",
  "type": "openapi",
  "function": {
    "name": "CopilotoFunctionApp_getStatus",
    "arguments": "{}"
  }
}
```

## ✅ SOLUCIÓN CORRECTA

**Foundry DEBE enviar el thread_id**. Hay 2 formas:

### Opción 1: Configurar Headers en Foundry UI

Al registrar la herramienta OpenAPI en Foundry, agregar headers personalizados:

```json
{
  "headers": {
    "X-Thread-ID": "${context.thread_id}",
    "X-Agent-ID": "${context.agent_id}"
  }
}
```

**Ubicación en Foundry:**

- Tools → OpenAPI Tool → Configuration → Custom Headers

### Opción 2: Modificar el Agente para que envíe thread_id

En la configuración del agente en Foundry:

```yaml
tools:
  - type: openapi
    spec_url: "https://copiloto-semantico-func-us2.azurewebsites.net/openapi.yaml"
    headers:
      X-Thread-ID: "{{thread.id}}"
      X-Agent-ID: "{{agent.id}}"
```

### Opción 3: Endpoint Proxy en Foundry

Crear un endpoint intermedio que capture el thread_id y lo reenvíe:

```python
# En Foundry (Python)
@app.route("/proxy/<path:endpoint>", methods=["POST"])
def proxy_with_thread(endpoint):
    thread_id = get_current_thread_id()  # Foundry SDK
    
    headers = {
        "X-Thread-ID": thread_id,
        "X-Agent-ID": get_agent_id()
    }
    
    response = requests.post(
        f"https://copiloto-semantico-func-us2.azurewebsites.net/api/{endpoint}",
        json=request.json,
        headers=headers
    )
    
    return response.json()
```

## 🔧 BACKEND: Normalización Automática

El backend YA está preparado para recibir thread_id de múltiples formas:

```python
# memory_helpers.py - extraer_session_info()
session_id = (
    req.headers.get("X-Thread-ID") or           # Opción 1
    req.headers.get("Thread-ID") or             # Alternativa
    req.params.get("thread_id") or              # Query param
    body.get("thread_id") or                    # Body JSON
    body.get("context", {}).get("thread_id")    # Contexto anidado
)
```

## 📊 ESTADO ACTUAL

| Componente | Estado | Acción Requerida |
|------------|--------|------------------|
| Backend normalización | ✅ Listo | Ninguna |
| Wrapper integración | ✅ Listo | Ninguna |
| Foundry configuración | ❌ Falta | **CONFIGURAR HEADERS** |
| OpenAPI spec | ✅ Listo | Ninguna |

## 🎯 PRÓXIMOS PASOS

1. **Ir a Foundry UI**
2. **Tools → CopilotoFunctionApp**
3. **Configuration → Custom Headers**
4. **Agregar:**

   ```
   X-Thread-ID: ${context.thread_id}
   X-Agent-ID: ${context.agent_id}
   ```

5. **Save**
6. **Test**: Invocar cualquier endpoint y verificar logs

## 🧪 VALIDACIÓN

Después de configurar, verificar en logs de Function App:

```
Session ID capturado: thread_XXXXX
Agent ID capturado: agent_XXXXX
```

Si aparece `fallback_session`, Foundry NO está enviando el header.

## 📝 DOCUMENTACIÓN FOUNDRY

Consultar:

- <https://learn.microsoft.com/azure/ai-studio/how-to/develop/agents>
- <https://learn.microsoft.com/azure/ai-studio/how-to/develop/custom-tools>

Buscar: "Custom headers in OpenAPI tools"
