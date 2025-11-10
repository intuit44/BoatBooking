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
                        texto_limpio = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto)
                        texto_limpio = texto_limpio.replace("endpoint", "consulta").replace("**", "").strip()
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
                texto_limpio = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto)
                texto_limpio = texto_limpio.replace("endpoint", "consulta").replace("**", "").strip()
                
                # 🔥 FILTRADO MEJORADO: Eventos pobres + clasificación
                if len(texto_limpio) < 40:
                    logging.debug(f"[FILTRADO] Texto muy corto: {texto_limpio[:50]}...")
                    continue
                
                if texto_limpio.startswith(("Evento", "Consulta procesada", "Interaccion procesada", "Registro de")):
                    logging.debug(f"[FILTRADO] Evento genérico: {texto_limpio[:50]}...")
                    continue
                
                # 🔥 ENRIQUECER CON CATEGORÍA Y RESULTADO
                if "tipo_error" in item:
                    item["categoria"] = item.get("categoria", "error")
                    item["resultado"] = "fallido"
                elif "es_repetido" in item and item["es_repetido"]:
                    item["categoria"] = "repetitivo"
                else:
                    item["categoria"] = item.get("categoria", "normal")
                    item["resultado"] = "exitoso" if item.get("exito", True) else "fallido"
                
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

        # 3. Usar sintetizar() solo para poblar respuesta_usuario (mantener resumen y por_sesion propios)
        top_interacciones = deduplicados[:params['limite']]
        sintetizador_usado = False
        respuesta_usuario = "No hay interacciones disponibles."

        try:
            # Importar sintetizar desde el módulo dedicado
            from function_app import sintetizar

            # Sintetizar combinando vectorial + cronológico
            respuesta_sintetizada = sintetizar(
                docs_search=docs_vectoriales,
                docs_cosmos=top_interacciones,
                max_items=7,
                max_chars_per_item=1200
            )
            respuesta_usuario = respuesta_sintetizada
            sintetizador_usado = True
            logging.info(
                f"✅ Sintetizado: {len(docs_vectoriales)} vectoriales + {len(top_interacciones)} cosmos")
        except Exception as e:
            logging.warning(f"⚠️ Error en sintetizar, usando fallback: {e}")
            # Fallback mejorado (misma data, solo formato humano)
            items = []
            for item in top_interacciones:
                t = (item.get('texto_semantico') or '').strip()
                # Requerir mínimo razonable para mostrar como "clave"
                if t and len(t) >= 40:
                    primera = t.splitlines()[0][:260]  # primera línea/idea
                    items.append(primera)

            # Títulos resumidos de documentos vectoriales (si existen)
            vec_titulos = []
            for d in docs_vectoriales:
                # Intentar extraer un título/encabezado representativo
                title = d.get('title') or d.get('titulo') or d.get('nombre') or d.get('texto') or ''
                if title:
                    vec_titulos.append(title.splitlines()[0][:140])

            if items or vec_titulos:
                cabecera = (f"🧠 Memoria global: {len(top_interacciones)} interacciones únicas. "
                           f"Sesiones activas: {len(por_sesion)}.")
                max_bullets = 7
                bullets = "\n".join(f"• {s}" for s in items[:max_bullets])
                if vec_titulos:
                    bullets += ("\n\nDocumentos relevantes:\n" +
                                "\n".join(f"• {t}" for t in vec_titulos[:3]))
                respuesta_usuario = f"{cabecera}\n\n{bullets}"
            else:
                respuesta_usuario = "No hay interacciones útiles para mostrar."
            sintetizador_usado = False

        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "resumen": resumen,
                "respuesta_usuario": respuesta_usuario,
                "interacciones": top_interacciones,
                "por_sesion": {k: len(v) for k, v in por_sesion.items()},
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "docs_vectoriales": len(docs_vectoriales),
                    "docs_cosmos": len(top_interacciones),
                    "sintetizador_usado": sintetizador_usado
                }
            }, ensure_ascii=False),
            mimetype="application/json", status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error en memoria-global: {e}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )
