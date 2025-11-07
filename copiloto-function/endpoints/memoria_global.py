"""
Endpoint: /api/memoria-global
Deduplicación y resumen sobre interacciones de múltiples sesiones
"""
from services.memory_service import memory_service
from semantic_query_builder import construir_query_dinamica, ejecutar_query_cosmos
from function_app import app
import logging
import json
import os
import sys
from datetime import datetime
import azure.functions as func

# Importar el app principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


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
            # Fallback a session común
            "session_id": body.get("session_id") or req.params.get("session_id") or "assistant",
            "tipo": body.get("tipo") or req.params.get("tipo"),
            "contiene": body.get("contiene") or req.params.get("contiene"),
            "fecha_inicio": body.get("fecha_inicio") or req.params.get("fecha_inicio", "últimas 24h"),
            "limite": int(body.get("limite", req.params.get("limite", 50)))
        }

        query = construir_query_dinamica(
            **{k: v for k, v in params.items() if v is not None})
        resultados = ejecutar_query_cosmos(
            query, memory_service.memory_container)

        # Deduplicación por hash completo (solo duplicados exactos)
        import hashlib
        vistos = set()
        deduplicados = []

        for item in resultados:
            texto = item.get("texto_semantico", "")
            # Hash completo: solo elimina duplicados 100% idénticos
            clave = hashlib.sha256(texto.strip().lower().encode('utf-8')).hexdigest()

            if clave and clave not in vistos:
                vistos.add(clave)
                deduplicados.append(item)
            else:
                logging.debug(f"[DUPLICADO EXACTO] {texto[:80]}...")

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

        # Devolver texto_semantico REAL sin resúmenes artificiales
        top_interacciones = deduplicados[:params['limite']]

        # Filtrar basura inteligente: solo si es corto Y contiene patrón
        patrones_basura = [
            "resumen de la ultima actividad",
            "consulta de historial completada",
            "ultimo tema:",
            "sin resumen de conversacion"
        ]
        
        textos_reales = []
        for item in top_interacciones:
            texto = item.get('texto_semantico', '').strip()
            if not texto or len(texto) < 50:
                continue
            
            # Solo descartar si es corto (<100) Y contiene patrón basura
            es_basura = any(p in texto.lower() for p in patrones_basura) and len(texto) < 100
            
            if not es_basura:
                textos_reales.append(texto)
            else:
                logging.debug(f"[FILTRADO BASURA] {texto[:80]}... (len={len(texto)})")

        respuesta_sintetizada = "\n\n---\n\n".join(
            textos_reales) if textos_reales else "No hay interacciones con contenido semántico disponible."

        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "resumen": resumen,
                "respuesta_usuario": respuesta_sintetizada,
                "interacciones": top_interacciones,
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
