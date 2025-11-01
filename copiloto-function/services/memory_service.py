import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from services.cosmos_store import CosmosMemoryStore
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
        timestamp = datetime.utcnow().isoformat()
        session_id = session_id or f"session_{int(datetime.utcnow().timestamp())}"
        
        # Estructura unificada
        event = {
            "id": f"{session_id}_{event_type}_{int(datetime.utcnow().timestamp())}",
            "session_id": session_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }
        
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
        """Escribe en Cosmos DB contenedor memory"""
        if not self.cosmos_available or not self.memory_container:
            logging.warning("Cosmos DB no disponible para escritura")
            return False
        
        try:
            # Asegurar que el evento tiene partition key (session_id)
            if "session_id" not in event:
                event["session_id"] = f"fallback_{int(datetime.utcnow().timestamp())}"
            
            # Asegurar que el ID es único
            if "id" not in event or not event["id"]:
                event["id"] = f"{event['session_id']}_{event.get('event_type', 'unknown')}_{int(datetime.utcnow().timestamp())}"
            
            logging.info(f"💾 Guardando en Cosmos: {event.get('id', 'N/A')} - Session: {event.get('session_id', 'N/A')}")
            logging.info(f"📄 Evento: {event.get('event_type', 'unknown')} - Tamaño: {len(str(event))} chars")
            
            # Mover texto_semantico al nivel raíz si está en data
            if "texto_semantico" in event.get("data", {}):
                event["texto_semantico"] = event["data"]["texto_semantico"]
                logging.info(f"📝 Moviendo texto_semantico al nivel raíz: {event['texto_semantico'][:100]}...")
            
            # Asegurar que siempre hay texto_semantico en el nivel raíz
            if not event.get("texto_semantico"):
                # Generar uno básico si no existe
                event["texto_semantico"] = f"Evento {event.get('event_type', 'unknown')} en sesión {event.get('session_id', 'unknown')}"
                logging.warning(f"⚠️ Generando texto_semantico de fallback: {event['texto_semantico']}")
            
            # Intentar upsert
            result = self.memory_container.upsert_item(event)
            logging.info(f"✅ Guardado exitoso en Cosmos DB - ID: {result.get('id', 'unknown')}")
            # Log detallado del texto semántico
            texto_guardado = event.get('texto_semantico', '')
            logging.info(f"🧠 Texto semántico guardado (longitud: {len(texto_guardado)}): {texto_guardado[:200]}")
            
            # Verificar también si está en data
            texto_en_data = event.get('data', {}).get('texto_semantico', '')
            if texto_en_data:
                logging.info(f"📄 Texto semántico también en data: {texto_en_data[:100]}...")
            
            # 🔥 INDEXAR AUTOMÁTICAMENTE EN AI SEARCH
            self._indexar_en_ai_search(event)
            
            return True
        except Exception as e:
            logging.error(f"❌ Error escribiendo en Cosmos memory: {e}")
            logging.error(f"📄 Evento que falló: {json.dumps(event, ensure_ascii=False)[:500]}...")
            print(f"DEBUG Cosmos error: {e}")
            print(f"DEBUG Event keys: {list(event.keys()) if isinstance(event, dict) else 'not dict'}")
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
                "endpoint": event.get("data", {}).get("endpoint", "unknown"),
                "texto_semantico": event.get("texto_semantico", ""),
                "exito": event.get("data", {}).get("success", True),
                "tipo": event.get("event_type", "interaccion"),
                "timestamp": event.get("timestamp", datetime.utcnow().isoformat())
            }
            
            # Solo indexar si hay texto semántico válido
            if not documento["texto_semantico"] or len(documento["texto_semantico"]) < 10:
                logging.info("⏭️ Saltando indexación en AI Search: texto semántico vacío o muy corto")
                return False
            
            # Llamar al indexador con formato correcto
            payload = {"documentos": [documento]}
            result = indexar_memoria_endpoint(payload)
            
            if result.get("exito"):
                logging.info(f"🔍 Indexado automáticamente en AI Search: {documento['id']}")
                return True
            else:
                logging.warning(f"⚠️ Error indexando en AI Search: {result.get('error')}")
                return False
                
        except Exception as e:
            logging.warning(f"⚠️ Error en indexación automática AI Search: {e}")
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
        """Obtiene historial de sesión desde Cosmos"""
        if not self.cosmos_available or not self.memory_container:
            return []
        
        try:
            query = "SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c._ts DESC"
            items = list(self.memory_container.query_items(
                query,
                parameters=[{"name": "@session_id", "value": session_id}],
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logging.error(f"Error consultando historial: {e}")
            return []
    
    def record_interaction(self, agent_id: str, source: str, input_data: Any, output_data: Any) -> bool:
        """Registra interacción de agente"""
        document = {
            "id": str(uuid.uuid4()),
            "session_id": input_data.get("session_id") or f"agent_{agent_id}_{int(datetime.utcnow().timestamp())}",
            "agent_id": agent_id,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": input_data.get("endpoint", source),
            "params": input_data,
            "data": output_data  # ← Aquí aseguramos que el contenido de output_data se incluya dentro de "data"
        }
        
        success_cosmos = self._log_cosmos(document)
        success_local = self._log_local(document)
        
        return success_local or success_cosmos
    
    def registrar_llamada(self, source: str, endpoint: str, method: str, params: Dict[str, Any], response_data: Any, success: bool) -> bool:
        """Método requerido por memory_decorator.py para registrar llamadas a endpoints"""
        
        logging.warning(f"🧩 DEBUG registrar_llamada - params keys: {list(params.keys())}")
        logging.warning(f"🧩 DEBUG registrar_llamada - headers en memoria: {params.get('headers')}")
        
        # Extraer session_id y agent_id de params - PRIORIZAR LOS PRESERVADOS
        session_id = params.get("session_id")
        agent_id = params.get("agent_id")
        
        # Solo generar fallback si no hay session_id
        if not session_id:
            import time
            session_id = "constant-session-id"
            logging.warning(f"⚠️ Session ID no encontrado en params, generando fallback: {session_id}")
        
        if not agent_id:
            agent_id = "unknown_agent"
        
        # DEBUG: Log session info
        logging.info(f"📝 Registrando llamada - Session: {session_id}, Agent: {agent_id}, Source: {source}")
        
        # ✅ Extraer respuesta_usuario antes del truncamiento, para reinyectarlo
        respuesta_usuario_completa = None
        if isinstance(response_data, dict) and response_data.get("respuesta_usuario"):
            respuesta_usuario_completa = str(response_data["respuesta_usuario"]).strip()
        
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
        
        llamada_data = {
            "source": source,
            "endpoint": endpoint,
            "method": method,
            "params": {k: v for k, v in params.items() if k not in ["body"]},  # Excluir body grande
            "response_data": cleaned_response,
            "success": success,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # ❌ FILTRAR EVENTOS BASURA: No guardar eventos genéricos sin valor
        if endpoint == "unknown" and not params.get("respuesta_usuario"):
            # Evento genérico sin contenido útil
            if isinstance(response_data, dict):
                msg = str(response_data.get("mensaje", ""))
                if "Evento semantic" in msg or not msg.strip():
                    logging.info("🚫 Evento basura filtrado: sin contenido útil")
                    return False  # No guardar
        
        # ✅ ENRIQUECER respuesta_resumen con información valiosa
        respuesta_resumen = None
        if isinstance(response_data, dict):
            # Extraer información útil para resumen
            resumen_parts = []
            if response_data.get("interpretacion_semantica"):
                resumen_parts.append(f"Interpretación: {response_data['interpretacion_semantica'][:200]}")
            if response_data.get("contexto_inteligente", {}).get("resumen_inteligente"):
                resumen_parts.append(f"Contexto: {response_data['contexto_inteligente']['resumen_inteligente'][:200]}")
            if response_data.get("total"):
                resumen_parts.append(f"Total procesado: {response_data['total']}")
            
            if resumen_parts:
                respuesta_resumen = " | ".join(resumen_parts)
                llamada_data["respuesta_resumen"] = respuesta_resumen
                logging.info(f"📊 Resumen enriquecido: {respuesta_resumen[:100]}...")
        
        # Crear texto semántico ENRIQUECIDO
        texto_semantico_final = None
        auto_generated = False

        # 1) Preferir respuesta_usuario si viene en response_data
        if isinstance(response_data, dict) and response_data.get("respuesta_usuario"):
            texto_semantico_final = str(response_data.get("respuesta_usuario")).strip()
            logging.info("📝 Usando 'respuesta_usuario' desde response_data como texto_semantico.")
        # 2) Luego preferir texto_semantico provisto por el servicio
        elif isinstance(response_data, dict) and response_data.get("texto_semantico"):
            texto_semantico_final = str(response_data.get("texto_semantico")).strip()
            logging.info("📝 Usando 'texto_semantico' desde response_data como texto_semantico.")
        # 3) Luego preferir un campo summary o summary_text
        elif isinstance(response_data, dict) and (response_data.get("summary") or response_data.get("summary_text")):
            texto_semantico_final = str(response_data.get("summary") or response_data.get("summary_text")).strip()
            logging.info("📝 Usando 'summary' desde response_data como texto_semantico.")
        # 4) Si params contiene un mensaje del usuario, usarlo
        elif params.get("user_message"):
            texto_semantico_final = str(params.get("user_message")).strip()
            logging.info("📝 Usando 'user_message' desde params como texto_semantico.")
        # 5) Si response_data es texto plano, usarlo (truncado)
        elif isinstance(response_data, str) and response_data.strip():
            texto_semantico_final = response_data.strip()[:1000]
            logging.info("📝 Usando texto plano de response_data como texto_semantico (truncado).")
        # 6) Generar un resumen ENRIQUECIDO (no genérico)
        else:
            auto_generated = True
            # Intentar extraer información útil
            if isinstance(response_data, dict):
                partes = []
                if response_data.get("mensaje"):
                    partes.append(str(response_data["mensaje"])[:300])
                if response_data.get("interpretacion_semantica"):
                    partes.append(f"Interpretación: {response_data['interpretacion_semantica'][:200]}")
                if response_data.get("total"):
                    partes.append(f"Total: {response_data['total']}")
                
                if partes:
                    texto_semantico_final = " | ".join(partes)
                else:
                    texto_semantico_final = f"Interacción en '{endpoint}' por {agent_id}. Éxito: {'sí' if success else 'no'}."
            else:
                texto_semantico_final = f"Interacción en '{endpoint}' por {agent_id}. Éxito: {'sí' if success else 'no'}."
            
            logging.warning("⚠️ Texto semántico autogenerado (enriquecido).")
        
        # Inyectarlo en el evento
        if texto_semantico_final and len(texto_semantico_final.strip()) > 10:
            llamada_data["texto_semantico"] = texto_semantico_final
            if auto_generated:
                llamada_data["texto_semantico_auto_generated"] = True
        else:
            logging.warning("⚠️ Texto semántico vacío o muy corto, no se guardará.")
            return False  # No guardar eventos sin contenido útil
        
        # Registrar como evento de tipo "endpoint_call" con session_id preservado
        result = self.log_event("endpoint_call", llamada_data, session_id=session_id)
        logging.info(f"💾 Guardado en memoria: {'✅' if result else '❌'} - Session: {session_id}")
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
            params = []
            
            if source_name:
                query += " AND c.data.source = @source_name"
                params.append({"name": "@source_name", "value": source_name})
            
            items = list(self.memory_container.query_items(
                query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            # Calcular estadísticas
            total = len(items)
            exitosas = sum(1 for item in items if item.get("data", {}).get("success", False))
            fallidas = total - exitosas
            
            fuentes = list(set(item.get("data", {}).get("source", "unknown") for item in items))
            ultimo = max(items, key=lambda x: x.get("timestamp", ""), default=None)
            
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
            params = []
            
            if source_name:
                query += " AND c.data.source = @source_name"
                params.append({"name": "@source_name", "value": source_name})
            
            items = list(self.memory_container.query_items(
                query,
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

# Instancia global
memory_service = MemoryService()