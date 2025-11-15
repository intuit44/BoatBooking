"""
Endpoint: /api/memoria-global
Deduplicación y resumen sobre interacciones de múltiples sesiones
"""
from services.memory_service import memory_service
from semantic_query_builder import construir_query_dinamica, ejecutar_query_cosmos
from function_app import app
from utils_helpers import build_event, build_structured_payload
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

        # 1. Consultar Cosmos DB (cronológico)
        query = construir_query_dinamica(
            **{k: v for k, v in params.items() if v is not None})
        resultados = ejecutar_query_cosmos(
            query, memory_service.memory_container)

        # 2. Consultar AI Search (vectorial semántico)
        docs_vectoriales = []
        try:
            from endpoints_search_memory import buscar_memoria_endpoint
            query_busqueda = body.get("query") or body.get(
                "contiene") or "actividad reciente"
            resultado_vectorial = buscar_memoria_endpoint({
                "query": query_busqueda,
                "top": 20,
                "session_id": params["session_id"]
            })
            if resultado_vectorial.get("exito"):
                docs_vectoriales = resultado_vectorial.get("documentos", [])
                # Limpiar emojis de documentos vectoriales
                import re
                for doc in docs_vectoriales:
                    if "texto_semantico" in doc:
                        texto = doc["texto_semantico"]
                        texto_limpio = re.sub(
                            r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto)
                        texto_limpio = texto_limpio.replace(
                            "endpoint", "consulta").replace("**", "").strip()
                        doc["texto_semantico"] = texto_limpio
                logging.info(
                    f"🔍 AI Search: {len(docs_vectoriales)} docs vectoriales")
        except Exception as e:
            logging.warning(f"⚠️ Error en búsqueda vectorial: {e}")

        # Deduplicación por hash completo (solo duplicados exactos)
        import hashlib
        import re
        vistos = set()
        deduplicados = []

        for item in resultados:
            texto = item.get("texto_semantico", "")
            # Hash completo: solo elimina duplicados 100% idénticos
            clave = hashlib.sha256(
                texto.strip().lower().encode('utf-8')).hexdigest()

            if clave and clave not in vistos:
                vistos.add(clave)
                # Limpiar emojis y referencias técnicas del texto
                texto_limpio = re.sub(
                    r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto)
                texto_limpio = texto_limpio.replace(
                    "endpoint", "consulta").replace("**", "").strip()

                # 🔥 FILTRADO MEJORADO: Eventos pobres + clasificación
                if len(texto_limpio) < 40:
                    logging.debug(
                        f"[FILTRADO] Texto muy corto: {texto_limpio[:50]}...")
                    continue

                if texto_limpio.startswith(("Evento", "Consulta procesada", "Interaccion procesada", "Registro de")):
                    logging.debug(
                        f"[FILTRADO] Evento genérico: {texto_limpio[:50]}...")
                    continue

                # 🔥 ENRIQUECER CON CATEGORÍA Y RESULTADO
                if "tipo_error" in item:
                    item["categoria"] = item.get("categoria", "error")
                    item["resultado"] = "fallido"
                elif item.get("es_repetido"):
                    item["categoria"] = "repetitivo"
                    item["resultado"] = "exitoso" if item.get(
                        "exito", True) else "fallido"
                else:
                    item["categoria"] = item.get("categoria", "normal")
                    item["resultado"] = "exitoso" if item.get(
                        "exito", True) else "fallido"

                item["texto_semantico"] = texto_limpio
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

        top_interacciones = deduplicados[:params['limite']]
        eventos: list = []

        for item in top_interacciones:
            texto = item.get("texto_semantico") or ""
            eventos.append(
                build_event(
                    endpoint=item.get("endpoint", "memoria-global"),
                    descripcion=texto,
                    estado="exito" if item.get("exito", True) else "error",
                    sugerencia="",
                    criticidad="informativa",
                    datos={
                        "timestamp": item.get("timestamp"),
                        "session_id": item.get("session_id", params["session_id"]),
                        "tipo": item.get("tipo", "interaccion_usuario")
                    },
                    timestamp=item.get("timestamp")
                )
            )

        for doc in docs_vectoriales[:5]:
            descripcion = doc.get("texto_semantico") or doc.get("texto") or ""
            if not descripcion:
                continue
            eventos.append(
                build_event(
                    endpoint=doc.get("endpoint", "memoria-global-vectorial"),
                    descripcion=descripcion,
                    estado="informativo",
                    sugerencia="",
                    criticidad="informativa",
                    datos={
                        "id": doc.get("id"),
                        "score": doc.get("score")
                    },
                    timestamp=doc.get("timestamp")
                )
            )

        if not eventos:
            eventos.append(
                build_event(
                    endpoint="memoria-global",
                    descripcion="No se encontraron interacciones únicas para esta consulta.",
                    estado="informativo",
                    sugerencia="",
                    criticidad="informativa"
                )
            )

        extras = {
            "resumen_global": resumen,
            "interacciones": top_interacciones,
            "por_sesion": {k: len(v) for k, v in por_sesion.items()},
            "docs_vectoriales": len(docs_vectoriales),
            "docs_cosmos": len(top_interacciones),
            "timestamp": datetime.now().isoformat()
        }

        contexto_inteligente = {
            "tiene_memoria": bool(deduplicados),
            "total_interacciones": resumen.get("total_interacciones", 0),
            "resumen": f"Sesiones activas: {len(por_sesion)}. Interacciones únicas: {len(deduplicados)}.",
            "fuente_datos": "Cosmos+AISearch"
        }

        payload = build_structured_payload(
            "memoria-global",
            eventos,
            narrativa_base="",
            resumen_automatico="",
            extras=extras,
            contexto_inteligente=contexto_inteligente,
            exito=True
        )
        payload["respuesta_usuario"] = ""
        payload["mensaje"] = ""

        return func.HttpResponse(
            json.dumps(payload, ensure_ascii=False),
            mimetype="application/json", status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error en memoria-global: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )
