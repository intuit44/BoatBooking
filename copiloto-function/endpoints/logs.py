"""
Endpoint: /api/logs
Expone logs estructurados del backend para análisis del agente
"""
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import azure.functions as func

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from function_app import app

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
        
        # Buscar archivos de log
        log_dir = Path(__file__).parent.parent
        log_files = list(log_dir.glob("*.log"))
        
        if not log_files:
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "logs": [],
                    "mensaje": "No hay archivos de log disponibles",
                    "respuesta_usuario": "No encontré archivos de log en el sistema."
                }),
                mimetype="application/json"
            )
        
        # Leer logs más reciente
        log_file = max(log_files, key=lambda f: f.stat().st_mtime)
        
        logs_estructurados = []
        cutoff_time = datetime.now() - timedelta(hours=horas)
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Filtrar por nivel si se especifica
                if nivel and nivel not in line:
                    continue
                
                # Filtrar por endpoint si se especifica
                if endpoint and endpoint not in line:
                    continue
                
                # Parsear línea de log
                log_entry = parse_log_line(line)
                if log_entry:
                    logs_estructurados.append(log_entry)
                
                if len(logs_estructurados) >= limite:
                    break
        
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
                    "archivo": log_file.name,
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
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
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
            analisis["endpoints_problematicos"][ep] = analisis["endpoints_problematicos"].get(ep, 0) + 1
    
    # Detectar patrones
    if analisis["por_nivel"].get("ERROR", 0) > 5:
        analisis["patrones"].append("Alta tasa de errores detectada")
    
    if len(analisis["endpoints_problematicos"]) > 0:
        analisis["patrones"].append(f"{len(analisis['endpoints_problematicos'])} endpoints con errores")
    
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
            top_problema = max(analisis["endpoints_problematicos"].items(), key=lambda x: x[1])
            resumen += f"El endpoint más problemático es {top_problema[0]} con {top_problema[1]} errores. "
    else:
        resumen += "No hay errores recientes. "
    
    if warnings > 0:
        resumen += f"Hay {warnings} advertencias. "
    
    if analisis["patrones"]:
        resumen += f"Patrones detectados: {', '.join(analisis['patrones'])}."
    
    return resumen
