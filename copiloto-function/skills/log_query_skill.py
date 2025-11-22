# -*- coding: utf-8 -*-
"""
Skill especializado para consultar y analizar logs desde Log Analytics.
Se evita duplicar endpoints HTTP y se usa caché para reducir latencia.
"""

from datetime import timedelta, datetime
import logging
import os
from typing import Any, Dict, List, Optional

try:
    from azure.monitor.query import LogsQueryClient  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore
except Exception:  # pragma: no cover - dependencias opcionales
    LogsQueryClient = None
    DefaultAzureCredential = None

from semantic_intent_classifier import preprocess_text
from services.redis_buffer_service import redis_buffer


class LogQuerySkill:
    """Consulta logs en Log Analytics sin mezclar responsabilidades del wrapper."""

    def __init__(self, workspace_id: Optional[str] = None):
        self.workspace_id = workspace_id or os.getenv("LOG_ANALYTICS_WORKSPACE_ID")
        self.client = None
        if LogsQueryClient and DefaultAzureCredential and self.workspace_id:
            try:
                self.client = LogsQueryClient(DefaultAzureCredential())
            except Exception as exc:  # pragma: no cover
                logging.warning(f"[LogQuerySkill] No se pudo inicializar LogsQueryClient: {exc}")

    def query_logs(self, funcion: Optional[str] = None, horas: int = 24) -> List[Dict[str, Any]]:
        """
        Ejecuta consulta contra Log Analytics filtrando por operacion/funcion.
        Retorna lista de dicts normalizados.
        """
        if not self.client or not self.workspace_id:
            raise RuntimeError("LogQuerySkill no inicializado (workspace o cliente ausente)")

        filtro_funcion = f"| where operation_Name contains '{funcion}'" if funcion else ""
        query = f"""
        traces
        | where timestamp > ago({horas}h)
        {filtro_funcion}
        | project timestamp, operation_Name, message, severityLevel
        | order by timestamp desc
        | take 200
        """
        result = self.client.query_workspace(
            self.workspace_id,
            query,
            timespan=timedelta(hours=horas),
        )
        return _resultado_a_dicts(result)


def _resultado_a_dicts(result: Any) -> List[Dict[str, Any]]:
    """Convierte LogsQueryResult a lista de dicts sencilla."""
    if not result or not getattr(result, "tables", None):
        return []
    salida: List[Dict[str, Any]] = []
    for table in result.tables:
        col_names = [c.name for c in getattr(table, "columns", [])]
        for row in getattr(table, "rows", []):
            row_dict = {col_names[i]: row[i] for i in range(len(col_names))}
            salida.append(
                {
                    "timestamp": row_dict.get("timestamp"),
                    "operation": row_dict.get("operation_Name"),
                    "message": row_dict.get("message"),
                    "severity": row_dict.get("severityLevel"),
                }
            )
    return salida


def extract_function_hint(user_text: str) -> Optional[str]:
    """Extrae un posible nombre de funcion/servicio del texto."""
    if not user_text:
        return None
    lowered = user_text.lower()
    # Heuristica simple: tomar palabra despues de "funcion", "function", "app"
    tokens = [t for t in lowered.replace(".", " ").replace("/", " ").split() if t]
    for i, tok in enumerate(tokens):
        if tok in ("funcion", "function", "functionapp", "app", "lambda"):
            if i + 1 < len(tokens):
                candidato = tokens[i + 1].strip(",:;")
                if len(candidato) > 2:
                    return candidato
    return None


def _stable_query_hash(user_query: str, funcion: Optional[str]) -> str:
    base = preprocess_text(user_query)
    payload = f"{base}|{funcion or ''}"
    return redis_buffer.stable_hash(payload)


def get_cached_analysis(user_query: str, funcion: Optional[str]) -> Optional[Dict[str, Any]]:
    """Obtiene análisis de logs cacheado."""
    if not redis_buffer.is_enabled:
        return None
    key = _stable_query_hash(user_query, funcion)
    return redis_buffer.get_cached_payload("logs_analysis", key)


def cache_log_analysis(user_query: str, funcion: Optional[str], analysis: Dict[str, Any]) -> None:
    """Cachea análisis de logs para evitar recomputar."""
    if not redis_buffer.is_enabled or not analysis:
        return
    key = _stable_query_hash(user_query, funcion)
    redis_buffer.cache_response("logs_analysis", key, analysis)


def analyze_logs_semantic(logs: List[Dict[str, Any]], funcion: Optional[str] = None) -> Dict[str, Any]:
    """Analiza lista de logs de forma semántica ligera (conteos, dedupe, ejemplos)."""
    if not logs:
        return {"exito": False, "mensaje": "No hay logs para analizar", "funcion": funcion}

    severity_counts: Dict[str, int] = {}
    errores: List[Dict[str, Any]] = []
    advertencias: List[Dict[str, Any]] = []
    dedupe_keys = set()

    for log in logs:
        sev = str(log.get("severity") or "INFO").upper()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        mensaje = str(log.get("message") or "")
        dedupe_key = redis_buffer.stable_hash(preprocess_text(mensaje))
        if dedupe_key in dedupe_keys:
            continue
        dedupe_keys.add(dedupe_key)

        resumen = {
            "timestamp": log.get("timestamp") or "",
            "operation": log.get("operation") or "",
            "severity": sev,
            "message": mensaje[:500],
        }

        if "ERROR" in sev or "WARN" in sev or "CRITICAL" in sev:
            errores.append(resumen) if "ERROR" in sev or "CRITICAL" in sev else advertencias.append(resumen)

    top_errores = errores[:5]
    top_warnings = advertencias[:5]

    resumen_texto = (
        f"{len(logs)} eventos | errores={len(errores)} | warnings={len(advertencias)} "
        f"| severidades={severity_counts}"
    )

    return {
        "exito": True,
        "mensaje": f"Analisis de logs completado ({resumen_texto})",
        "funcion": funcion,
        "conteo_severidad": severity_counts,
        "errores": top_errores,
        "advertencias": top_warnings,
        "muestras": (errores + advertencias)[:10],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
