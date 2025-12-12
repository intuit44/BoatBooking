"""
Endpoint: /api/buscar-memoria
Endpoints de Búsqueda Semántica - Azure AI Search con Managed Identity
"""

from function_app import app
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import azure.functions as func


def _sanitize_filter_string(filter_str: Optional[str]) -> Optional[str]:
    if not filter_str:
        return None
    clauses = [clause.strip()
               for clause in filter_str.split(" and ") if clause.strip()]
    cleaned = [
        clause for clause in clauses
        if "is_synthetic" not in clause.lower()
        and "document_class" not in clause.lower()
    ]
    return " and ".join(cleaned) if cleaned else None


def _doc_es_ruido(doc: Any) -> bool:
    """Descarta documentos de hilos asistente (assistant-*.json) o threads/* que contaminan contexto inicial."""
    if not isinstance(doc, dict):
        return False
    campos = ("id", "ruta", "ruta_blob", "blob_path",
              "nombre", "name", "archivo", "path")
    for campo in campos:
        val = doc.get(campo)
        if isinstance(val, str):
            low = val.lower()
            if "assistant-" in low or "threads/" in low:
                return True
    return False


def _filtrar_ruido_docs(docs: Any) -> list:
    if not isinstance(docs, list):
        return []
    return [d for d in docs if not _doc_es_ruido(d)]


def _enriquecer_respuesta_llm(resultado: Dict[str, Any], include_context: bool, include_narrative: bool, format_type: str, req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquece la respuesta con contexto narrativo para LLM
    """
    try:
        documentos = resultado.get("documentos", [])
        total = resultado.get("total", 0)

        # Crear contexto narrativo
        contexto_narrativo = {
            "resumen_busqueda": f"Se encontraron {total} documentos relevantes en memoria semántica",
            "modo_busqueda_usado": resultado.get("metadata", {}).get("modo_busqueda", "desconocido"),
            "query_procesada": resultado.get("metadata", {}).get("query_original", ""),
            "timestamp": datetime.utcnow().isoformat()
        }

        if include_context and documentos:
            # Extraer contextos textuales de los documentos
            contextos = []
            # Límite de 5 para evitar respuestas demasiado largas
            for doc in documentos[:5]:
                if doc.get("texto_semantico"):
                    contextos.append({
                        "fuente": doc.get("id", "desconocida"),
                        "contenido": doc.get("texto_semantico")[:500] + "..." if len(doc.get("texto_semantico", "")) > 500 else doc.get("texto_semantico", ""),
                        "timestamp": doc.get("timestamp", "desconocido"),
                        "session_id": doc.get("session_id", "desconocida")
                    })
            contexto_narrativo["contextos_extraidos"] = contextos

        if include_narrative:
            # Generar narrativa para LLM
            if total > 0:
                contexto_narrativo["narrativa_llm"] = f"""
                Encontré {total} elementos relevantes en la memoria semántica. Los documentos contienen información 
                relacionada con la consulta realizada. El modo de búsqueda utilizado fue '{resultado.get('metadata', {}).get('modo_busqueda', 'desconocido')}'.
                
                {'Esta información puede ser utilizada como contexto para generar respuestas más informadas.' if include_context else ''}
                
                Los resultados están ordenados por relevancia semántica.
                """.strip()
            else:
                contexto_narrativo["narrativa_llm"] = """
                No se encontraron documentos específicamente relevantes para esta consulta en la memoria semántica.
                Esto podría significar que es una consulta nueva o que requiere información externa.
                """.strip()

        # Agregar enhanced info al resultado
        resultado["enhanced_response"] = contexto_narrativo
        resultado["llm_ready"] = True
        resultado["format_requested"] = format_type

        # Si se pidió formato específico
        if format_type == "narrative" and include_narrative:
            resultado["response_text"] = contexto_narrativo.get(
                "narrativa_llm", "")

        logging.info(
            f"🤖 Respuesta enriquecida para LLM: {len(contexto_narrativo)} elementos agregados")

    except Exception as e:
        logging.warning(f"⚠️ Error enriqueciendo respuesta para LLM: {e}")
        # No fallar, solo agregar info básica
        resultado["enhanced_response"] = {"error": str(e), "fallback": True}
        resultado["llm_ready"] = False

    return resultado


def _search_with_fallback(service, query: str, top: int, filter_str: Optional[str]):
    try:
        result = service.search(query=query, top=top, filters=filter_str)
        return result, filter_str
    except Exception as exc:
        message = str(exc)
        if ("is_synthetic" in message or "document_class" in message):
            clean_filter = _sanitize_filter_string(filter_str)
            if clean_filter != filter_str:
                logging.warning(
                    "⚠️ Campo inexistente en filtro; reintentando búsqueda sin filtros sintéticos")
                result = service.search(query=query, top=top,
                                        filters=clean_filter)
                return result, clean_filter
        raise


@app.function_name(name="buscar_memoria_endpoint")
@app.route(route="buscar-memoria", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def buscar_memoria_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function: Buscar en memoria semántica
    Endpoint HTTP que expone buscar_memoria_endpoint
    """
    try:
        # Obtener payload del request
        try:
            req_body = req.get_json() or {}
        except Exception:
            req_body = {}

        # Procesar búsqueda usando la función interna
        resultado = buscar_memoria_endpoint(req_body)

        # Siempre HTTP 200 para LLM compatibility
        return func.HttpResponse(
            json.dumps(resultado, default=str, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        error_response = {
            "exito": False,
            "error": str(e),
            "mensaje": "Error procesando búsqueda de memoria",
            "timestamp": datetime.utcnow().isoformat()
        }

        logging.error(f"Error en buscar_memoria_http: {str(e)}", exc_info=True)

        return func.HttpResponse(
            json.dumps(error_response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )


def buscar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/buscar-memoria
    Busca en memoria semántica usando Azure AI Search
    🔥 SESSION WIDENING: Cascada de búsqueda (sesión → agente → universal)
    🔧 DETECCIÓN TÉCNICA: Búsqueda literal para UUIDs e IDs
    🤖 LLM ENHANCED: Soporta parámetros para respuestas narrativas
    """
    try:
        from services.azure_search_client import get_search_service
        from semantic_query_builder import detectar_query_tecnica, buscar_literal_cosmos
        from services.cosmos_store import CosmosMemoryStore

        # Extraer parámetros enhanced para LLM
        # 🤖 ENHANCEMENT OPCIONAL - solo cuando se solicite explícitamente
        include_context = req_body.get(
            "include_context", False)  # Por defecto False
        include_narrative = req_body.get(
            "include_narrative", False)  # Por defecto False
        format_type = req_body.get("format", "json")

        # Validar payload - con defaults enhanced activados, query sigue siendo requerido
        query = req_body.get("query", "").strip()
        if not query:
            return {"exito": False, "error": "Campo 'query' requerido para búsqueda semántica"}

        # 🤖 LOG enhancement activado por defecto
        if include_context or include_narrative:
            logging.info(
                f"🤖 Enhancement LLM activado - context:{include_context}, narrative:{include_narrative}, format:{format_type}")

        session_id = req_body.get("session_id")
        agent_id = req_body.get("agent_id")
        top = int(req_body.get("top", 10))
        tipo = req_body.get("tipo")

        GENERIC_SESSIONS = {"assistant", "test_session", "unknown",
                            "agent-default", "fallback_session", None, ""}
        GENERIC_AGENTS = {"foundry_user", "default",
                          "assistant", "unknown", None, ""}

        base_filters = [
            "is_synthetic ne true",
            "(document_class eq 'cognitive_memory' or document_class eq null)"
        ]

        # 🔧 DETECTAR SI ES QUERY TÉCNICA (UUID, Client ID, etc.)
        query_tecnica = detectar_query_tecnica(query)

        if query_tecnica:
            # Usar búsqueda LITERAL en Cosmos DB
            logging.info(
                f"🔧 Query técnica detectada: {query_tecnica['tipo']} → búsqueda literal")
            try:
                cosmos_store = CosmosMemoryStore()
                if not cosmos_store.enabled or not cosmos_store.container:
                    raise Exception("Cosmos DB no disponible")

                documentos = buscar_literal_cosmos(
                    query_tecnica=query_tecnica,
                    cosmos_container=cosmos_store.container,
                    session_id=session_id,
                    agent_id=agent_id
                )

                return {
                    "exito": True,
                    "total": len(documentos),
                    "documentos": documentos[:top],
                    "metadata": {
                        "query_original": query,
                        "modo_busqueda": "literal_cosmos",
                        "query_tecnica": query_tecnica,
                        "session_widening_activo": True,
                        "tiempo_busqueda": datetime.utcnow().isoformat()
                    }
                }
            except Exception as cosmos_err:
                logging.warning(
                    f"⚠️ Búsqueda literal falló: {cosmos_err}, fallback a vectorial")
                # Continuar con búsqueda vectorial como fallback

        # Búsqueda VECTORIAL normal (Azure AI Search)
        search_service = get_search_service()

        # 🔄 CASCADA DE BÚSQUEDA
        resultado = None
        modo_usado = None
        filtros_usados = None

        # NIVEL 1: Búsqueda en sesión específica
        if session_id and session_id not in GENERIC_SESSIONS:
            filters = list(base_filters)
            safe_sid = str(session_id).replace("'", "''")
            filters.append(f"session_id eq '{safe_sid}'")
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo_interaccion eq '{safe_tipo}'")

            filter_str = " and ".join(filters)
            resultado, filter_str_final = _search_with_fallback(
                search_service, query, top, filter_str)

            if resultado.get("exito") and resultado.get("total", 0) > 0:
                modo_usado = "session_specific"
                filtros_usados = filter_str_final or "NINGUNO"
                logging.info(
                    f"✅ Nivel 1: Encontrados {resultado['total']} en sesión {session_id}")
            else:
                logging.info(
                    f"⚠️ Nivel 1: 0 resultados en sesión {session_id}, escalando...")
                resultado = None

        # NIVEL 2: Búsqueda por agent_id (todas las sesiones)
        if not resultado and agent_id and agent_id not in GENERIC_SESSIONS:
            filters = list(base_filters)
            safe_aid = str(agent_id).replace("'", "''")
            filters.append(f"agent_id eq '{safe_aid}'")
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo_interaccion eq '{safe_tipo}'")

            filter_str = " and ".join(filters)
            resultado, filter_str_final = _search_with_fallback(
                search_service, query, top, filter_str)

            if resultado.get("exito") and resultado.get("total", 0) > 0:
                modo_usado = "agent_wide"
                filtros_usados = filter_str_final or "NINGUNO"
                logging.info(
                    f"✅ Nivel 2: Encontrados {resultado['total']} para agent_id {agent_id}")
            else:
                logging.info(
                    f"⚠️ Nivel 2: 0 resultados para agent_id {agent_id}, escalando...")
                resultado = None

        # NIVEL 3: Búsqueda universal (sin filtros de sesión/agente)
        if not resultado:
            # Si el session_id y agent_id son genéricos, no escalar a universal para evitar ruido cruzado
            if (session_id in GENERIC_SESSIONS) and (agent_id in GENERIC_AGENTS):
                logging.info(
                    "⚠️ Búsqueda universal omitida por session/agent genéricos")
                return {"exito": True, "total": 0, "documentos": [], "metadata": {
                    "modo_busqueda": "omitido_por_generico",
                    "query_original": query,
                    "filtros_aplicados": {
                        "session_id": "generico",
                        "agent_id": "generico",
                        "tipo_interaccion": tipo
                    },
                    "session_widening_activo": False,
                    "filtros_odata": "omitido",
                    "tiempo_busqueda": datetime.utcnow().isoformat()
                }}
            filters = list(base_filters)
            if tipo:
                safe_tipo = str(tipo).replace("'", "''")
                filters.append(f"tipo_interaccion eq '{safe_tipo}'")

            filter_str = " and ".join(filters)
            resultado, filter_str_final = _search_with_fallback(
                search_service, query, top, filter_str)
            modo_usado = "universal"
            filtros_usados = filter_str_final or "NINGUNO"
            logging.info(
                f"✅ Nivel 3: Búsqueda universal → {resultado.get('total', 0)} resultados")

        # Agregar metadata explicativa
        if resultado and resultado.get("exito"):
            # Filtrar ruido (threads/assistant-*.json) antes de devolver
            docs_filtrados = _filtrar_ruido_docs(
                resultado.get("documentos", []))
            resultado["documentos"] = docs_filtrados
            resultado["total"] = len(docs_filtrados)

            resultado["metadata"] = {
                "query_original": query,
                "filtros_aplicados": {
                    "session_id": session_id if session_id and session_id not in GENERIC_SESSIONS else "no aplicado",
                    "tipo_interaccion": tipo,
                    "agent_id": agent_id if agent_id and agent_id not in GENERIC_SESSIONS else "no aplicado"
                },
                "modo_busqueda": modo_usado,
                "session_widening_activo": True,
                "filtros_odata": filtros_usados,
                "tiempo_busqueda": datetime.utcnow().isoformat()
            }

        if resultado:
            logging.info(
                f"🔍 Búsqueda '{query}' → {resultado.get('total', 0)} resultados [modo: {modo_usado}]")

            # 🤖 ENRIQUECER RESPUESTA PARA LLM si se solicitaron parámetros enhanced
            if any([include_context, include_narrative, format_type != "json"]):
                resultado = _enriquecer_respuesta_llm(
                    resultado, include_context, include_narrative, format_type, req_body)

        return resultado or {"exito": False, "error": "No se pudo completar la búsqueda"}

    except Exception as e:
        logging.error(f"Error en buscar_memoria: {e}")
        return {"exito": False, "error": str(e)}


@app.function_name(name="indexar_memoria_endpoint")
@app.route(route="indexar-memoria-search", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def indexar_memoria_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function: Indexar documentos en memoria semántica
    """
    try:
        req_body = req.get_json() or {}
        resultado = indexar_memoria_endpoint(req_body)

        return func.HttpResponse(
            json.dumps(resultado, default=str, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if resultado.get("exito") else 400
        )

    except Exception as e:
        error_response = {
            "exito": False,
            "error": str(e),
            "mensaje": "Error indexando memoria"
        }

        logging.error(
            f"Error en indexar_memoria_http: {str(e)}", exc_info=True)

        return func.HttpResponse(
            json.dumps(error_response, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )


def indexar_memoria_endpoint(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint: /api/indexar-memoria
    Indexa documentos en Azure AI Search CON EMBEDDINGS REALES
    """
    try:
        from services.azure_search_client import get_search_service
        from embedding_generator import generar_embedding
        from services.memory_service import MemoryService

        memory_service = MemoryService()

        # Validar payload
        documentos = req_body.get("documentos")
        if not documentos or not isinstance(documentos, list):
            return {"exito": False, "error": "Campo 'documentos' requerido (array)"}
        index_name = req_body.get(
            "index_name") or req_body.get("indice_destino")

        documentos_con_vectores = []
        duplicados = 0
        indexados = 0

        for doc in documentos:
            if not doc.get("id"):
                logging.warning("Documento omitido: falta 'id'")
                continue
            if not doc.get("agent_id"):
                logging.warning(
                    f"Documento {doc.get('id')} omitido: falta 'agent_id'")
                continue
            if not doc.get("texto_semantico"):
                logging.warning(
                    f"Documento {doc.get('id')} omitido: falta 'texto_semantico'")
                continue

            texto = doc.get("texto_semantico", "")

            try:
                if memory_service.evento_ya_existe(texto):
                    duplicados += 1
                    logging.info(
                        f"⏭️ Duplicado detectado: {doc['id']} — omitido")
                    continue
            except Exception as mem_err:
                logging.warning(
                    f"Error verificando duplicado en {doc['id']}: {mem_err} — se continúa")

            vector = generar_embedding(texto)
            if not vector:
                logging.warning(
                    f"⚠️ No se pudo generar embedding para {doc['id']}, omitido")
                continue

            # Ajustar al esquema del índice: el campo vectorial es vector_semantico
            doc["vector_semantico"] = vector

            if "timestamp" in doc:
                ts = doc["timestamp"]
                if isinstance(ts, str):
                    if '.' in ts:
                        base, micro = ts.split('.')
                        micro = micro[:3]
                        doc["timestamp"] = f"{base}.{micro}Z"
                    elif not ts.endswith('Z'):
                        doc["timestamp"] = f"{ts}Z"

            documentos_con_vectores.append(doc)

        if not documentos_con_vectores:
            return {
                "exito": True,
                "indexados": 0,
                "duplicados": duplicados,
                "mensaje": "Todos los documentos eran duplicados o inválidos"
            }

        search_service = get_search_service()
        resultado = search_service.indexar_documentos(
            documentos_con_vectores, index_name=index_name)

        indexados = len(documentos_con_vectores)

        if resultado.get("exito"):
            logging.info(
                f"✅ Indexados {indexados} documentos CON EMBEDDINGS en Azure Search")

        return {
            "exito": resultado.get("exito", False),
            "indexados": indexados,
            "duplicados": duplicados,
            "error": resultado.get("error") if not resultado.get("exito") else None
        }

    except Exception as e:
        logging.error(f"Error en indexar_memoria: {e}")
        return {"exito": False, "error": str(e)}
