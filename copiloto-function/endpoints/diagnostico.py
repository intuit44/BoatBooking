"""
Endpoint: /api/diagnostico
Analiza qué ocurrió en determinada sesión usando queries dinámicas
"""
import logging
import json
import os
import sys
from datetime import datetime
import azure.functions as func

# Importar el app principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from function_app import app
from semantic_query_builder import construir_query_dinamica, ejecutar_query_cosmos
from services.memory_service import memory_service

@app.function_name(name="diagnostico")
@app.route(route="diagnostico", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def diagnostico_http(req: func.HttpRequest) -> func.HttpResponse:
        """Diagnóstico de sesión con análisis de errores y patrones"""
        try:
            session_id = req.headers.get("Session-ID") or req.params.get("session_id")
            
            if not session_id:
                return func.HttpResponse(
                    json.dumps({"exito": False, "error": "Session-ID requerido"}),
                    mimetype="application/json", status_code=400
                )
            
            try:
                body = req.get_json()
            except:
                body = {}
            
            # Consultar todas las interacciones de la sesión
            params = {
                "session_id": session_id,
                "fecha_inicio": body.get("fecha_inicio") or req.params.get("fecha_inicio", "últimas 24h"),
                "limite": 100
            }
            
            query = construir_query_dinamica(**params)
            resultados = ejecutar_query_cosmos(query, memory_service.memory_container)
            
            # Análisis de diagnóstico
            diagnostico = {
                "total_interacciones": len(resultados),
                "exitosas": 0,
                "fallidas": 0,
                "endpoints_usados": {},
                "errores_detectados": [],
                "patrones": []
            }
            
            for item in resultados:
                exito = item.get("exito", True)
                endpoint = item.get("endpoint", "unknown")
                texto = item.get("texto_semantico", "")
                
                if exito:
                    diagnostico["exitosas"] += 1
                else:
                    diagnostico["fallidas"] += 1
                    diagnostico["errores_detectados"].append({
                        "endpoint": endpoint,
                        "timestamp": item.get("timestamp"),
                        "texto": texto[:100]
                    })
                
                diagnostico["endpoints_usados"][endpoint] = diagnostico["endpoints_usados"].get(endpoint, 0) + 1
            
            # Detectar patrones
            if diagnostico["fallidas"] > diagnostico["exitosas"]:
                diagnostico["patrones"].append("Alta tasa de errores detectada")
            
            if diagnostico["endpoints_usados"].get("historial-interacciones", 0) > 10:
                diagnostico["patrones"].append("Consultas frecuentes al historial (posible recursión)")
            
            # Calcular métricas
            tasa_exito = (diagnostico["exitosas"] / diagnostico["total_interacciones"] * 100) if diagnostico["total_interacciones"] > 0 else 0
            
            diagnostico["metricas"] = {
                "tasa_exito": f"{tasa_exito:.1f}%",
                "tasa_error": f"{(100 - tasa_exito):.1f}%",
                "endpoint_mas_usado": max(diagnostico["endpoints_usados"], key=diagnostico["endpoints_usados"].get) if diagnostico["endpoints_usados"] else "N/A"
            }
            
            # Recomendaciones
            recomendaciones = []
            if tasa_exito < 50:
                recomendaciones.append("Revisar configuración - tasa de éxito baja")
            if len(diagnostico["errores_detectados"]) > 5:
                recomendaciones.append("Múltiples errores detectados - revisar logs")
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "diagnostico": diagnostico,
                    "recomendaciones": recomendaciones,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )
            
        except Exception as e:
            logging.error(f"❌ Error en diagnostico: {e}")
            return func.HttpResponse(
                json.dumps({"exito": False, "error": str(e)}),
                mimetype="application/json", status_code=500
            )
