"""
Endpoint: /api/sugerencias
Genera sugerencias basadas en interacciones previas usando queries dinámicas
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
from semantic_query_builder import construir_query_dinamica, interpretar_intencion_agente, ejecutar_query_cosmos
from services.memory_service import memory_service

@app.function_name(name="sugerencias")
@app.route(route="sugerencias", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def sugerencias_http(req: func.HttpRequest) -> func.HttpResponse:
        """Genera sugerencias basadas en historial de interacciones"""
        try:
            session_id = req.headers.get("Session-ID") or req.params.get("session_id")
            
            if not session_id:
                return func.HttpResponse(
                    json.dumps({"exito": False, "error": "Session-ID requerido"}),
                    mimetype="application/json", status_code=400
                )
            
            # Obtener últimas 20 interacciones exitosas
            params = {
                "session_id": session_id,
                "exito": True,
                "fecha_inicio": "últimas 24h",
                "limite": 20
            }
            
            query = construir_query_dinamica(**params)
            resultados = ejecutar_query_cosmos(query, memory_service.memory_container)
            
            # Analizar patrones y generar sugerencias
            sugerencias = []
            endpoints_usados = set()
            acciones_frecuentes = {}
            
            for item in resultados:
                endpoint = item.get("endpoint", "")
                if endpoint:
                    endpoints_usados.add(endpoint)
                
                texto = item.get("texto_semantico", "")
                if "copiloto" in texto.lower():
                    acciones_frecuentes["copiloto"] = acciones_frecuentes.get("copiloto", 0) + 1
                if "diagnostico" in texto.lower():
                    acciones_frecuentes["diagnostico"] = acciones_frecuentes.get("diagnostico", 0) + 1
            
            # Generar sugerencias basadas en patrones
            if "copiloto" in acciones_frecuentes:
                sugerencias.append({
                    "tipo": "accion",
                    "texto": "Continuar explorando con el copiloto",
                    "comando": "/api/copiloto",
                    "relevancia": acciones_frecuentes["copiloto"] / len(resultados)
                })
            
            if "diagnostico" in acciones_frecuentes:
                sugerencias.append({
                    "tipo": "accion",
                    "texto": "Ejecutar diagnóstico completo",
                    "comando": "diagnosticar:completo",
                    "relevancia": acciones_frecuentes["diagnostico"] / len(resultados)
                })
            
            # Sugerencias por endpoints no usados recientemente
            todos_endpoints = {"/api/copiloto", "/api/diagnostico-recursos", "/api/leer-archivo"}
            no_usados = todos_endpoints - endpoints_usados
            
            for endpoint in no_usados:
                sugerencias.append({
                    "tipo": "exploracion",
                    "texto": f"Explorar {endpoint}",
                    "comando": endpoint,
                    "relevancia": 0.3
                })
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "sugerencias": sorted(sugerencias, key=lambda x: x["relevancia"], reverse=True)[:5],
                    "analisis": {
                        "total_interacciones": len(resultados),
                        "endpoints_usados": list(endpoints_usados),
                        "acciones_frecuentes": acciones_frecuentes
                    },
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )
            
        except Exception as e:
            logging.error(f"❌ Error en sugerencias: {e}")
            return func.HttpResponse(
                json.dumps({"exito": False, "error": str(e)}),
                mimetype="application/json", status_code=500
            )
