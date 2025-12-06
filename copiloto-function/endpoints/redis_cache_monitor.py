"""
Endpoint: redis-cache-monitor
Monitoreo específico de la estrategia de caché dual (sesión + global) en Redis.
Complementa al diagnóstico general existente.
"""
import json
import logging
from typing import Any, Dict, List

import azure.functions as func

from function_app import app
from services.redis_buffer_service import redis_buffer


@app.function_name(name="redis_cache_monitor")
@app.route(route="redis-cache-monitor", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def redis_cache_monitor(req: func.HttpRequest) -> func.HttpResponse:
    if not redis_buffer.is_enabled:
        return func.HttpResponse(
            json.dumps({"error": "Redis cache disabled"}),
            mimetype="application/json",
            status_code=503,
        )

    try:
        patterns: Dict[str, str] = {
            "llm_session_keys": "llm:*:session:*",
            "llm_global_keys": "llm:*:model:*:msg:*",
            "llm_auto_sessions": "llm:*:session:auto-*",
            "memoria_keys": "memoria:*",
            "thread_keys": "thread:*",
            "narrativa_keys": "narrativa:*",
        }

        counts: Dict[str, Any] = {}
        sample_keys: Dict[str, List[str]] = {}

        for name, pattern in patterns.items():
            try:
                keys = redis_buffer.keys(pattern)
                counts[name] = len(keys)
                sample_keys[name] = [
                    k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
                    for k in keys[:3]
                ]
            except Exception as e:  # pragma: no cover
                logging.warning(f"[RedisCacheMonitor] Error listando {pattern}: {e}")
                counts[name] = f"error: {str(e)[:100]}"
                sample_keys[name] = []

        stats = redis_buffer.get_cache_stats()

        ttl_samples: Dict[str, Any] = {}
        client = getattr(redis_buffer, "_client", None)
        if client:
            for pattern_name, keys in sample_keys.items():
                if keys and pattern_name.startswith("llm_"):
                    for key in keys[:2]:
                        try:
                            ttl_val = client.ttl(key)
                            ttl_samples[key] = ttl_val if ttl_val >= 0 else "expired"
                        except Exception:
                            ttl_samples[key] = "error"

        hits = stats.get("keyspace_hits", 0) or 0
        misses = stats.get("keyspace_misses", 0) or 0
        total_ops = hits + misses
        hit_ratio = hits / total_ops if total_ops > 0 else 0

        issues: List[str] = []
        auto_sessions = counts.get("llm_auto_sessions", 0)
        session_keys = counts.get("llm_session_keys", 0)
        global_keys = counts.get("llm_global_keys", 0)

        if isinstance(auto_sessions, int) and auto_sessions > 100:
            issues.append(f"Muchas sesiones auto-generadas: {auto_sessions}")
        if isinstance(session_keys, int) and isinstance(global_keys, int):
            if session_keys > 0 and global_keys == 0:
                issues.append("Cache global no está siendo escrita (solo session cache)")
        if total_ops > 100 and hit_ratio < 0.3:
            issues.append(f"Hit ratio bajo: {hit_ratio:.1%}")

        result = {
            "cache_strategy": "dual_cache_session_global",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "redis_enabled": redis_buffer.is_enabled,
            "key_counts": counts,
            "session_vs_global_ratio": f"{session_keys}:{global_keys}",
            "cache_effectiveness": {
                "hit_ratio": f"{hit_ratio:.1%}",
                "hits": hits,
                "misses": misses,
                "total_operations": total_ops,
            },
            "sample_keys": {k: v for k, v in sample_keys.items() if v},
            "ttl_samples": ttl_samples,
            "redis_stats": {
                "used_memory": stats.get("used_memory_human", "unknown"),
                "dbsize": stats.get("dbsize", "unknown"),
                "connected_clients": stats.get("connected_clients", "unknown"),
                "failure_streak": stats.get("failure_streak", 0),
            },
            "issues": issues,
            "issues_count": len(issues),
            "recommendations": [
                "Cache dual activa: session + global keys",
                f"Hit ratio objetivo: >60% (actual: {hit_ratio:.1%})",
                "Cache global permite reuso cross-sesión",
            ],
        }

        return func.HttpResponse(
            json.dumps(result, indent=2, default=str),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:  # pragma: no cover
        logging.error(f"[RedisCacheMonitor] Error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
