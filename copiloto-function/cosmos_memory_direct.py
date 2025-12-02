# -*- coding: utf-8 -*-
"""
Consulta directa a Cosmos DB para memoria sem├íntica
Reemplaza las funciones que no consultan realmente la base de datos
"""

from semantic_helpers import generar_resumen_conversacion
import logging
import os
import azure.functions as func

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from opentelemetry import metrics, trace
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential


_COSMOS_CLIENT = None
_COSMOS_CONTAINER = None
_COSMOS_DATABASE = None


def get_cosmos_client():
    """Retorna cliente y contenedor compartidos de Cosmos DB."""
    global _COSMOS_CLIENT, _COSMOS_CONTAINER, _COSMOS_DATABASE

    if _COSMOS_CLIENT and _COSMOS_CONTAINER:
        return _COSMOS_CLIENT, _COSMOS_CONTAINER

    endpoint = os.environ.get(
        "COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
    key = os.environ.get("COSMOSDB_KEY")
    database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
    container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")

    # Permitir autenticación con DefaultAzureCredential si no hay key explícita
    if key:
        client = CosmosClient(endpoint, key)
    else:
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential=credential)

    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    _COSMOS_CLIENT = client
    _COSMOS_DATABASE = database
    _COSMOS_CONTAINER = container
    return _COSMOS_CLIENT, _COSMOS_CONTAINER


def deduplicar_interacciones_semanticas(items: list, max_items: int = 50) -> list:
    """
    Deduplica interacciones sem├ínticamente similares
    Excluye endpoints meta-operacionales (historial, health, verificar)
    Mantiene solo la m├ís reciente de cada grupo
    """
    from collections import defaultdict
    import hashlib

    # ­ƒÜ½ FILTROS DE EXCLUSI├ôN
    ENDPOINTS_EXCLUIDOS = {
        'historial-interacciones', '/api/historial-interacciones',
        'health', '/api/health',
        'verificar-sistema', 'verificar-cosmos', 'verificar-app-insights'
    }

    PATRONES_BASURA = [
        'CONSULTA DE HISTORIAL',
        'Se encontraron',
        'interacciones recientes',
        'Consulta completada',
        'Sin resumen de conversaci├│n'
    ]

    # Filtrar items excluidos
    items_filtrados = []
    for item in items:
        endpoint = item.get('endpoint', '')
        texto = item.get('texto_semantico', '')
        session_id = item.get('session_id', '')

        if item.get("is_synthetic"):
            continue
        if item.get("document_class") and item.get("document_class") != "cognitive_memory":
            continue
        if session_id.startswith("fallback_session"):
            continue

        # Excluir endpoints meta-operacionales
        if endpoint in ENDPOINTS_EXCLUIDOS:
            continue

        # Excluir contenido basura
        if any(patron in texto for patron in PATRONES_BASURA):
            continue

        # Excluir texto muy corto
        if len(texto.strip()) < 10:
            continue

        items_filtrados.append(item)

    logging.info(
        f"­ƒÜ½ Filtrados {len(items) - len(items_filtrados)} items (meta-operacionales + basura)")

    # Agrupar por endpoint + hash sem├íntico del texto
    grupos = defaultdict(list)

    for item in items_filtrados:
        endpoint = item.get('endpoint', 'unknown')
        texto = item.get('texto_semantico', '')

        # Hash sem├íntico: primeros 100 chars normalizados
        texto_norm = texto[:100].lower().strip()
        hash_semantico = hashlib.md5(texto_norm.encode()).hexdigest()[:8]

        # Clave de agrupaci├│n: endpoint + hash
        clave = f"{endpoint}_{hash_semantico}"
        grupos[clave].append(item)

    # Tomar solo el m├ís reciente de cada grupo
    items_unicos = []
    for grupo in grupos.values():
        grupo_ordenado = sorted(
            grupo, key=lambda x: x.get('_ts', 0), reverse=True)
        items_unicos.append(grupo_ordenado[0])

    # Ordenar por timestamp y limitar
    items_unicos.sort(key=lambda x: x.get('_ts', 0), reverse=True)
    return items_unicos[:max_items]


def consultar_memoria_cosmos_directo(req: func.HttpRequest, session_override: Optional[str] = None, agent_override: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Consulta DIRECTAMENTE Cosmos DB para obtener historial de interacciones
    CON DEDUPLICACI├ôN SEM├üNTICA
    Soporta autenticación con Key o Managed Identity
    """
    try:
        # Extraer session_id del request o usar override
        session_id = session_override or extraer_session_id_request(req)
        if not session_id:
            logging.info("No se encontr├│ session_id en el request")
            return None

        # Extraer agent_id para fallback o usar override
        agent_id = agent_override or extraer_agent_id_request(req)

        # Conectar a Cosmos DB (soporta Key o MI)
        try:
            key = os.environ.get("COSMOSDB_KEY")
            endpoint = os.environ.get(
                "COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
            logging.info(f"🔌 Intentando conectar a Cosmos DB...")
            logging.info(f"   Endpoint: {endpoint}")
            logging.info(f"   Auth: {'Key' if key else 'Managed Identity'}")

            _, container = get_cosmos_client()
            logging.info("✅ Cosmos DB conectado exitosamente")
        except Exception as e:
            logging.error(f"❌ Cosmos DB no disponible: {type(e).__name__}")
            logging.error(f"   Detalle: {str(e)}")
            return None

        # ­ƒîì MEMORIA GLOBAL DIRECTA: Solo por agent_id
        if not agent_id or agent_id == "unknown_agent":
            agent_id = "GlobalAgent"  # Forzar agent_id por defecto
            logging.info(f"­ƒöº Agent ID forzado a: {agent_id}")

        # ­ƒîì MEMORIA GLOBAL CON DEDUPLICACI├ôN SEM├üNTICA
        # Traer más items para luego deduplicar
        query = """
        SELECT TOP 200 c.id, c.agent_id, c.session_id, c.endpoint, c.timestamp,
                       c.event_type, c.texto_semantico, c.contexto_conversacion,
                       c.metadata, c.resumen_conversacion, c.data.respuesta_resumen,
                       c.data.interpretacion_semantica, c.data.contexto_inteligente,
                       c.data.response_data.respuesta_usuario, c._ts
        FROM c
        WHERE IS_DEFINED(c.texto_semantico) 
          AND (NOT IS_DEFINED(c.document_class) OR c.document_class = 'cognitive_memory')
          AND (NOT IS_DEFINED(c.is_synthetic) OR c.is_synthetic != true)
          AND NOT CONTAINS(c.endpoint, 'health')
          AND NOT CONTAINS(c.endpoint, 'verificar-')
          AND NOT CONTAINS(c.endpoint, 'historial-interacciones')
        ORDER BY c._ts DESC
        """
        logging.info("­ƒîì Ejecutando memoria con deduplicaci├│n sem├íntica")
        logging.debug(f"­ƒîì Query: {query}")

        logging.info(f"🔍 Ejecutando query en Cosmos DB...")
        raw_items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        logging.info(
            f"📊 Query completada: {len(raw_items)} documentos recuperados")

        # Ô£à DEDUPLICACI├ôN SEM├üNTICA: Agrupar por endpoint + texto similar
        items = deduplicar_interacciones_semanticas(raw_items, max_items=50)
        logging.info(
            f"🔹 Deduplicación: {len(raw_items)} → {len(items)} interacciones únicas")

        # LOG de aplicaci├│n (aparece en 'traces' table)
        logging.info(
            "historial-interacciones: memoria_global_aplicada count=%d", len(items))

        # M├ëTRICA personalizada como log (AI la convierte en customMetrics)
        try:
            logging.info(
                f"customMetric|name=historial_interacciones_hits;value=1;agent_id={agent_id};endpoint=historial_interacciones"
            )
        except Exception as _:
            pass

        # TRACE manual (aparece en 'traces' con span)
        try:
            tracer = trace.get_tracer("copiloto.memory")
            with tracer.start_as_current_span("consultar_memoria_cosmos_directo") as span:
                span.set_attribute("items_encontrados", len(items))
                span.set_attribute("agent_id", agent_id or "unknown")
        except Exception as _:
            pass

        if items:
            logging.info(
                f"🔌 Memoria global: {len(items)} interacciones encontradas")
            logging.info(
                f"   Primera: {items[0].get('endpoint', 'N/A')} - {items[0].get('timestamp', 'N/A')}")
        else:
            logging.warning("🚫 Sin memoria previa encontrada")
            logging.warning(f"   Raw items antes de filtrar: {len(raw_items)}")
            if len(raw_items) > 0:
                logging.warning(
                    f"   Causa: Todos filtrados por deduplicación/exclusión")

        if items:
            # Procesar interacciones encontradas CON TEXTO_SEMANTICO
            interacciones_formateadas = []

            # Ajustes de truncado m├ís generosos para evitar p├®rdida de contexto
            CONSULTA_MAX = int(os.environ.get("CONSULTA_MAX_CHARS", "1000"))
            RESPUESTA_MAX = int(os.environ.get("RESPUESTA_MAX_CHARS", "1000"))
            LOG_SNIPPET = int(os.environ.get("LOG_SNIPPET_CHARS", "200"))

            for item in items:
                # Extraer datos del nivel ra├¡z y de secci├│n posible de data
                data_section = item.get("data", {})

                # Ô£à EXTRAER INFORMACI├ôN ENRIQUECIDA
                consulta_text = (
                    data_section.get("params", {}).get("comando", "") or
                    data_section.get("params", {}).get("consulta", "") or
                    item.get("resumen_conversacion", "") or
                    ""
                )

                # Ô£à PRIORIZAR respuesta_resumen si existe
                respuesta_text = (
                    item.get("respuesta_resumen") or  # Campo directo
                    data_section.get("respuesta_resumen") or  # En data
                    # Interpretaci├│n
                    data_section.get("interpretacion_semantica", "") or
                    # respuesta_usuario
                    str(data_section.get("response_data", {}).get("respuesta_usuario", "")) or
                    item.get("resumen_conversacion", "")
                )

                # Ô£à EXTRAER CONTEXTO INTELIGENTE si existe
                contexto_extra = None
                if data_section.get("contexto_inteligente"):
                    ctx = data_section["contexto_inteligente"]
                    if isinstance(ctx, dict) and ctx.get("resumen_inteligente"):
                        contexto_extra = ctx["resumen_inteligente"]

                interaccion = {
                    "timestamp": item.get("timestamp", data_section.get("timestamp", "")),
                    "endpoint": item.get("endpoint", data_section.get("endpoint", "unknown")),
                    "consulta": consulta_text[:CONSULTA_MAX],
                    "exito": data_section.get("success", True),
                    # NIVEL RA├ìZ
                    "texto_semantico": item.get("texto_semantico", ""),
                    "respuesta_resumen": respuesta_text[:RESPUESTA_MAX],
                    "contexto_extra": contexto_extra  # Ô£à NUEVO: Contexto adicional
                }
                interacciones_formateadas.append(interaccion)

                # Log para verificar (mostrar snippet mayor)
                texto_snippet = interaccion['texto_semantico'][:LOG_SNIPPET] if interaccion[
                    'texto_semantico'] else interaccion['consulta'][:LOG_SNIPPET]
                logging.info(
                    f"­ƒôØ Interacci├│n recuperada: {interaccion['endpoint']} - texto: {texto_snippet}...")
                if contexto_extra:
                    logging.info(
                        f"  ­ƒÄ» Contexto extra: {contexto_extra[:100]}...")

            # Generar resumen para el agente
            resumen_conversacion = generar_resumen_conversacion(
                interacciones_formateadas)

            # ­ƒºá INTERPRETACI├ôN SEM├üNTICA RICA DEL SISTEMA
            interpretacion_semantica = interpretar_patron_semantico(
                interacciones_formateadas)
            logging.info(
                f"­ƒºá Interpretaci├│n sem├íntica: {interpretacion_semantica}")

            # ­ƒÄ» CONTEXTO INTELIGENTE ADICIONAL
            try:
                from semantic_classifier import get_intelligent_context
                context_analysis = get_intelligent_context(
                    interacciones_formateadas)
                contexto_inteligente = {
                    "modo_operacion": context_analysis['mode'],
                    "contexto_seleccionado": len(context_analysis['context']),
                    "total_analizado": context_analysis['total_analyzed'],
                    "resumen_inteligente": context_analysis['summary']
                }
                logging.info(
                    f"­ƒÄ» Contexto inteligente: {contexto_inteligente}")
            except ImportError:
                contexto_inteligente = {
                    "modo_operacion": "fallback",
                    "contexto_seleccionado": len(interacciones_formateadas),
                    "total_analizado": len(items),
                    "resumen_inteligente": "An├ílisis b├ísico aplicado"
                }

            # Dejar registro local adicional justo antes del return para verificar emisi├│n
            logging.info(
                "Ô£à customMetric|name=historial_interacciones_hits;value=1;agent_id=%s;endpoint=historial_interacciones", agent_id)

            response = {
                "tiene_historial": True,
                "session_id": session_id,
                "agent_id": agent_id,
                "total_interacciones": len(items),
                "total_interacciones_sesion": len(items),
                "interacciones_recientes": interacciones_formateadas,
                "resumen_conversacion": resumen_conversacion,
                "interpretacion_semantica": interpretacion_semantica,
                "contexto_inteligente": contexto_inteligente,
                "ultima_actividad": items[0].get("timestamp") if items else None,
                "contexto_recuperado": True,
                "memoria_global": True,
                "estrategia": "global_por_agent_id",
                "foundry_optimized": False,
                "validation_applied": False,
                "validation_stats": {
                    "original_count": len(items),
                    "final_optimized": len(interacciones_formateadas)
                },
                "metadata": {
                    "memoria_aplicada": True,
                    "memoria_global": True,
                    "interacciones_previas": len(items),
                    "endpoint_detectado": "historial_interacciones",
                    "agent_id": agent_id,
                    "foundry_detected": False,
                    "session_info": {
                        "session_id": session_id,
                        "agent_id": agent_id
                    },
                    "memoria_disponible": True,
                    "wrapper_aplicado": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # ­ƒöì VALIDACI├ôN DE CONTEXTO ANTES DEL MODELO
            try:
                from context_validator import validate_context_before_model
                response = validate_context_before_model(response)
                logging.info(f"­ƒöì Contexto validado y optimizado")
            except ImportError:
                logging.warning("ÔÜá´©Å Validador de contexto no disponible")

            return response
        else:
            return {
                "tiene_historial": False,
                "session_id": session_id,
                "agent_id": agent_id,
                "nueva_sesion": True,
                "memoria_global": False,
                "estrategia": "sin_memoria",
                "interpretacion_semantica": "Nueva sesi├│n iniciada sin historial previo",
                "contexto_inteligente": {
                    "modo_operacion": "new_session",
                    "contexto_seleccionado": 0,
                    "total_analizado": 0,
                    "resumen_inteligente": "Sin contexto previo disponible"
                },
                "validation_applied": True,
                "validation_stats": {
                    "original_count": 0,
                    "final_optimized": 0
                },
                "metadata": {
                    "memoria_aplicada": False,
                    "memoria_global": False,
                    "interacciones_previas": 0,
                    "endpoint_detectado": "historial_interacciones",
                    "agent_id": agent_id,
                    "session_info": {
                        "session_id": session_id,
                        "agent_id": agent_id
                    },
                    "memoria_disponible": False,
                    "wrapper_aplicado": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

    except Exception as e:
        logging.error(f"Error consultando Cosmos DB directamente: {e}")
        return None


def extraer_session_id_request(req: func.HttpRequest) -> Optional[str]:
    """Extrae session_id de m├║ltiples fuentes en el request (solo para metadata)"""

    # 1. Desde headers (prioridad alta)
    session_id = (
        req.headers.get("Session-ID") or
        req.headers.get("X-Session-ID") or
        req.headers.get("x-session-id")
    )
    if session_id:
        return session_id

    # 2. Desde par├ímetros de query
    session_id = req.params.get("session_id")
    if session_id:
        return session_id

    # 3. Desde body JSON
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            session_id = body.get("session_id")
            if session_id:
                return session_id
    except:
        pass

    # 4. Generar session_id temporal (solo para metadata, no afecta memoria)
    import time
    session_id = f"temp_{int(time.time())}"
    return session_id


# Importar funci├│n desde semantic_helpers

# Usar clasificador sem├íntico existente para interpretaci├│n din├ímica
try:
    from semantic_classifier import get_intelligent_context
    from semantic_intent_classifier import classify_user_intent

    def interpretar_patron_semantico(interacciones: list) -> str:
        if not interacciones:
            return "Sin actividad previa detectada"

        # Usar el contexto inteligente existente
        contexto = get_intelligent_context(interacciones)

        # Analizar la ├║ltima interacci├│n para detectar intenci├│n
        ultima = interacciones[0] if interacciones else {}
        texto_semantico = ultima.get('texto_semantico', '')

        if texto_semantico:
            intent_result = classify_user_intent(texto_semantico)
            intent = intent_result.get('intent', 'general')
            confidence = intent_result.get('confidence', 0.5)

            return f"An├ílisis inteligente: {contexto['summary']} | Intenci├│n detectada: {intent} (confianza: {int(confidence*100)}%) | Modo: {contexto['mode']}"
        else:
            return f"An├ílisis inteligente: {contexto['summary']} | Modo: {contexto['mode']}"

except ImportError:
    def interpretar_patron_semantico(interacciones: list) -> str:
        if not interacciones:
            return "Sin actividad previa detectada"
        return f"An├ílisis de {len(interacciones)} interacciones completado"


def aplicar_memoria_cosmos_directo(req: func.HttpRequest, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica memoria consultando directamente Cosmos DB y enriquece la respuesta
    INCLUYE detecci├│n autom├ítica de endpoint para evitar "unknown"
    """
    try:
        # ­ƒÄ» DETECTAR ENDPOINT AUTOM├üTICAMENTE
        endpoint_detectado = "unknown"
        try:
            from endpoint_detector import aplicar_deteccion_endpoint_automatica
            endpoint_detectado = aplicar_deteccion_endpoint_automatica(req)
            logging.info(
                f"­ƒÄ» Endpoint auto-detectado para memoria: {endpoint_detectado}")
        except Exception as e:
            logging.warning(
                f"ÔÜá´©Å Error en detecci├│n autom├ítica de endpoint: {e}")

        # ­ƒñû DETECTAR SI ES FOUNDRY PARA OPTIMIZAR RESPUESTA
        user_agent = req.headers.get("User-Agent", "")
        es_foundry = "azure-agents" in user_agent.lower()
        if es_foundry:
            logging.info(
                "­ƒñû Foundry detectado - optimizando respuesta sem├íntica")

        # Consultar memoria directamente
        memoria = consultar_memoria_cosmos_directo(req)

        if memoria and memoria.get("tiene_historial"):
            # Asegurar que response_data es mutable
            if not isinstance(response_data, dict):
                response_data = {"data": response_data}

            # Agregar contexto de conversaci├│n al inicio
            if "contexto_conversacion" not in response_data:
                response_data["contexto_conversacion"] = {
                    "mensaje": f"Memoria global activa: {memoria.get('total_interacciones', 0)} interacciones previas del agente {memoria.get('agent_id', 'unknown')}",
                    "ultimas_consultas": memoria.get("resumen_conversacion", ""),
                    "session_id": memoria.get("session_id"),
                    "agent_id": memoria.get("agent_id"),
                    "ultima_actividad": memoria.get("ultima_actividad"),
                    "estrategia_memoria": "global_por_agent_id"
                }

            # Agregar metadata de memoria
            if "metadata" not in response_data:
                response_data["metadata"] = {}

            response_data["metadata"].update({
                "memoria_aplicada": True,
                "memoria_global": True,
                "interacciones_previas": memoria.get("total_interacciones", 0),
                "endpoint_detectado": endpoint_detectado,
                "agent_id": memoria.get("agent_id"),
                "session_info": {
                    "session_id": memoria.get("session_id"),
                    "agent_id": memoria.get("agent_id")
                },
                "memoria_disponible": True,
                "wrapper_aplicado": True,
                "aplicacion_manual": True,
                "timestamp": datetime.now().isoformat()
            })

            logging.info(
                f"­ƒºá Memoria global aplicada: {memoria.get('total_interacciones', 0)} interacciones para {memoria.get('agent_id')}")
        else:
            # Sin memoria disponible
            if "metadata" not in response_data:
                response_data["metadata"] = {}

            response_data["metadata"].update({
                "memoria_aplicada": False,
                "memoria_global": False,
                "interacciones_previas": 0,
                "endpoint_detectado": endpoint_detectado,
                "session_info": {
                    "session_id": None,
                    "agent_id": None
                },
                "memoria_disponible": False,
                "wrapper_aplicado": True,
                "timestamp": datetime.now().isoformat()
            })

            logging.info("­ƒôØ Sin memoria previa disponible")

        return response_data

    except Exception as e:
        logging.error(f"Error aplicando memoria Cosmos directo: {e}")
        return response_data


# Usar sistema existente de memory_service
try:
    from services.memory_service import memory_service

    def registrar_redireccion_cosmos(req: func.HttpRequest, endpoint_original: str, fue_redirigido: bool, respuesta_redirigida: Any) -> bool:
        try:
            memory_service.registrar_llamada(
                source="redirect",
                endpoint=endpoint_original,
                method=req.method,
                params={"redirigido": fue_redirigido},
                response_data=respuesta_redirigida,
                success=True
            )
            return True
        except Exception:
            return False
except ImportError:
    def registrar_redireccion_cosmos(req: func.HttpRequest, endpoint_original: str, fue_redirigido: bool, respuesta_redirigida: Any) -> bool:
        return True  # Fallback silencioso


def extraer_input_usuario_simple(req: func.HttpRequest) -> str:
    """Extrae input del usuario de forma simple"""
    try:
        # Par├ímetros
        for key in ['consulta', 'query', 'mensaje', 'q']:
            if key in req.params:
                return str(req.params[key])

        # Body
        try:
            body = req.get_json()
            if body:
                for key in ['consulta', 'query', 'mensaje', 'prompt']:
                    if key in body:
                        return str(body[key])
        except:
            pass

        return "input_no_detectado"
    except:
        return "error_extrayendo_input"


def registrar_interaccion_cosmos_directo(req: func.HttpRequest, endpoint: str, response_data: Dict[str, Any]) -> bool:
    """
    Registra la interacci├│n actual directamente en Cosmos DB con el endpoint correcto
    """
    try:
        from azure.cosmos import CosmosClient

        # Configuraci├│n de Cosmos DB
        cosmos_endpoint = os.environ.get(
            "COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")

        if not key:
            return False

        # Extraer informaci├│n del request
        session_id = extraer_session_id_request(req) or "unknown_session"
        agent_id = extraer_agent_id_request(req) or "unknown_agent"
        input_usuario = extraer_input_usuario_simple(req)

        # Conectar a Cosmos DB
        client = CosmosClient(cosmos_endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Crear documento de interacci├│n con ID ├║nico
        timestamp_unico = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        documento = {
            "id": f"interaction_{session_id}_{timestamp_unico}",
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,  # ­ƒÄ» ENDPOINT CORRECTO DETECTADO AUTOM├üTICAMENTE
            "consulta": input_usuario[:500],  # Limitar tama├▒o
            # Respuesta resumida
            "respuesta": str(response_data).replace('"', "'")[:500],
            "exito": response_data.get("exito", True) if isinstance(response_data, dict) else True,
            "method": getattr(req, 'method', 'GET'),
            "tipo": "interaccion_usuario",
            "_ts": int(datetime.now().timestamp())
        }

        # Usar upsert para evitar conflictos
        container.upsert_item(documento)
        logging.info(
            f"­ƒÆ¥ Interacci├│n registrada en Cosmos: {endpoint} (session: {session_id[:8]}...)")
        return True

    except Exception as e:
        logging.warning(
            f"ÔÜá´©Å Error registrando interacci├│n en Cosmos: {e}")
        return False


def extraer_agent_id_request(req: func.HttpRequest) -> str:
    """Extrae agent_id del request (CR├ìTICO para memoria global)"""
    try:
        # Headers
        agent_id = (
            req.headers.get("Agent-ID") or
            req.headers.get("X-Agent-ID") or
            req.headers.get("x-agent-id")
        )
        if agent_id:
            logging.info(f"­ƒñû Agent ID desde headers: {agent_id}")
            return agent_id

        # Par├ímetros
        agent_id = req.params.get("agent_id")
        if agent_id:
            logging.info(f"­ƒñû Agent ID desde params: {agent_id}")
            return agent_id

        # Body
        try:
            body = req.get_json()
            if body and isinstance(body, dict):
                agent_id = body.get("agent_id")
                if agent_id:
                    logging.info(f"­ƒñû Agent ID desde body: {agent_id}")
                    return agent_id
        except:
            pass

        # SIEMPRE retornar GlobalAgent como fallback
        agent_id = "GlobalAgent"
        logging.info(f"­ƒöº Agent ID forzado a fallback: {agent_id}")
        return agent_id
    except:
        return "GlobalAgent"
