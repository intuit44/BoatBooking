"""
Endpoint: /api/memoria-global
Deduplicación y resumen sobre interacciones de múltiples sesiones
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

@app.function_name(name="memoria_global")
@app.route(route="memoria-global", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def memoria_global_http(req: func.HttpRequest) -> func.HttpResponse:
        """Consulta memoria global con deduplicación"""
        try:
            try:
                body = req.get_json()
            except:
                body = {}
            
            # Parámetros para consulta global (sin session_id específico)
            params = {
                "session_id": body.get("session_id") or req.params.get("session_id") or "assistant",  # Fallback a session común
                "tipo": body.get("tipo") or req.params.get("tipo"),
                "contiene": body.get("contiene") or req.params.get("contiene"),
                "fecha_inicio": body.get("fecha_inicio") or req.params.get("fecha_inicio", "últimas 24h"),
                "limite": int(body.get("limite", req.params.get("limite", 50)))
            }
            
            query = construir_query_dinamica(**{k: v for k, v in params.items() if v is not None})
            resultados = ejecutar_query_cosmos(query, memory_service.memory_container)
            
            # Deduplicación por texto_semantico similar
            vistos = set()
            deduplicados = []
            
            for item in resultados:
                texto = item.get("texto_semantico", "")
                # Usar primeros 100 caracteres como clave de deduplicación
                clave = texto[:100].strip().lower()
                
                if clave and clave not in vistos:
                    vistos.add(clave)
                    deduplicados.append(item)
            
            # Agrupar por sesión
            por_sesion = {}
            for item in deduplicados:
                sid = item.get("session_id", "unknown")
                if sid not in por_sesion:
                    por_sesion[sid] = []
                por_sesion[sid].append(item)
            
            # Generar resumen global
            resumen = {
                "total_interacciones": len(resultados),
                "interacciones_unicas": len(deduplicados),
                "sesiones_activas": len(por_sesion),
                "tasa_deduplicacion": f"{((len(resultados) - len(deduplicados)) / len(resultados) * 100):.1f}%" if resultados else "0%"
            }
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "resumen": resumen,
                    "interacciones": deduplicados[:20],  # Primeras 20
                    "por_sesion": {k: len(v) for k, v in por_sesion.items()},
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json", status_code=200
            )
            
        except Exception as e:
            logging.error(f"❌ Error en memoria-global: {e}")
            return func.HttpResponse(
                json.dumps({"exito": False, "error": str(e)}),
                mimetype="application/json", status_code=500
            )
