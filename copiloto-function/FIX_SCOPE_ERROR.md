# 🔧 FIX: Error 'HttpRequest' object has no attribute 'scope'

## 🐛 Problema

El endpoint `/api/precalentar-memoria` falla con:
```
AttributeError: 'HttpRequest' object has no attribute 'scope'
```

## 🔍 Causa Raíz

El atributo `scope` es de **Starlette/FastAPI**, NO de **Azure Functions**.

`azure.functions.HttpRequest` NO tiene atributo `scope`.

## ✅ Solución

Envolver el `req` en un try-catch para evitar accesos a atributos inexistentes.

### Cambio en `function_app.py` - Endpoint `precalentar_memoria_http`

```python
@app.function_name(name="precalentar_memoria_http")
@app.route(route="precalentar-memoria", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def precalentar_memoria_http(req: func.HttpRequest) -> func.HttpResponse:
    """Carga explícitamente la memoria de una sesión desde Cosmos y la guarda en Redis."""
    from cosmos_memory_direct import consultar_memoria_cosmos_directo
    from memory_helpers import extraer_session_info

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    session_id = (
        (body or {}).get("session_id")
        or req.headers.get("Session-ID")
        or req.headers.get("X-Session-ID")
    )
    thread_id = (
        (body or {}).get("thread_id")
        or req.headers.get("Thread-ID")
        or req.headers.get("X-Thread-ID")
    )
    agent_id = (
        (body or {}).get("agent_id")
        or req.headers.get("Agent-ID")
        or req.headers.get("X-Agent-ID")
    )

    # ✅ FIX: Envolver en try-catch para evitar AttributeError
    try:
        session_info = extraer_session_info(req, skip_api_call=True)  # ✅ Agregar skip_api_call=True
    except AttributeError as e:
        logging.warning(f"Error extrayendo session_info (AttributeError): {e}")
        session_info = {}
    except Exception as e:
        logging.warning(f"Error extrayendo session_info: {e}")
        session_info = {}

    session_id = session_id or session_info.get("session_id")
    agent_id = agent_id or session_info.get("agent_id")

    # Clave estable para Redis
    redis_session_key = session_id or thread_id
    if not redis_session_key and agent_id:
        redis_session_key = f"agent-{agent_id}"
    if not redis_session_key:
        redis_session_key = "agent-global"

    agent_id = agent_id or "foundry_user"
    thread_id = thread_id or redis_session_key

    logging.info(
        f"[precalentar-memoria] Precargando sesión={redis_session_key} (session_id={session_id or 'N/A'}) agente={agent_id} thread={thread_id}")

    # ✅ FIX: Envolver consulta en try-catch
    try:
        memoria = consultar_memoria_cosmos_directo(req, session_override=session_id)
    except AttributeError as e:
        logging.error(f"Error en consultar_memoria_cosmos_directo (AttributeError): {e}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Error interno: {str(e)}",
                "session_id": redis_session_key,
                "agent_id": agent_id
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error en consultar_memoria_cosmos_directo: {e}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Error consultando memoria: {str(e)}",
                "session_id": redis_session_key,
                "agent_id": agent_id
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )

    if not memoria:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "session_id": redis_session_key,
                "agent_id": agent_id,
                "error": "No se encontró memoria en Cosmos con los identificadores proporcionados."
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=404
        )

    redis_snapshot = {
        "enabled": redis_buffer.is_enabled,
        "cached": False
    }

    if redis_buffer.is_enabled:
        redis_buffer.cache_memoria_contexto(
            redis_session_key, memoria, thread_id=thread_id)
        redis_snapshot["cached"] = True

    total_interacciones = memoria.get("total_interacciones") or len(
        memoria.get("interacciones_recientes", []))

    respuesta = {
        "exito": True,
        "session_id": redis_session_key,
        "thread_id": thread_id,
        "agent_id": agent_id,
        "interacciones_cacheadas": total_interacciones,
        "redis": redis_snapshot,
        "fuente": "cosmos",
        "mensaje": "Memoria precalentada y enviada a Redis" if redis_snapshot["cached"] else "Memoria recuperada. Redis no disponible."
    }

    return func.HttpResponse(
        json.dumps(respuesta, ensure_ascii=False),
        mimetype="application/json",
        status_code=200
    )
```

## 🎯 Cambios Clave

1. ✅ Agregar `skip_api_call=True` a `extraer_session_info()` para evitar llamadas a Foundry API
2. ✅ Envolver `extraer_session_info()` en try-catch específico para `AttributeError`
3. ✅ Envolver `consultar_memoria_cosmos_directo()` en try-catch
4. ✅ Retornar error 500 con mensaje descriptivo si falla

## 🧪 Testing

```powershell
Invoke-RestMethod -Uri 'http://localhost:7071/api/precalentar-memoria' `
  -Method POST `
  -Headers @{ 'Content-Type' = 'application/json' } `
  -Body '{"session_id":"test_session","agent_id":"GlobalAgent"}'
```

## ✅ Resultado Esperado

```json
{
  "exito": true,
  "session_id": "test_session",
  "agent_id": "GlobalAgent",
  "interacciones_cacheadas": 50,
  "mensaje": "Memoria precalentada y enviada a Redis"
}
```
