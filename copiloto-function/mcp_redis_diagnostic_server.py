#!/usr/bin/env python3
"""
Servidor MCP SOLO para diagnóstico de la cache Redis.

- No responde a usuarios finales; se usa para monitoreo y tuning.
- Consulta los endpoints /api/redis-cache-health y /api/redis-cache-monitor.
"""
import json
import logging
import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP

# Configuración del transporte MCP (por defecto HTTP en 0.0.0.0:8001)
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
# Puerto diferente al servidor de chat
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
FUNCTION_APP_URL = os.getenv(
    "FUNCTION_APP_URL",
    "https://copiloto-semantico-func-us2.azurewebsites.net",
).rstrip("/")

mcp = FastMCP("redis-diagnostics", host=MCP_HOST,
              port=MCP_PORT, streamable_http_path="/mcp")
logging.basicConfig(level=logging.INFO)


async def _fetch_json(url: str) -> Dict[str, Any]:
    """Realiza GET y retorna JSON o error estructurado."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(url)
        try:
            data: Dict[str, Any] = resp.json()
        except Exception:
            data: Dict[str, Any] = {"error": f"Respuesta no JSON: {resp.text}"}
        if "status_code" not in data:
            data["status_code"] = resp.status_code
        return data


class RedisCacheDiagnosticTool:
    """Tool de diagnóstico para cache Redis dual."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def diagnose_cache(self, detailed_analysis: bool = False) -> Dict[str, Any]:
        # 1) Health básico
        health = await _fetch_json(f"{self.base_url}/api/redis-cache-health")
        if health.get("status") != "healthy":
            return {
                "diagnosis": "cache_unhealthy",
                "severity": "high",
                "message": health.get("message", "Redis cache no saludable"),
                "health": health,
                "recommendations": [
                    "Verificar conexión a Redis/credenciales",
                    "Revisar REDIS_KEY/Managed Identity",
                ],
            }

        # 2) Métricas detalladas
        metrics = await _fetch_json(f"{self.base_url}/api/redis-cache-monitor")
        if "error" in metrics:
            return {
                "diagnosis": "monitor_unavailable",
                "severity": "medium",
                "message": f"No se pudieron obtener métricas: {metrics.get('error')}",
            }

        # 3) Análisis semántico
        analysis = self._analyze(metrics)

        result: Dict[str, Any] = {
            "diagnosis": "full_analysis_completed",
            "severity": "low" if analysis["overall_status"] == "optimal" else "medium",
            "timestamp": metrics.get("timestamp"),
            "summary": {
                "redis_enabled": metrics.get("redis_enabled", False),
                "hit_ratio": metrics.get("cache_effectiveness", {}).get("hit_ratio", "0%"),
                "issues_detected": metrics.get("issues_count", 0),
            },
            "analysis": analysis,
        }

        if detailed_analysis:
            result["health"] = health
            result["metrics"] = metrics
        return result

    def _analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        eff = metrics.get("cache_effectiveness", {})
        hit_ratio_str = eff.get("hit_ratio", "0%")
        try:
            hit_ratio = float(hit_ratio_str.replace("%", "")) / 100
        except Exception:
            hit_ratio = 0.0

        key_counts = metrics.get("key_counts", {})
        session_keys = key_counts.get("llm_session_keys", 0) or 0
        global_keys = key_counts.get("llm_global_keys", 0) or 0
        issues = metrics.get("issues", []) or []

        score = int(hit_ratio * 70)
        if global_keys > 0:
            score += 20

        if score >= 80:
            status = "optimal"
            performance = "Cache funcionando excelentemente"
        elif score >= 60:
            status = "good"
            performance = "Cache adecuada"
        elif score >= 40:
            status = "needs_attention"
            performance = "Cache con margen de mejora"
        else:
            status = "needs_improvement"
            performance = "Cache con problemas de efectividad"

        recommendations = []
        if hit_ratio < 0.3:
            recommendations.append(
                "Hit ratio bajo: ajustar TTLs o revisar misses")
        if session_keys > 0 and global_keys == 0:
            recommendations.append("Cache global no se está escribiendo")
        for issue in issues:
            if "auto-generadas" in issue:
                recommendations.append(
                    "Muchas sesiones auto: revisar generación de session_id")

        if not recommendations:
            recommendations.append("Configu­ración óptima")

        return {
            "overall_status": status,
            "performance_assessment": performance,
            "efficiency_score": min(100, score),
            "detected_issues": issues,
            "recommendations": recommendations,
        }


tool = RedisCacheDiagnosticTool(FUNCTION_APP_URL)


@mcp.tool()
async def redis_full_diagnostic(detailed_analysis: bool = False) -> str:
    """
    Ejecuta el flujo completo de diagnóstico de Redis combinando health + monitor.
    Retorna análisis consolidado y recomendaciones priorizadas.
    """
    try:
        result = await tool.diagnose_cache(detailed_analysis=detailed_analysis)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as exc:  # pragma: no cover - protección final
        return json.dumps(
            {"diagnosis": "tool_error", "severity": "high", "error": str(exc)},
            indent=2,
            ensure_ascii=False,
        )


@mcp.tool()
async def redis_health_check() -> str:
    """
    Verifica el estado básico de la conexión Redis y disponibilidad de datos.
    Realiza ping, valida credenciales y cuenta claves disponibles.
    """
    logging.info("[MCP] Ejecutando redis_health_check")
    try:
        health = await _fetch_json(f"{FUNCTION_APP_URL}/api/redis-cache-health")
        logging.info(
            f"[MCP] redis_health_check completado - status: {health.get('status')}")
        return json.dumps(health, indent=2, ensure_ascii=False)
    except Exception as exc:
        logging.error(f"[MCP] Error en redis_health_check: {exc}")
        return json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def redis_cache_monitor() -> str:
    """
    Obtiene métricas detalladas del rendimiento de Redis cache.
    Incluye hit ratio, conteo de claves, TTLs y análisis de efectividad.
    """
    logging.info("[MCP] Ejecutando redis_cache_monitor")
    try:
        metrics = await _fetch_json(f"{FUNCTION_APP_URL}/api/redis-cache-monitor")
        logging.info(
            f"[MCP] redis_cache_monitor completado - hit_ratio: {metrics.get('cache_effectiveness', {}).get('hit_ratio', 'N/A')}")
        return json.dumps(metrics, indent=2, ensure_ascii=False)
    except Exception as exc:
        logging.error(f"[MCP] Error en redis_cache_monitor: {exc}")
        return json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def redis_buscar_memoria(query: str = "", limit: int = 10) -> str:
    """
    Busca y recupera entradas de memoria almacenadas en Redis.
    Permite inspeccionar contenido de cache y patrones de almacenamiento.

    Args:
        query: Término de búsqueda opcional para filtrar resultados
        limit: Número máximo de resultados a retornar (default: 10)
    """
    logging.info(
        f"[MCP] Ejecutando redis_buscar_memoria - query: '{query}', limit: {limit}")
    try:
        params = {"q": query, "limit": limit} if query else {"limit": limit}
        url = f"{FUNCTION_APP_URL}/api/buscar-memoria"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            try:
                data = resp.json() if resp.headers.get(
                    "content-type", "").startswith("application/json") else {"error": resp.text}
            except Exception:
                data = {"error": resp.text}
            if not isinstance(data, dict):
                data = {"error": str(data)}
            data["http_status"] = str(resp.status_code)

        logging.info(
            f"[MCP] redis_buscar_memoria completado - resultados: {len(data.get('resultados', []))}")
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as exc:
        logging.error(f"[MCP] Error en redis_buscar_memoria: {exc}")
        return json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def verificar_health_cache() -> str:
    """
    Health check rápido de Redis cache (ping + presencia de llaves).
    Alias para redis_health_check para compatibilidad.
    """
    return await redis_health_check()


def main() -> None:
    logging.info(f"Iniciando MCP diagnóstico en {MCP_HOST}:{MCP_PORT}")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
