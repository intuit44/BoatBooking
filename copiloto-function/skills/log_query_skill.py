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
        self.workspace_id = workspace_id or os.getenv(
            "LOG_ANALYTICS_WORKSPACE_ID")
        self.client = None
        if LogsQueryClient and DefaultAzureCredential and self.workspace_id:
            try:
                self.client = LogsQueryClient(DefaultAzureCredential())
            except Exception as exc:  # pragma: no cover
                logging.warning(
                    f"[LogQuerySkill] No se pudo inicializar LogsQueryClient: {exc}")

    def query_logs(
        self,
        funcion: Optional[str] = None,
        horas: int = 24,
        *,
        dynamic_query: Optional[str] = None,
        model_spec: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta consulta contra Log Analytics.

        Comportamiento:
        - Si `dynamic_query` es provista (string Kusto), la ejecuta tal cual después de una
          validación mínima (se asegura filtro de tiempo y un `take`).
          Esto permite que un agente externo (p.ej. Foundry) arme la query dinámica.
        - Si no, intenta construir la query a partir de `model_spec` (estructura dict) de forma
          segura evitando concatenación sin escape.
        - Si tampoco hay `model_spec`, usa una consulta generada por parámetros (`funcion`, `horas`).

        Parámetros:
        - funcion: nombre a filtrar en OperationName (opcional).
        - horas: ventana temporal en horas.
        - dynamic_query: query Kusto completa provista por el modelo/agent.
        - model_spec: dict con posibles keys: table, extra_filters (list de strings),
                      project (list de columnas), order_by (str), take (int).

        Retorna lista de dicts normalizados.
        """
        if not self.client or not self.workspace_id:
            raise RuntimeError(
                "LogQuerySkill no inicializado (workspace o cliente ausente)")

        def _esc_literal(val: Any) -> str:
            # Escape básico para literales Kusto (duplica comillas simples)
            return str(val).replace("'", "''")

        def _ensure_time_and_limits(q: str, horas_local: int, default_take: int = 200) -> str:
            # Si no hay filtro de TimeGenerated, aplicarlo al inicio
            if "timegenerated" not in q.lower():
                time_filter = f"| where TimeGenerated > ago({horas_local}h)"
                q = f"{time_filter}\n{q}"
            # Asegurar que hay un take y un project razonable
            if "take " not in q.lower():
                q = (q.rstrip() + f"\n| take {default_take}")
            return q

        # 1) Ejecutar dynamic_query proporcionada por el agente/modelo (preferible)
        if dynamic_query:
            # Validación mínima: evitar múltiples comandos separados por ';' y asegurar límites
            if ";" in dynamic_query:
                raise ValueError("dynamic_query contiene ';' inválido")
            safe_query = _ensure_time_and_limits(dynamic_query, horas)
            result = self.client.query_workspace(
                self.workspace_id,
                safe_query,
                timespan=timedelta(hours=horas),
            )
            return _resultado_a_dicts(result)

        # 2) Construir desde model_spec de forma controlada
        if model_spec:
            table = model_spec.get("table", "AppTraces")
            extra_filters = model_spec.get("extra_filters", []) or []
            project_cols = model_spec.get(
                "project", ["TimeGenerated", "OperationName", "Message", "SeverityLevel"])
            order_by = model_spec.get("order_by", "TimeGenerated desc")
            take_n = int(model_spec.get("take", 200))
            # sanitizar take
            take_n = max(1, min(take_n, 1000))

            filters: List[str] = [f"TimeGenerated > ago({horas}h)"]
            if funcion:
                filters.append(
                    f"OperationName contains '{_esc_literal(funcion)}'")
            for f in extra_filters:
                # permitir filtros ya formateados por el agente, pero evitar ';'
                if ";" in str(f):
                    continue
                filters.append(str(f).strip())

            # leading '| ' in each filter line
            filters_block = "\n| ".join([""] + [f for f in filters])
            proj_block = ", ".join(project_cols)
            query = f"""
            {table}
            {filters_block}
            | project {proj_block}
            | order by {order_by}
            | take {take_n}
            """
            result = self.client.query_workspace(
                self.workspace_id,
                query,
                timespan=timedelta(hours=horas),
            )
            return _resultado_a_dicts(result)

        # 3) Fallback: construir query segura a partir de funcion/horas (sin hardcodear literalmente)
        filtro_funcion = f"| where OperationName contains '{_esc_literal(funcion)}'" if funcion else ""
        query = f"""
        AppTraces
        | where TimeGenerated > ago({horas}h)
        {filtro_funcion}
        | project TimeGenerated, OperationName, Message, SeverityLevel
        | order by TimeGenerated desc
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
        cols = getattr(table, "columns", []) or []
        # Manejar columnas que pueden ser objetos con .name o simples strings
        col_names: List[str] = []
        for c in cols:
            if hasattr(c, "name"):
                col_names.append(c.name)
            else:
                col_names.append(str(c))

        for row in getattr(table, "rows", []):
            # proteger contra discrepancias de longitud entre columnas y fila
            length = min(len(col_names), len(row))
            row_dict = {col_names[i]: row[i] for i in range(length)}

            # helper para obtener campo de forma resiliente (case-insensitive y variantes de nombre)
            def _get_field(d: Dict[str, Any], *candidates: str) -> Optional[Any]:
                for cand in candidates:
                    if cand in d:
                        return d[cand]
                # case-insensitive fallback
                lowers = {k.lower(): k for k in d.keys()}
                for cand in candidates:
                    lk = cand.lower()
                    if lk in lowers:
                        return d[lowers[lk]]
                return None

            timestamp = _get_field(
                row_dict, "TimeGenerated", "timestamp", "timegenerated") or ""
            operation = _get_field(
                row_dict, "OperationName", "operation", "operation_Name") or ""
            message = _get_field(row_dict, "Message", "message") or ""
            severity = _get_field(row_dict, "SeverityLevel",
                                  "severityLevel", "severity") or ""

            salida.append(
                {
                    "timestamp": timestamp,
                    "operation": operation,
                    "message": message,
                    "severity": severity,
                }
            )
    return salida


def extract_function_hint(user_text: str) -> Optional[str]:
    """Extrae un posible nombre de funcion/servicio del texto."""
    if not user_text:
        return None
    lowered = user_text.lower()
    # Heuristica simple: tomar palabra despues de "funcion", "function", "app"
    tokens = [t for t in lowered.replace(
        ".", " ").replace("/", " ").split() if t]
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
            errores.append(
                resumen) if "ERROR" in sev or "CRITICAL" in sev else advertencias.append(resumen)

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
