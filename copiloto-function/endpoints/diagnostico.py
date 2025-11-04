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
from memory_decorator import registrar_memoria

@app.function_name(name="diagnostico")
@app.route(route="diagnostico", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
@registrar_memoria("diagnostico")
def diagnostico_http(req: func.HttpRequest) -> func.HttpResponse:
        """Diagnóstico de sesión con análisis de errores y patrones"""
        try:
            # Extraer session_id de múltiples fuentes
            session_id = (
                req.headers.get("Session-ID") or
                req.headers.get("X-Session-ID") or
                req.params.get("session_id") or
                req.params.get("Session-ID")
            )
            
            # Si no hay session_id, retornar info del servicio disponible
            if not session_id:
                return func.HttpResponse(
                    json.dumps({
                        "ok": True,
                        "message": "Servicio de diagnósticos disponible",
                        "mgmt_sdk_available": True,
                        "endpoints": {
                            "POST": "Configurar diagnósticos para un recurso"
                        },
                        "uso": "Enviar Session-ID en headers o params para diagnóstico de sesión",
                        "ejemplo": "GET /api/diagnostico?session_id=tu-session-id"
                    }, ensure_ascii=False),
                    mimetype="application/json", status_code=200
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
            
            # 🧠 Generar respuesta_usuario para memoria semántica
            respuesta_usuario = f"""DIAGNÓSTICO DE SESIÓN {session_id[:8]}...

📊 Resumen:
- Total interacciones: {diagnostico['total_interacciones']}
- Exitosas: {diagnostico['exitosas']} ({tasa_exito:.1f}%)
- Fallidas: {diagnostico['fallidas']} ({(100-tasa_exito):.1f}%)
- Endpoint más usado: {diagnostico['metricas']['endpoint_mas_usado']}

{f'⚠️ Patrones detectados: ' + ', '.join(diagnostico['patrones']) if diagnostico['patrones'] else '✅ Sin patrones anómalos'}

{f'💡 Recomendaciones: ' + ', '.join(recomendaciones) if recomendaciones else '✅ Sistema funcionando correctamente'}
"""
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "diagnostico": diagnostico,
                    "recomendaciones": recomendaciones,
                    "respuesta_usuario": respuesta_usuario,
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
