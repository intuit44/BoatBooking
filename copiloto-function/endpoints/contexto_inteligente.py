"""
Endpoint: /api/contexto-inteligente
Devuelve contexto interpretado y filtrado usando queries dinámicas
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

@app.function_name(name="contexto_inteligente")
@app.route(route="contexto-inteligente", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def contexto_inteligente_http(req: func.HttpRequest) -> func.HttpResponse:
        """Devuelve contexto interpretado filtrado por intención"""
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
            
            mensaje = body.get("mensaje") or req.params.get("query")
            
            # Interpretar intención si hay mensaje
            if mensaje:
                params = interpretar_intencion_agente(mensaje, dict(req.headers))
            else:
                params = {
                    "session_id": session_id,
                    "tipo": body.get("tipo") or req.params.get("tipo"),
                    "contiene": body.get("contiene") or req.params.get("contiene"),
                    "limite": int(body.get("limite", req.params.get("limite", 10)))
                }
            
            query = construir_query_dinamica(**{k: v for k, v in params.items() if v is not None})
            resultados = ejecutar_query_cosmos(query, memory_service.memory_container)
            
            # Construir contexto inteligente
            contexto = {
                "resumen": "",
                "temas_principales": [],
                "endpoints_relevantes": [],
                "acciones_sugeridas": []
            }
            
            # Analizar resultados
            temas = {}
            endpoints = {}
            
            for item in resultados:
                texto = item.get("texto_semantico", "")
                endpoint = item.get("endpoint", "")
                
                # Extraer temas
                palabras_clave = ["cosmos", "diagnostico", "copiloto", "memoria", "error"]
                for palabra in palabras_clave:
                    if palabra in texto.lower():
                        temas[palabra] = temas.get(palabra, 0) + 1
                
                if endpoint:
                    endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
            
            # Generar resumen
            if temas:
                tema_principal = max(temas, key=temas.get)
                contexto["resumen"] = f"Actividad reciente centrada en {tema_principal} ({temas[tema_principal]} interacciones)"
            
            contexto["temas_principales"] = [{"tema": k, "frecuencia": v} for k, v in sorted(temas.items(), key=lambda x: x[1], reverse=True)[:3]]
            contexto["endpoints_relevantes"] = [{"endpoint": k, "usos": v} for k, v in sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            # Sugerir acciones
            if "error" in temas:
                contexto["acciones_sugeridas"].append("Revisar errores recientes con diagnostico:completo")
            if "copiloto" in temas:
                contexto["acciones_sugeridas"].append("Continuar interacción con copiloto")
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "contexto": contexto,
                    "total_interacciones": len(resultados),
                    "interpretacion": "automática" if mensaje else "explícita",
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )
            
        except Exception as e:
            logging.error(f"❌ Error en contexto-inteligente: {e}")
            return func.HttpResponse(
                json.dumps({"exito": False, "error": str(e)}),
                mimetype="application/json", status_code=500
            )
