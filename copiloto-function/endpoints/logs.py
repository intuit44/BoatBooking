"""
Endpoint: /api/logs
Expone logs estructurados del backend para análisis del agente
"""
from function_app import app
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import azure.functions as func

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@app.function_name(name="logs")
@app.route(route="logs", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def logs_http(req: func.HttpRequest) -> func.HttpResponse:
    """Lee y estructura logs del backend"""
    try:
        # Parámetros
        nivel = req.params.get("nivel", "").upper()  # ERROR, WARNING, INFO
        limite = int(req.params.get("limite", "100"))
        horas = int(req.params.get("horas", "24"))
        endpoint = req.params.get("endpoint", "")

        logs_estructurados = []

        # 1. LOGS EN TIEMPO REAL (Python logging)
        root_logger = logging.getLogger()
        logs_estructurados.append({
            "nivel": "INFO",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/api/logs",
            "mensaje": f"Sistema activo. Nivel logging: {logging.getLevelName(root_logger.level)}",
            "es_error": False,
            "fuente": "python_logging"
        })

        # 2. LOGS DE COSMOS (Historial de errores)
        try:
            from services.memory_service import memory_service
            historial = memory_service.get_session_history(
                "global", limit=limite)

            for item in historial:
                texto = item.get("texto_semantico", "")
                exito = item.get("exito", True)
                success = item.get("data", {}).get("success", True)
                
                # Agregar TODOS los logs si no hay filtro
                if not nivel:
                    logs_estructurados.append({
                        "nivel": "INFO",
                        "timestamp": item.get("timestamp"),
                        "endpoint": item.get("data", {}).get("endpoint", "unknown"),
                        "mensaje": texto[:200],
                        "es_error": False,
                        "fuente": "cosmos_db"
                    })
                # Detectar errores
                elif not exito or not success or "error" in texto.lower() or "failed" in texto.lower():
                    logs_estructurados.append({
                        "nivel": "ERROR",
                        "timestamp": item.get("timestamp"),
                        "endpoint": item.get("data", {}).get("endpoint", "unknown"),
                        "mensaje": texto[:500],
                        "es_error": True,
                        "fuente": "cosmos_db"
                    })
                elif "warning" in texto.lower():
                    logs_estructurados.append({
                        "nivel": "WARNING",
                        "timestamp": item.get("timestamp"),
                        "endpoint": item.get("data", {}).get("endpoint", "unknown"),
                        "mensaje": texto[:500],
                        "es_error": False,
                        "fuente": "cosmos_db"
                    })
        except Exception as e:
            logging.warning(f"No se pudo consultar Cosmos: {e}")

        # 3. LOGS DE APPLICATION INSIGHTS (via Azure CLI)
        try:
            import subprocess
            app_name = os.getenv("WEBSITE_SITE_NAME",
                                 "copiloto-semantico-func-us2")

            # Consultar últimos logs de App Insights
            cmd = f'az monitor app-insights query --app {app_name} --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc | take 10" --output json'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5)

            if result.returncode == 0 and result.stdout:
                ai_data = json.loads(result.stdout)
                for row in ai_data.get("tables", [{}])[0].get("rows", []):
                    logs_estructurados.append({
                        "nivel": row[2] if len(row) > 2 else "INFO",
                        "timestamp": row[0] if len(row) > 0 else datetime.utcnow().isoformat(),
                        "endpoint": "app_insights",
                        "mensaje": row[1] if len(row) > 1 else "",
                        "es_error": "error" in str(row).lower(),
                        "fuente": "application_insights"
                    })
        except Exception as e:
            logging.debug(f"Application Insights no disponible: {e}")

        # Análisis semántico
        analisis = analizar_logs(logs_estructurados)

        # Generar respuesta para el agente
        respuesta_usuario = generar_resumen_logs(logs_estructurados, analisis)

        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "logs": logs_estructurados[-limite:],
                "total": len(logs_estructurados),
                "analisis": analisis,
                "respuesta_usuario": respuesta_usuario,
                "metadata": {
                    "fuentes": {
                        "python_logging": "Logs en tiempo real del sistema",
                        "cosmos_db": "Historial de errores guardados",
                        "application_insights": "Logs de Azure (si disponible)"
                    },
                    "filtros": {
                        "nivel": nivel or "todos",
                        "horas": horas,
                        "endpoint": endpoint or "todos"
                    }
                }
            }, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error en /api/logs: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


def parse_log_line(line):
    """Parsea una línea de log en estructura"""
    try:
        # Detectar nivel
        nivel = "INFO"
        if "ERROR" in line:
            nivel = "ERROR"
        elif "WARNING" in line:
            nivel = "WARNING"
        elif "DEBUG" in line:
            nivel = "DEBUG"

        # Detectar timestamp (formato común: [2025-01-10 10:30:45])
        import re
        timestamp_match = re.search(
            r'\[(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None

        # Detectar endpoint
        endpoint_match = re.search(r'(/api/[\w-]+)', line)
        endpoint = endpoint_match.group(1) if endpoint_match else None

        return {
            "nivel": nivel,
            "timestamp": timestamp,
            "endpoint": endpoint,
            "mensaje": line[:500],  # Limitar longitud
            "es_error": nivel == "ERROR"
        }
    except Exception:
        return None


def analizar_logs(logs):
    """Análisis semántico de logs"""
    analisis = {
        "total": len(logs),
        "por_nivel": {},
        "errores_frecuentes": [],
        "endpoints_problematicos": {},
        "patrones": []
    }

    # Contar por nivel
    for log in logs:
        nivel = log.get("nivel", "INFO")
        analisis["por_nivel"][nivel] = analisis["por_nivel"].get(nivel, 0) + 1

    # Detectar endpoints con errores
    for log in logs:
        if log.get("es_error") and log.get("endpoint"):
            ep = log["endpoint"]
            analisis["endpoints_problematicos"][ep] = analisis["endpoints_problematicos"].get(
                ep, 0) + 1

    # Detectar patrones
    if analisis["por_nivel"].get("ERROR", 0) > 5:
        analisis["patrones"].append("Alta tasa de errores detectada")

    if len(analisis["endpoints_problematicos"]) > 0:
        analisis["patrones"].append(
            f"{len(analisis['endpoints_problematicos'])} endpoints con errores")

    return analisis


def generar_resumen_logs(logs, analisis):
    """Genera resumen en lenguaje natural para el agente"""
    total = analisis["total"]
    errores = analisis["por_nivel"].get("ERROR", 0)
    warnings = analisis["por_nivel"].get("WARNING", 0)

    resumen = f"Analicé {total} entradas de log. "

    if errores > 0:
        resumen += f"Encontré {errores} errores. "

        if analisis["endpoints_problematicos"]:
            top_problema = max(
                analisis["endpoints_problematicos"].items(), key=lambda x: x[1])
            resumen += f"El endpoint más problemático es {top_problema[0]} con {top_problema[1]} errores. "
    else:
        resumen += "No hay errores recientes. "

    if warnings > 0:
        resumen += f"Hay {warnings} advertencias. "

    if analisis["patrones"]:
        resumen += f"Patrones detectados: {', '.join(analisis['patrones'])}."

    return resumen
