"""
Health check ligero para la caché Redis (más específico que el diagnóstico general).
"""
import json
import azure.functions as func

from function_app import app
from services.redis_buffer_service import redis_buffer


@app.function_name(name="redis_cache_health")
@app.route(route="redis-cache-health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def redis_cache_health(req: func.HttpRequest) -> func.HttpResponse:
    health = {
        "status": "unknown",
        "redis_enabled": redis_buffer.is_enabled,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "checks": {},
    }

    if not redis_buffer.is_enabled:
        health["status"] = "disabled"
        health["message"] = "Redis cache is disabled"
        return func.HttpResponse(json.dumps(health), mimetype="application/json", status_code=200)

    try:
        client = getattr(redis_buffer, "_client", None)
        ping_ok = bool(client.ping()) if client else False
        llm_keys = redis_buffer.keys("llm:*")
        auto_keys = redis_buffer.keys("llm:*:session:auto-*")

        health["checks"]["ping"] = ping_ok
        health["checks"]["has_llm_keys"] = len(llm_keys) > 0
        health["checks"]["llm_keys_count"] = len(llm_keys)
        health["checks"]["auto_sessions_count"] = len(auto_keys)

        if ping_ok:
            if health["checks"]["has_llm_keys"]:
                health["status"] = "healthy"
                health["message"] = "Cache activa y con datos"
            else:
                health["status"] = "no_data"
                health["message"] = "Redis responde, sin datos cacheados aún"
        else:
            health["status"] = "unhealthy"
            health["message"] = "Redis no responde al ping"

        return func.HttpResponse(json.dumps(health, indent=2), mimetype="application/json", status_code=200)

    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)
        return func.HttpResponse(json.dumps(health), mimetype="application/json", status_code=500)
