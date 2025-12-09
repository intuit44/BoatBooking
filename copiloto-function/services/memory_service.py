import os
import json
import logging
import uuid
from datetime import timezone, datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Sequence
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from services.cosmos_store import CosmosMemoryStore
from services.redis_buffer_service import redis_buffer

COGNITIVE_INDEX_NAME = os.environ.get(
    "AZURE_SEARCH_INDEX", "agent-memory-index-optimized")
LOG_INDEX_NAME = os.environ.get("AZURE_SEARCH_LOG_INDEX", COGNITIVE_INDEX_NAME)

DOC_CLASS_COGNITIVE = "cognitive_memory"
DOC_CLASS_SYSTEM = "system_log"
DOC_CLASS_SYNTHETIC = "synthetic_summary"

SYNTHETIC_EVENT_TYPES = {
    "respuesta_semantica",
    "conversation_snapshot",
    "endpoint_call",
    "agent_snapshot",
    "context_snapshot"
}

SYSTEM_ENDPOINT_KEYWORDS = [
    "historial",
    "health",
    "status",
    "diagnostico",
    "precalentar",
    "introspection",
    "verificar",
    "heartbeat",
    "monitor",
    "cli",
    "copiloto",
    "fallback"
]

SYSTEM_ENDPOINTS = {
    'historial-interacciones', '/api/historial-interacciones', 'historial_interacciones',
    'health', '/api/health',
    'status', '/api/status',
    'diagnostico', '/api/diagnostico',
    'precalentar-memoria', '/api/precalentar-memoria',
    'introspection', '/api/introspection',
    'verificar-sistema', '/api/verificar-sistema',
    'verificar-cosmos', '/api/verificar-cosmos',
    'ejecutar-cli', 'ejecutar_cli', '/api/ejecutar-cli',
    'dashboard', '/api/dashboard'
}


class MemoryService:
    def __init__(self):
        # Configurar Cosmos DB directamente
        self.cosmos = CosmosMemoryStore()
        endpoint = os.environ.get('COSMOSDB_ENDPOINT') or ""
        key = os.environ.get('COSMOSDB_KEY')
        database_name = os.environ.get('COSMOSDB_DATABASE', 'agentMemory')

        try:
            if key:
                client = CosmosClient(endpoint, key)
            else:
                credential = DefaultAzureCredential()
                client = CosmosClient(endpoint, credential)

            database = client.get_database_client(database_name)
            self.memory_container = database.get_container_client('memory')
            self.cosmos_available = True
        except Exception as e:
            logging.warning(f"Cosmos DB no disponible: {e}")
            self.cosmos_available = False
            self.memory_container = None

        # Fallback local
        self.local_enabled = True
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        self.semantic_log_file = self.scripts_dir / "semantic_log.jsonl"

    def log_event(self, event_type: str, data: Dict[str, Any], session_id: Optional[str] = None) -> bool:
        """Registra evento en local + Cosmos DB"""
        timestamp = datetime.now(timezone.utc).isoformat()
        session_id = session_id or f"session_{int(datetime.now(timezone.utc).timestamp())}"

        # Estructura unificada
        event = {
            "id": f"{session_id}_{event_type}_{int(datetime.now(timezone.utc).timestamp())}",
            "session_id": session_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }

        if isinstance(data, dict):
            event["tipo"] = data.get("tipo") or event_type
            if data.get("document_class"):
                event["document_class"] = data["document_class"]
            if "is_synthetic" in data:
                event["is_synthetic"] = data["is_synthetic"]

            # ✅ EXTRAER DATOS DE CONVERSACIÓN AL NIVEL RAÍZ
            if "conversacion_humana" in data:
                event["conversacion_humana"] = data["conversacion_humana"]
                logging.info(
                    f"[CONVERSATION] Extrayendo conversacion_humana al nivel raíz: {list(data['conversacion_humana'].keys())}")

            if "es_conversacion_humana" in data:
                event["es_conversacion_humana"] = data["es_conversacion_humana"]
                logging.info(
                    f"[CONVERSATION] Extrayendo es_conversacion_humana: {data['es_conversacion_humana']}")

            # ✅ EXTRAER TEXTO_SEMANTICO AL NIVEL RAÍZ (CRÍTICO)
            if "texto_semantico" in data:
                event["texto_semantico"] = data["texto_semantico"]
                logging.info(
                    f"[SEMANTIC] Extrayendo texto_semantico al nivel raíz: {data['texto_semantico'][:100]}...")

        success_local = self._log_local(event)
        success_cosmos = self._log_cosmos(event)

        return success_local or success_cosmos

    def _log_local(self, event: Dict[str, Any]) -> bool:
        """Escribe en archivo local JSONL"""
        if not self.local_enabled:
            return False

        try:
            with open(self.semantic_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logging.error(f"Error escribiendo log local: {e}")
            return False

    def _log_cosmos(self, event: Dict[str, Any]) -> bool:
        """Escribe en Cosmos DB contenedor memory con clasificación semántica y anti-duplicados"""
        if not self.cosmos_available or not self.memory_container:
            logging.warning("Cosmos DB no disponible para escritura")
            return False

        try:
            # 🚨 PASO 1: GARANTIZAR texto_semantico INMEDIATAMENTE
            # Mover texto_semantico al nivel raíz si está en data
            if "texto_semantico" in event.get("data", {}):
                event["texto_semantico"] = event["data"]["texto_semantico"]
                logging.info(
                    f"[SEMANTIC] Movido texto_semantico de data al nivel raíz")

            # Asegurar que siempre hay texto_semantico en el nivel raíz
            if not event.get("texto_semantico"):
                # Generar uno básico si no existe
                fallback_text = f"Evento {event.get('event_type', 'unknown')} en sesión {event.get('session_id', 'unknown')}"
                event["texto_semantico"] = fallback_text
                logging.warning(
                    f"[WARN] Generando texto_semantico de fallback: {fallback_text}")

            # Asegurar que el evento tiene partition key (session_id)
            if "session_id" not in event:
                event["session_id"] = "fallback_session"

            # Asegurar que el ID es único
            if "id" not in event or not event["id"]:
                event["id"] = f"{event['session_id']}_{event.get('event_type', 'unknown')}_{int(datetime.now(timezone.utc).timestamp())}"

            # BARRERA ANTI-DUPLICADOS: Calcular hash y verificar antes de guardar
            texto_semantico = event.get("texto_semantico", "")
            if texto_semantico:
                import hashlib
                texto_hash = hashlib.sha256(
                    texto_semantico.strip().lower().encode('utf-8')).hexdigest()
                event["texto_hash"] = texto_hash

                # Verificar si ya existe
                if self.existe_texto_en_sesion(event["session_id"], texto_hash):
                    logging.info(
                        f"[SKIP] Texto duplicado detectado en sesión; se omite registro: {event['id']}")
                    return False

            # CLASIFICACIÓN SEMÁNTICA DE ERRORES
            texto = str(texto_semantico).lower()
            if "no such file" in texto or "no se pudo leer" in texto or "archivo no encontrado" in texto:
                event["tipo_error"] = "archivo_no_encontrado"
                event["categoria"] = "error_filesystem"
            elif "estado: desconocido" in texto or "tipo: desconocido" in texto:
                event["tipo_error"] = "recurso_sin_metrica"
                event["categoria"] = "diagnostico_incompleto"
            elif "error" in texto or "fallo" in texto or "failed" in texto:
                event["tipo_error"] = "error_generico"
                event["categoria"] = "error"
            else:
                event["categoria"] = event.get("event_type", "interaccion")

            logging.info(
                f"[COSMOS] Guardando en Cosmos: {event.get('id', 'N/A')} - Session: {event.get('session_id', 'N/A')}")
            logging.info(
                f"[EVENT] Evento: {event.get('event_type', 'unknown')} - Tamaño: {len(str(event))} chars")

            # 🔧 ENRIQUECER texto_semantico con campos técnicos si no fueron agregados antes
            if "🔑" not in event.get("texto_semantico", ""):
                def _extraer_ids_evento(evt):
                    ids = []
                    data = evt.get("data", {})
                    if isinstance(data, dict):
                        for key in ['principalId', 'clientId', 'tenantId', 'subscriptionId']:
                            if data.get(key):
                                ids.append(f"{key}: {data[key]}")
                    return "\n🔑 " + "\n🔑 ".join(ids) if ids else ""

                ids_extra = _extraer_ids_evento(event)
                if ids_extra:
                    texto_actual = event.get("texto_semantico", "")
                    event["texto_semantico"] = texto_actual + ids_extra
                    logging.info(
                        f"🔑 IDs técnicos agregados al evento en _log_cosmos")

            # Clasificación de documento (cognitivo vs sintético/log)
            doc_class_override = event.get("document_class")
            if doc_class_override:
                doc_class = doc_class_override
            else:
                doc_class = self._classify_event(event)
                event["document_class"] = doc_class

            if "is_synthetic" not in event:
                event["is_synthetic"] = doc_class != DOC_CLASS_COGNITIVE
            target_index = COGNITIVE_INDEX_NAME if doc_class == DOC_CLASS_COGNITIVE else LOG_INDEX_NAME
            event["indice_destino"] = target_index

            # Intentar upsert
            result = self.memory_container.upsert_item(event)
            logging.info(
                f"[OK] Guardado exitoso en Cosmos DB - ID: {result.get('id', 'unknown')}")
            # Log detallado del texto semántico
            texto_guardado = event.get('texto_semantico', '')
            logging.info(
                f"[SEMANTIC] Texto semántico guardado (longitud: {len(texto_guardado)}): {texto_guardado[:200]}")

            # Verificar también si está en data
            texto_en_data = event.get('data', {}).get('texto_semantico', '')
            if texto_en_data:
                logging.info(
                    f"[SEMANTIC] Texto semántico también en data: {texto_en_data[:100]}...")

            # INDEXAR AUTOMÁTICAMENTE EN AI SEARCH
            self._indexar_en_ai_search(event)

            return True
        except Exception as e:
            logging.error(f"[ERROR] Error escribiendo en Cosmos memory: {e}")
            logging.error(
                f"[ERROR] Evento que falló: {json.dumps(event, ensure_ascii=False)[:500]}...")
            print(f"DEBUG Cosmos error: {e}")
            print(
                f"DEBUG Event keys: {list(event.keys()) if isinstance(event, dict) else 'not dict'}")
            return False

    def _indexar_en_ai_search(self, event: Dict[str, Any]) -> bool:
        """Indexa automáticamente en AI Search después de guardar en Cosmos"""
        try:
            from endpoints_search_memory import indexar_memoria_endpoint

            # Preparar documento para AI Search
            documento = {
                "id": event.get("id"),
                "session_id": event.get("session_id", "unknown"),
                "agent_id": event.get("agent_id") or event.get("data", {}).get("agent_id", "unknown"),
                "endpoint": event.get("endpoint") or event.get("data", {}).get("endpoint", "unknown"),
                "texto_semantico": event.get("texto_semantico", ""),
                "exito": event.get("data", {}).get("success", True),
                "tipo_interaccion": event.get("tipo") or event.get("event_type", "interaccion"),
                "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "document_class": event.get("document_class", DOC_CLASS_SYSTEM),
                "is_synthetic": event.get("is_synthetic", False)
            }

            # Solo indexar si hay texto semántico válido
            texto_semantico = documento.get("texto_semantico", "")
            if not texto_semantico or len(texto_semantico) < 10:
                logging.info(
                    "[SKIP] Saltando indexación en AI Search: texto semántico vacío o muy corto")
                return False

            # Validar duplicados y calidad ANTES de generar embedding
            texto_sem = documento.get("texto_semantico", "")
            if len(texto_sem) < 10:
                logging.info(
                    f"[SKIP] Texto muy corto, se omite indexación: {len(texto_sem)} chars")
                return False

            if documento["document_class"] == DOC_CLASS_COGNITIVE and self.evento_ya_existe(texto_sem):
                logging.info(
                    f"[SKIP] Duplicado detectado, se omite indexación (sin generar embedding): {documento['id']}")
                return False

            if documento["document_class"] != DOC_CLASS_COGNITIVE:
                logging.info(
                    f"[SKIP] Registro de clase '{documento['document_class']}' no se indexa (solo memoria cognitiva)")
                return False

            target_index = event.get("indice_destino") or COGNITIVE_INDEX_NAME

            # Llamar al indexador con formato correcto
            payload = {"documentos": [documento], "index_name": target_index}
            result = indexar_memoria_endpoint(payload)

            if result.get("exito"):
                logging.info(
                    f"[AI_SEARCH] Indexado automáticamente en AI Search: {documento['id']}")
                return True
            else:
                logging.warning(
                    f"[WARN] Error indexando en AI Search: {result.get('error')}")
                return False

        except Exception as e:
            logging.warning(
                f"[WARN] Error en indexación automática AI Search: {e}")
            # No fallar el guardado en Cosmos si falla la indexación
            return False

    def save_pending_fix(self, fix_data: Dict[str, Any]) -> bool:
        """Guarda fix pendiente en local + Cosmos"""
        return self.log_event("pending_fix", fix_data)

    def log_alert(self, alert_data: Dict[str, Any], run_id: str) -> bool:
        """Registra alerta"""
        return self.log_event("alert", alert_data, session_id=run_id)

    def log_semantic_event(self, event_data: Dict[str, Any]) -> bool:
        """Registra evento semántico general"""
        return self.log_event("semantic", event_data)

    def get_session_history(self, session_id: str, limit: int = 100) -> list:
        """Obtiene historial de sesión, priorizando Redis como caché antes de Cosmos."""
        # Validar session_id para evitar consultas inválidas
        if not session_id or not isinstance(session_id, str) or len(session_id.strip()) == 0:
            logging.warning(
                f"[COSMOS] session_id inválido: {repr(session_id)}")
            return []

        session_id = session_id.strip()

        cache_key = None
        if redis_buffer and getattr(redis_buffer, "is_enabled", False):
            try:
                cache_key = redis_buffer._format_key("historial", session_id)
                cached = redis_buffer._json_get(cache_key)
                if cached:
                    logging.info(
                        f"[CACHE HIT] Historial sesión {session_id}: {len(cached)} items desde Redis")
                    redis_buffer._refresh_ttl(cache_key, "memoria")
                    return cached
            except Exception as e:
                logging.warning(f"[CACHE ERROR] Redis no disponible: {e}")

        if not self.cosmos_available or not self.memory_container:
            return []

        query = "SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c._ts DESC"
        try:
            parameters: List[Dict[str, Any]] = [
                {"name": "@session_id", "value": session_id}]

            logging.debug(
                f"[COSMOS] Ejecutando consulta con session_id: {repr(session_id)}")

            items = list(self.memory_container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit,
                enable_cross_partition_query=True
            ))

            # Guardar en Redis para próximos accesos si está habilitado
            if cache_key and items:
                try:
                    redis_buffer._json_set(
                        cache_key, items, ttl=redis_buffer._get_ttl("memoria"))
                    redis_buffer._emit_cache_event(
                        "write", "memoria", cache_key, {"items": len(items)})
                except Exception as e:
                    logging.debug(
                        f"[CACHE WRITE] No se pudo cachear historial en Redis: {e}", exc_info=True)

            return items
        except Exception as e:
            # Manejo específico para errores de consulta Cosmos DB
            error_msg = str(e)
            if "1004" in error_msg or "400" in error_msg:
                logging.error(
                    f"[COSMOS] Error 400/1004 en consulta historial - session_id: {repr(session_id)}, query: {query}, error: {error_msg}")
            else:
                logging.error(f"[COSMOS] Error consultando historial: {e}")
            return []

    def record_interaction(self, agent_id: str, source: str, input_data: Any, output_data: Any) -> bool:
        """Registra interacción de agente"""
        document = {
            "id": str(uuid.uuid4()),
            "session_id": input_data.get("session_id") or f"agent_{agent_id}_{int(datetime.now(timezone.utc).timestamp())}",
            "agent_id": agent_id,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": input_data.get("endpoint", source),
            "params": input_data,
            # ← Aquí aseguramos que el contenido de output_data se incluya dentro de "data"
            "data": output_data
        }

        success_cosmos = self._log_cosmos(document)
        success_local = self._log_local(document)

        return success_local or success_cosmos

    def registrar_llamada(self, source: str, endpoint: str, method: str, params: Dict[str, Any], response_data: Any, success: bool) -> bool:
        """Método requerido por memory_decorator.py para registrar llamadas a endpoints"""

        logging.warning(
            f"[DEBUG] registrar_llamada - params keys: {list(params.keys())}")
        logging.warning(
            f"[DEBUG] registrar_llamada - headers en memoria: {params.get('headers')}")

        response_dict = response_data if isinstance(
            response_data, dict) else {}

        def _extract_from(source: Any, key: str) -> Optional[str]:
            if not isinstance(source, dict):
                return None
            candidates = [
                key,
                key.replace("_", "-"),
                key.replace("-", "_"),
                key.upper(),
                key.lower(),
                key.title()
            ]
            for candidate in candidates:
                value = source.get(candidate)
                if value:
                    return str(value)
            return None

        headers_info = params.get("headers")
        body_info = params.get("body")
        metadata = response_dict.get("metadata", {}) if isinstance(
            response_dict, dict) else {}
        session_info = metadata.get("session_info", {}) if isinstance(
            metadata, dict) else {}
        contexto_convers = response_dict.get(
            "contexto_conversacion", {}) if isinstance(response_dict, dict) else {}

        session_id = params.get("session_id") or \
            _extract_from(headers_info, "Session-ID") or \
            _extract_from(body_info, "session_id") or \
            _extract_from(response_dict, "session_id") or \
            _extract_from(contexto_convers, "session_id") or \
            _extract_from(session_info, "session_id") or \
            _extract_from(metadata, "session_id")

        agent_id = params.get("agent_id") or \
            _extract_from(headers_info, "Agent-ID") or \
            _extract_from(body_info, "agent_id") or \
            _extract_from(response_dict, "agent_id") or \
            _extract_from(contexto_convers, "agent_id") or \
            _extract_from(session_info, "agent_id") or \
            _extract_from(metadata, "agent_id")

        # Solo generar fallback si no hay session_id
        if not session_id:
            session_id = "fallback_session"
            logging.warning(
                f"[WARN] Session ID no encontrado en params, generando fallback: {session_id}")

        if not agent_id:
            agent_id = "unknown_agent"

        params["session_id"] = session_id
        params["agent_id"] = agent_id

        # DEBUG: Log session info
        logging.info(
            f"[MEMORY] Registrando llamada - Session: {session_id}, Agent: {agent_id}, Source: {source}")        # ✅ Extraer respuesta_usuario antes del truncamiento, para reinyectarlo
        respuesta_usuario_completa = None
        if isinstance(response_data, dict) and response_data.get("respuesta_usuario"):
            respuesta_usuario_completa = str(
                response_data["respuesta_usuario"]).strip()

        # Limpiar response_data para evitar documentos muy grandes
        cleaned_response = response_data
        if isinstance(response_data, dict) and len(str(response_data)) > 2000:
            cleaned_response = {
                "status": "truncated",
                "original_keys": list(response_data.keys()) if isinstance(response_data, dict) else [],
                "success": response_data.get("exito", response_data.get("success", success))
            }
        elif isinstance(response_data, (list, tuple)) and len(str(response_data)) > 2000:
            cleaned_response = {
                "status": "truncated_list",
                "length": len(response_data),
                "success": success
            }

        # ✅ Reinyectar respuesta_usuario si fue eliminado por truncamiento
        if respuesta_usuario_completa:
            if isinstance(cleaned_response, dict):
                cleaned_response["respuesta_usuario"] = respuesta_usuario_completa

        # ✅ Use timezone-aware datetime

        timestamp_utc = datetime.now(timezone.utc).isoformat()

        # Debug params before filtering
        logging.info(
            f"[PARAMS_DEBUG] Original params keys: {list(params.keys())}")
        logging.info(
            f"[PARAMS_DEBUG] thread_id in original: {params.get('thread_id')}")
        logging.info(
            f"[PARAMS_DEBUG] Thread-ID in original: {params.get('Thread-ID')}")

        filtered_params = {k: v for k, v in params.items() if k not in [
            "body"]}
        logging.info(
            f"[PARAMS_DEBUG] Filtered params keys: {list(filtered_params.keys())}")
        logging.info(
            f"[PARAMS_DEBUG] thread_id in filtered: {filtered_params.get('thread_id')}")
        logging.info(
            f"[PARAMS_DEBUG] Thread-ID in filtered: {filtered_params.get('Thread-ID')}")

        llamada_data = {
            "source": source,
            "endpoint": endpoint,
            "method": method,
            # Excluir body grande
            "params": filtered_params,
            "response_data": cleaned_response,
            "success": success,
            "agent_id": agent_id,
            "timestamp": timestamp_utc  # ✅ Updated to use timezone-aware timestamp
        }

        # Conversaciones humanas y contexto de Foundry
        mensaje_usuario = (
            params.get("mensaje_usuario")
            or params.get("mensaje")
            or params.get("query")
            or params.get("consulta")
            or response_dict.get("mensaje_usuario")
            or response_dict.get("mensaje_original")
        )

        mensaje_asistente = None
        if isinstance(response_dict, dict):
            mensaje_asistente = (
                response_dict.get("respuesta_usuario")
                or response_dict.get("texto_semantico")
                or response_dict.get("mensaje_asistente")
            )

        # Capturar thread_id con múltiples variaciones

        # Extract thread_id from various sources - fixed logic
        thread_foundry = None
        if params.get("thread_id"):
            thread_foundry = str(params.get("thread_id")).strip()
        elif params.get("Thread-ID"):
            thread_foundry = str(params.get("Thread-ID")).strip()
        elif response_dict.get("thread_id"):
            thread_foundry = str(response_dict.get("thread_id")).strip()
        elif contexto_convers.get("thread_id"):
            thread_foundry = str(contexto_convers.get("thread_id")).strip()

        # Ensure empty strings become None
        if not thread_foundry:
            thread_foundry = None

        instrucciones_humanas = (
            params.get("instrucciones")
            or response_dict.get("instrucciones_humanas")
            or contexto_convers.get("mensaje")
        )

        contexto_conversacional = contexto_convers or response_dict.get(
            "contexto_inteligente") or {}

        flujo_dialogo: List[Dict[str, Any]] = []
        posibles_interacciones = (
            response_dict.get("interacciones")
            or response_dict.get("extras", {}).get("interacciones")
            or []
        )
        if isinstance(posibles_interacciones, list):
            for item in posibles_interacciones[:10]:
                if isinstance(item, dict):
                    flujo_dialogo.append({
                        "timestamp": item.get("timestamp"),
                        "endpoint": item.get("endpoint"),
                        "texto": item.get("texto_semantico") or item.get("consulta"),
                        "exito": item.get("exito", True)
                    })

        llamada_data["conversacion_humana"] = {
            "mensaje_usuario": mensaje_usuario or "",
            "mensaje_asistente": mensaje_asistente or "",
            "thread_id": thread_foundry or "",
            "contexto_conversacional": contexto_conversacional,
            "instrucciones_humanas": instrucciones_humanas or "",
            "flujo_dialogo": flujo_dialogo
        }
        llamada_data["es_conversacion_humana"] = bool(
            mensaje_usuario or mensaje_asistente)

        # ❌ FILTRAR EVENTOS BASURA: No guardar eventos genéricos sin valor
        if endpoint == "unknown" and not params.get("respuesta_usuario"):
            if isinstance(response_data, dict):
                msg = str(response_data.get("mensaje", ""))
                if "Evento semantic" in msg or not msg.strip():
                    logging.info(
                        "🚫 Evento basura filtrado: sin contenido útil")
                    return False

        # 🔥 DETECTAR EVENTOS REPETITIVOS
        if self._es_evento_repetitivo(endpoint, response_data, session_id):
            llamada_data["es_repetido"] = True
            llamada_data["categoria"] = "repetitivo"
            logging.info(f"🔁 Evento repetitivo detectado: {endpoint}")

        # ✅ ENRIQUECER respuesta_resumen con información valiosa
        respuesta_resumen = None
        if isinstance(response_data, dict):
            # Extraer información útil para resumen
            resumen_parts = []
            if response_data.get("interpretacion_semantica"):
                resumen_parts.append(
                    f"Interpretación: {response_data['interpretacion_semantica'][:200]}")
            if response_data.get("contexto_inteligente", {}).get("resumen_inteligente"):
                resumen_parts.append(
                    f"Contexto: {response_data['contexto_inteligente']['resumen_inteligente'][:200]}")
            if response_data.get("total"):
                resumen_parts.append(
                    f"Total procesado: {response_data['total']}")

            if resumen_parts:
                respuesta_resumen = " | ".join(resumen_parts)
                llamada_data["respuesta_resumen"] = respuesta_resumen
                logging.info(
                    f"📊 Resumen enriquecido: {respuesta_resumen[:100]}...")

        # === EXTRACTOR DE CAMPOS TÉCNICOS ===
        def _extraer_campos_tecnicos(data: Any) -> str:
            """Extrae IDs técnicos (UUIDs, Client ID, etc.) de JSONs para búsqueda literal."""
            campos_extraidos = []

            def _buscar_recursivo(obj, profundidad=0):
                if profundidad > 3:  # Limitar recursión
                    return

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        key_lower = str(key).lower()

                        # Detectar campos de IDs
                        if any(id_key in key_lower for id_key in ['principalid', 'clientid', 'tenantid', 'subscriptionid', 'applicationid', 'resourceid']):
                            if value and isinstance(value, str):
                                # Formatear para búsqueda
                                campo_nombre = key.replace(
                                    '_', ' ').replace('-', ' ').title()
                                campos_extraidos.append(
                                    f"{campo_nombre}: {value}")

                        # Buscar UUIDs en valores
                        if isinstance(value, str) and len(value) == 36 and value.count('-') == 4:
                            import re
                            if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', value, re.IGNORECASE):
                                campo_nombre = key.replace(
                                    '_', ' ').replace('-', ' ').title()
                                campos_extraidos.append(
                                    f"{campo_nombre}: {value}")

                        # Recursión
                        _buscar_recursivo(value, profundidad + 1)

                elif isinstance(obj, (list, tuple)) and profundidad < 2:
                    for item in obj[:5]:  # Limitar a primeros 5 elementos
                        _buscar_recursivo(item, profundidad + 1)

            _buscar_recursivo(data)

            if campos_extraidos:
                # Deduplicar
                campos_unicos = list(dict.fromkeys(campos_extraidos))
                # Máximo 10 campos
                return "\n🔑 " + "\n🔑 ".join(campos_unicos[:10])
            return ""

        def _inferir_tipo_evento(texto_semantico: str) -> str:
            """Deriva la intención real del evento usando clasificador semántico avanzado."""
            # 1️⃣ PRIORIDAD: Tipos explícitos en response_data/params
            explicitos: List[str] = []
            if isinstance(response_data, dict):
                for key in ["tipo", "tipo_evento", "categoria", "category"]:
                    valor = response_data.get(key)
                    if isinstance(valor, str) and valor.strip():
                        explicitos.append(valor.strip().lower())
                metadata_resp = response_data.get("metadata") or {}
                if isinstance(metadata_resp, dict):
                    for key in ["tipo", "categoria"]:
                        valor = metadata_resp.get(key)
                        if isinstance(valor, str) and valor.strip():
                            explicitos.append(valor.strip().lower())
            if isinstance(params, dict):
                valor_param = params.get("tipo")
                if isinstance(valor_param, str) and valor_param.strip():
                    explicitos.append(valor_param.strip().lower())

            for candidato in explicitos:
                if candidato:
                    return candidato

            # 2️⃣ CLASIFICACIÓN SEMÁNTICA PRINCIPAL
            try:
                from semantic_intent_classifier import classify_text

                # Construir texto completo para clasificación
                texto_completo = " ".join(filter(None, [
                    texto_semantico or "",
                    str(response_data.get("respuesta_usuario", "")
                        ) if isinstance(response_data, dict) else "",
                    str(params.get("consulta", "")) if isinstance(
                        params, dict) else "",
                    str(params.get("mensaje", "")) if isinstance(
                        params, dict) else ""
                ])).strip()

                if texto_completo:
                    response_dict_safe = response_data if isinstance(
                        response_data, dict) else {}
                    clasificacion = classify_text(
                        text=texto_completo,
                        endpoint=endpoint or "",
                        response_data=response_dict_safe,
                        success=success
                    )

                    tipo_semantico = clasificacion.get("tipo")
                    confianza = clasificacion.get("confianza", 0.0)
                    metodo = clasificacion.get("metodo", "semantic")

                    # Usar resultado semántico si hay confianza razonable
                    if tipo_semantico and confianza >= 0.4:  # Umbral más bajo para mayor cobertura
                        logging.info(
                            f"[SEMANTIC] Tipo inferido semánticamente: {tipo_semantico} (confianza: {confianza:.2f}, método: {metodo})")
                        return tipo_semantico

            except Exception as e:
                logging.debug(
                    f"Fallback a clasificación por palabras clave: {e}")

            # 3️⃣ FALLBACK MÍNIMO: Solo para casos extremos
            for candidato in explicitos:
                if candidato:
                    return candidato

            # 4️⃣ FALLBACK PALABRAS CLAVE: Definir listas y función auxiliar
            def _contiene(keywords):
                texto_ref = " ".join(filter(None, [
                    texto_semantico or "",
                    endpoint or "",
                    source or "",
                    str(params.get("comando") or ""),
                    str(params.get("consulta") or ""),
                    str(params.get("query") or ""),
                    str(params.get("operacion") or ""),
                    str(response_dict.get("mensaje")) if isinstance(
                        response_dict, dict) and response_dict.get("mensaje") else ""
                ])).lower()
                return any(kw in texto_ref for kw in keywords)

            # Definir listas de palabras clave
            correccion_kw = ["corregir", "reparar", "fix",
                             "arreglar", "aplicar", "correccion"]
            diagnostico_kw = ["diagnostico", "status",
                              "health", "verificar", "comprobar"]
            boat_kw = ["boat", "embarcacion", "reserva",
                       "booking", "alquiler", "rental"]
            archivo_kw = ["archivo", "file",
                          "escribir", "leer", "crear", "eliminar"]
            cli_kw = ["az ", "cli", "comando", "ejecutar"]

            # Clasificación por palabras clave
            if _contiene(correccion_kw):
                return "correccion"
            if not success:
                return "error_endpoint"
            if _contiene(diagnostico_kw):
                return "diagnostico"
            if _contiene(boat_kw):
                return "boat_management"
            if _contiene(archivo_kw):
                return "operacion_archivo"
            if _contiene(cli_kw):
                return "ejecucion_cli"

            # Análisis contextual adicional
            if endpoint and any(word in endpoint.lower() for word in ["boat", "rental", "booking"]):
                return "boat_management"
            if source and "copiloto" in source.lower():
                return "consulta_general"

            return "interaccion"

        # === GENERADOR SEMÁNTICO ENRIQUECIDO ===
        def _construir_texto_semantico_rico(response_data, endpoint, agent_id, success, params):
            """Construye texto semántico útil, contextual y rico como lo haría un asistente inteligente."""

            # 1️⃣ PRIORIDAD MÁXIMA: respuesta_usuario (voz del agente)
            if isinstance(response_data, dict) and response_data.get("respuesta_usuario"):
                return str(response_data["respuesta_usuario"]).strip(), False

            # 2️⃣ Texto semántico explícito del endpoint
            if isinstance(response_data, dict) and response_data.get("texto_semantico"):
                return str(response_data["texto_semantico"]).strip(), False

            # 3️⃣ CONSTRUCCIÓN ENRIQUECIDA: Combinar múltiples fuentes
            if isinstance(response_data, dict):
                bloques = []

                # Mensaje principal
                if response_data.get("mensaje"):
                    msg = str(response_data["mensaje"]).strip()
                    if len(msg) > 50 and "CONSULTA DE HISTORIAL" not in msg:
                        bloques.append(f"MENSAJE: {msg[:400]}")

                # Interpretación semántica
                if response_data.get("interpretacion_semantica"):
                    bloques.append(
                        f"🧠 Interpretación: {response_data['interpretacion_semantica'][:300]}")

                # Contexto inteligente
                ctx = response_data.get("contexto_inteligente", {})
                if ctx.get("resumen_inteligente"):
                    bloques.append(
                        f"📊 Contexto: {ctx['resumen_inteligente'][:300]}")
                elif ctx.get("resumen"):
                    bloques.append(f"📊 {ctx['resumen'][:300]}")

                # Resultados cuantitativos
                if response_data.get("total"):
                    total = response_data["total"]
                    tipo = response_data.get("tipo", "elementos")
                    bloques.append(f"🔢 Procesados: {total} {tipo}")

                # Interacciones o documentos
                if response_data.get("interacciones"):
                    count = len(response_data["interacciones"]) if isinstance(
                        response_data["interacciones"], list) else response_data["interacciones"]
                    bloques.append(f"💾 {count} interacciones recuperadas")

                if response_data.get("documentos_relevantes"):
                    bloques.append(
                        f"📄 {response_data['documentos_relevantes']} documentos relevantes")

                # Acciones sugeridas
                if response_data.get("acciones_sugeridas"):
                    acciones = response_data["acciones_sugeridas"]
                    if isinstance(acciones, list) and acciones:
                        bloques.append(
                            f"🎯 Acciones: {', '.join(acciones[:3])}")

                # Resultado o summary
                if response_data.get("resultado") and isinstance(response_data["resultado"], str):
                    res = response_data["resultado"].strip()
                    if len(res) > 30:
                        bloques.append(f"✅ {res[:300]}")

                if response_data.get("summary"):
                    bloques.append(f"📋 {response_data['summary'][:300]}")

                # Error si existe
                if response_data.get("error"):
                    bloques.append(f"⚠️ Error: {response_data['error'][:200]}")

                # Combinar bloques
                if bloques:
                    return "\n".join(bloques), True

            # 4️⃣ FALLBACK ENRIQUECIDO: Construir desde endpoint y contexto
            endpoint_name = endpoint.split(
                "/")[-1] if "/" in endpoint else endpoint
            endpoint_readable = endpoint_name.replace(
                "-", " ").replace("_", " ").title()

            estado = "✅ exitosa" if success else "❌ fallida"

            # Intentar extraer contexto del params
            contexto_extra = []
            if params.get("query"):
                contexto_extra.append(f"Query: '{params['query'][:100]}'")
            if params.get("session_id"):
                contexto_extra.append(f"Sesión: {params['session_id']}")

            if contexto_extra:
                return f"🔧 {endpoint_readable} {estado} por {agent_id}. {' | '.join(contexto_extra)}", True

            return f"🔧 {endpoint_readable} {estado} por {agent_id}", True

        texto_semantico_final, auto_generated = _construir_texto_semantico_rico(
            response_data, endpoint, agent_id, success, params
        )

        # 🔧 ENRIQUECER con campos técnicos extraídos
        campos_tecnicos = _extraer_campos_tecnicos(response_data)
        if campos_tecnicos:
            texto_semantico_final = f"{texto_semantico_final}\n{campos_tecnicos}"
            logging.info(
                f"🔑 Campos técnicos extraídos y agregados al texto semántico")

        if auto_generated:
            logging.info(
                f"🤖 Texto semántico construido automáticamente: {texto_semantico_final[:100]}...")
        else:
            logging.info(
                f"📝 Texto semántico desde respuesta: {texto_semantico_final[:100]}...")

        # Inyectarlo en el evento
        if texto_semantico_final and len(texto_semantico_final.strip()) > 10:
            llamada_data["texto_semantico"] = texto_semantico_final
            if auto_generated:
                llamada_data["texto_semantico_auto_generated"] = True
        else:
            logging.warning(
                "⚠️ Texto semántico vacío o muy corto, no se guardará.")
            return False  # No guardar eventos sin contenido útil

        tipo_inferido = _inferir_tipo_evento(texto_semantico_final)
        llamada_data["tipo"] = tipo_inferido
        if tipo_inferido == "correccion":
            llamada_data["document_class"] = DOC_CLASS_COGNITIVE
            llamada_data["is_synthetic"] = False

        # Registrar como evento de tipo "endpoint_call" con session_id preservado
        result = self.log_event(
            "endpoint_call", llamada_data, session_id=session_id)
        logging.info(
            f"💾 Guardado en memoria: {'✅' if result else '❌'} - Session: {session_id}")
        return result

    def obtener_estadisticas(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de memoria"""
        try:
            if not self.cosmos_available or not self.memory_container:
                return {
                    "total_llamadas": 0,
                    "llamadas_exitosas": 0,
                    "llamadas_fallidas": 0,
                    "fuentes_activas": [],
                    "ultimo_registro": None,
                    "servicio": "local_only"
                }

            # Consultar estadísticas desde Cosmos DB
            query = "SELECT * FROM c WHERE c.event_type = 'endpoint_call'"
            params: List[Dict[str, Any]] = []

            if source_name:
                query += " AND c.data.source = @source_name"
                params.append({"name": "@source_name", "value": source_name})

            items = list(self.memory_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))

            # Calcular estadísticas
            total = len(items)
            exitosas = sum(1 for item in items if item.get(
                "data", {}).get("success", False))
            fallidas = total - exitosas

            fuentes = list(set(item.get("data", {}).get(
                "source", "unknown") for item in items))
            ultimo = max(items, key=lambda x: x.get(
                "timestamp", ""), default=None)

            return {
                "total_llamadas": total,
                "llamadas_exitosas": exitosas,
                "llamadas_fallidas": fallidas,
                "fuentes_activas": fuentes,
                "ultimo_registro": ultimo.get("timestamp") if ultimo else None,
                "servicio": "cosmos_db"
            }

        except Exception as e:
            logging.error(f"Error obteniendo estadísticas: {e}")
            return {
                "error": str(e),
                "servicio": "error"
            }

    def limpiar_registros(self, source_name: Optional[str] = None) -> bool:
        """Limpia registros de memoria"""
        try:
            if not self.cosmos_available or not self.memory_container:
                # Limpiar archivo local
                if self.semantic_log_file.exists():
                    self.semantic_log_file.unlink()
                    logging.info("🧹 Archivo local de memoria limpiado")
                return True

            # Consultar elementos a eliminar
            query = "SELECT c.id, c.session_id FROM c WHERE c.event_type = 'endpoint_call'"
            params: List[Dict[str, Any]] = []

            if source_name:
                query += " AND c.data.source = @source_name"
                params.append({"name": "@source_name", "value": source_name})

            items = list(self.memory_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))

            # Eliminar elementos
            deleted_count = 0
            for item in items:
                try:
                    self.memory_container.delete_item(
                        item["id"],
                        partition_key=item["session_id"]
                    )
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"Error eliminando item {item['id']}: {e}")

            logging.info(f"🧹 Limpiados {deleted_count} registros de memoria")
            return deleted_count > 0

        except Exception as e:
            logging.error(f"Error limpiando memoria: {e}")
            return False

    def _classify_event(self, event: Dict[str, Any]) -> str:
        """Determina la clase de documento para evitar contaminar la memoria cognitiva."""
        event_type = str(event.get("event_type")
                         or event.get("tipo") or "").lower()
        endpoint_raw = str(event.get("endpoint") or event.get(
            "data", {}).get("endpoint", "")).lower()
        endpoint = endpoint_raw.replace("_", "-")

        if event.get("data", {}).get("from_historial"):
            return DOC_CLASS_SYNTHETIC

        if event_type in SYNTHETIC_EVENT_TYPES:
            return DOC_CLASS_SYNTHETIC

        if endpoint in SYSTEM_ENDPOINTS:
            return DOC_CLASS_SYSTEM

        if any(keyword in endpoint for keyword in SYSTEM_ENDPOINT_KEYWORDS):
            return DOC_CLASS_SYSTEM

        if "historial" in endpoint or "copiloto" in endpoint:
            return DOC_CLASS_SYSTEM

        return DOC_CLASS_COGNITIVE

    def existe_texto_en_sesion(self, session_id: str, texto_hash: str) -> bool:
        """Verifica si un texto_hash ya existe en la sesión (barrera anti-duplicados)"""
        try:
            if not self.cosmos_available or not self.memory_container:
                return False

            query = "SELECT TOP 1 c.id FROM c WHERE c.session_id = @session_id AND c.texto_hash = @hash"
            parameters: List[Dict[str, Any]] = [
                {"name": "@session_id", "value": session_id},
                {"name": "@hash", "value": texto_hash}
            ]
            items = list(self.memory_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            return len(items) > 0
        except Exception as e:
            logging.warning(f"Error verificando duplicado por hash: {e}")
            return False

    def _es_evento_repetitivo(self, endpoint: str, response_data: Any, session_id: str, ventana: int = 5) -> bool:
        """Detecta si el mismo endpoint se ejecutó recientemente con respuesta similar"""
        try:
            if not self.cosmos_available or not self.memory_container:
                return False

            query = f"SELECT TOP {ventana} * FROM c WHERE c.session_id = @session_id AND c.data.endpoint = @endpoint ORDER BY c.timestamp DESC"
            parameters: List[Dict[str, Any]] = [
                {"name": "@session_id", "value": session_id},
                {"name": "@endpoint", "value": endpoint}
            ]
            items = list(self.memory_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if len(items) >= 3:
                return True
            return False
        except:
            return False

    def evento_ya_existe(self, texto_semantico: str) -> bool:
        """Verifica si un evento con texto similar ya existe en AI Search."""
        try:
            from services.azure_search_client import get_search_service
            search_service = get_search_service()

            resultados = search_service.search(
                query=texto_semantico, top=1).get("documentos", [])
            if resultados and len(resultados) > 0:
                score = resultados[0].get("@search.score", 0)
                if score > 0.95:
                    logging.info(f"Duplicado detectado: score={score:.3f}")
                    return True
            return False
        except Exception as e:
            logging.warning(f"Error verificando duplicados: {e}")
            return False


# Instancia global
memory_service = MemoryService()
