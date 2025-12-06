"""Agente de monitoreo de la cache Redis para consumo desde Foundry o copilotos.

Consulta los endpoints expuestos por la Function App:
 - /api/redis-cache-health   (chequeo ligero)
 - /api/redis-cache-monitor  (métricas detalladas de la estrategia dual)

Usa httpx (ya presente en requirements) y expone un flujo end‑to‑end que
interpreta resultados y devuelve recomendaciones estructuradas.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx


class RedisCacheMonitoringAgent:
    """Agente especializado en monitoreo de cache Redis."""

    def __init__(self, function_app_base_url: str, timeout: float = 10.0) -> None:
        self.base_url = function_app_base_url.rstrip("/")
        self.timeout = timeout

    async def check_cache_health(self) -> Dict[str, Any]:
        """Health check rápido - pensado para polling frecuente."""
        url = f"{self.base_url}/api/redis-cache-health"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "error", "message": f"HTTP {resp.status_code}"}

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Métricas detalladas - uso periódico (no en hot loop)."""
        url = f"{self.base_url}/api/redis-cache-monitor"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 503:
                return {"error": "Redis cache disabled"}
            return {"error": f"HTTP {resp.status_code}"}

    @staticmethod
    def _parse_hit_ratio(value: Any) -> float:
        """Convierte '64.7%' a 0.647; si falla devuelve 0.0."""
        if isinstance(value, str) and value.endswith("%"):
            try:
                return float(value.rstrip("%")) / 100.0
            except ValueError:
                return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def analyze_and_recommend(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza métricas y genera recomendaciones para agentes."""
        analysis: Dict[str, Any] = {
            "timestamp": metrics.get("timestamp"),
            "overall_status": "unknown",
            "recommendations": [],
            "actions": [],
            "warnings": [],
        }

        if not metrics.get("redis_enabled", False):
            analysis["overall_status"] = "critical"
            analysis["recommendations"].append("Habilitar Redis cache")
            analysis["actions"].append("check_redis_configuration")
            return analysis

        effectiveness = metrics.get("cache_effectiveness", {})
        hit_ratio = self._parse_hit_ratio(effectiveness.get("hit_ratio", "0%"))

        if hit_ratio > 0.6:
            analysis["overall_status"] = "optimal"
            analysis["recommendations"].append(
                f"Hit ratio excelente: {effectiveness.get('hit_ratio', 'n/a')}"
            )
        elif hit_ratio > 0.3:
            analysis["overall_status"] = "good"
            analysis["recommendations"].append(
                f"Hit ratio aceptable: {effectiveness.get('hit_ratio', 'n/a')}"
            )
        else:
            analysis["overall_status"] = "needs_attention"
            analysis["recommendations"].append(
                f"Hit ratio bajo: {effectiveness.get('hit_ratio', 'n/a')}"
            )
            analysis["actions"].append("review_cache_strategy")

        issues: List[str] = metrics.get("issues", []) or []
        if issues:
            analysis["overall_status"] = "needs_attention"
            analysis["warnings"].extend(issues)
            analysis["actions"].append("address_cache_issues")

        key_counts = metrics.get("key_counts", {})
        session_keys = key_counts.get("llm_session_keys", 0)
        global_keys = key_counts.get("llm_global_keys", 0)
        if isinstance(session_keys, int) and isinstance(global_keys, int):
            if session_keys > 0 and global_keys == 0:
                analysis["warnings"].append("Cache global no se está escribiendo")
                analysis["actions"].append("verify_global_cache_writes")

        return analysis

    async def full_monitoring_workflow(self) -> Dict[str, Any]:
        """Flujo completo de monitoreo para agentes."""
        health = await self.check_cache_health()

        if health.get("status") != "healthy":
            return {
                "workflow": "cache_monitoring",
                "status": "interrupted",
                "health_status": health.get("status"),
                "message": f"Cache no saludable: {health.get('message')}",
                "actions": ["investigate_redis_connection"],
            }

        metrics = await self.get_detailed_metrics()
        if "error" in metrics:
            return {
                "workflow": "cache_monitoring",
                "status": "error",
                "error": metrics.get("error"),
                "actions": ["check_monitor_endpoint"],
            }

        analysis = self.analyze_and_recommend(metrics)

        return {
            "workflow": "cache_monitoring",
            "status": "completed",
            "timestamp": metrics.get("timestamp"),
            "health_check": health,
            "detailed_metrics": metrics,
            "analysis": analysis,
            "summary": {
                "redis_enabled": metrics.get("redis_enabled", False),
                "hit_ratio": metrics.get("cache_effectiveness", {}).get("hit_ratio", "0%"),
                "issues_count": metrics.get("issues_count", 0),
                "overall_status": analysis.get("overall_status", "unknown"),
            },
        }


# Ejecución manual de prueba: python redis_cache_monitoring_agent.py https://<func-app>.azurewebsites.net
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python redis_cache_monitoring_agent.py <function_app_base_url>")
        sys.exit(1)

    base_url = sys.argv[1]
    agent = RedisCacheMonitoringAgent(base_url)

    async def _run() -> None:
        result = await agent.full_monitoring_workflow()
        from pprint import pprint

        pprint(result)

    asyncio.run(_run())
