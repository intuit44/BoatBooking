#!/usr/bin/env python3
"""
Middleware de Continuidad Conversacional

Este middleware automáticamente inyecta contexto conversacional desde Redis
en las consultas de los agentes, proporcionando verdadera continuidad sin necesidad
de que el agente invoque herramientas explícitas.

🎯 Objetivo: Hacer que los agentes respondan como si "recordaran" conversaciones anteriores
📌 Uso: Se integra con memory_route_wrapper para inyección transparente de contexto

Características:
✅ Inyección automática del contexto de thread:* desde Redis
✅ Aplicación silenciosa de memoria semántica memoria:*
✅ Construcción inteligente de prompts con continuidad
✅ Zero-configuration para los agentes
✅ Respuestas naturales con referencias al historial previo
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from services.redis_buffer_service import redis_buffer

# Configuración del middleware
MAX_CONTEXT_MESSAGES = 15  # Máximo número de mensajes previos a incluir
MIN_MESSAGE_LENGTH = 10    # Longitud mínima para considerar un mensaje relevante
MAX_CONTEXT_CHARS = 4000   # Límite de caracteres para el contexto inyectado
SIMILARITY_THRESHOLD = 0.3  # Umbral de similitud para memoria semántica


class ConversationalContinuityMiddleware:
    """
    Middleware que proporciona continuidad conversacional automática
    inyectando contexto desde Redis de forma transparente.
    """

    def __init__(self):
        self.redis_client = redis_buffer

    def inject_conversational_context(self, user_message: str, session_id: str,
                                      agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Inyecta contexto conversacional automáticamente desde Redis.

        Args:
            user_message: Mensaje actual del usuario
            session_id: ID de la sesión
            agent_id: ID del agente (opcional)

        Returns:
            Dict con contexto enriquecido para inyectar en el prompt
        """
        try:
            # 1. 🧵 RECUPERAR HISTORIAL DE CONVERSACIÓN (thread:*)
            thread_context = self._get_thread_context(session_id)

            # 2. 🧠 RECUPERAR MEMORIA SEMÁNTICA (memoria:*)
            semantic_context = self._get_semantic_context(
                user_message, session_id)

            # 3. 🔍 BÚSQUEDA DE CONTEXTO RELEVANTE (search:*)
            search_context = self._get_search_context(user_message, session_id)

            # 4. 🎯 CONSTRUIR CONTEXTO FINAL OPTIMIZADO
            enriched_context = self._build_enriched_context(
                user_message=user_message,
                thread_context=thread_context,
                semantic_context=semantic_context,
                search_context=search_context,
                session_id=session_id,
                agent_id=agent_id
            )

            # 5. 📊 LOGGING PARA DEBUGGING
            self._log_context_injection(enriched_context, session_id)

            return enriched_context

        except Exception as e:
            logging.error(
                f"❌ [ConversationalMiddleware] Error inyectando contexto: {e}")
            return {
                "has_context": False,
                "context_summary": "No se pudo recuperar contexto previo",
                "error": str(e)
            }

    def _get_thread_context(self, session_id: str) -> Dict[str, Any]:
        """Recupera el historial de conversación desde thread:*"""
        try:
            # Buscar todas las claves de thread para la sesión
            thread_pattern = f"thread:{session_id}:*"
            thread_keys = self.redis_client.keys(thread_pattern)

            if not thread_keys:
                return {"messages": [], "has_history": False}

            messages = []
            for key in thread_keys[-MAX_CONTEXT_MESSAGES:]:  # Últimos N mensajes
                try:
                    thread_data = self.redis_client.get(
                        key.decode() if isinstance(key, bytes) else key)
                    if thread_data:
                        msg_data = json.loads(thread_data) if isinstance(
                            thread_data, str) else thread_data

                        # Extraer información relevante
                        if isinstance(msg_data, dict):
                            message_text = (
                                msg_data.get("texto_semantico") or
                                msg_data.get("message") or
                                msg_data.get("response") or
                                str(msg_data)
                            )

                            if message_text and len(message_text) >= MIN_MESSAGE_LENGTH:
                                messages.append({
                                    "timestamp": msg_data.get("timestamp", ""),
                                    "type": msg_data.get("event_type", "message"),
                                    # Truncar mensajes largos
                                    "content": message_text[:500],
                                    "agent_id": msg_data.get("agent_id", ""),
                                    "success": msg_data.get("exito", True)
                                })
                except Exception as e:
                    logging.debug(f"Error procesando thread key {key}: {e}")
                    continue

            # Ordenar por timestamp
            messages.sort(key=lambda x: x.get("timestamp", ""))

            return {
                "messages": messages,
                "has_history": len(messages) > 0,
                "total_messages": len(messages),
                "thread_keys_found": len(thread_keys)
            }

        except Exception as e:
            logging.error(f"❌ Error recuperando thread context: {e}")
            return {"messages": [], "has_history": False, "error": str(e)}

    def _get_semantic_context(self, user_message: str, session_id: str) -> Dict[str, Any]:
        """Recupera memoria semántica relevante desde memoria:*"""
        try:
            # Buscar claves de memoria
            memory_pattern = f"memoria:*"
            memory_keys = self.redis_client.keys(memory_pattern)

            if not memory_keys:
                return {"relevant_memory": [], "has_semantic_memory": False}

            relevant_memories = []
            user_message_lower = user_message.lower()

            for key in memory_keys[-20:]:  # Revisar últimas 20 memorias
                try:
                    memory_data = self.redis_client.get(
                        key.decode() if isinstance(key, bytes) else key)
                    if memory_data:
                        mem_data = json.loads(memory_data) if isinstance(
                            memory_data, str) else memory_data

                        if isinstance(mem_data, dict):
                            # Verificar relevancia del contenido
                            content = (
                                mem_data.get("content") or
                                mem_data.get("texto_semantico") or
                                mem_data.get("summary") or
                                str(mem_data)
                            )

                            # Simple relevancia por palabras clave
                            if self._is_content_relevant(content, user_message_lower):
                                relevant_memories.append({
                                    "content": content[:300],  # Truncar
                                    "timestamp": mem_data.get("timestamp", ""),
                                    "relevance": "keyword_match",
                                    "key": key.decode() if isinstance(key, bytes) else key
                                })

                except Exception as e:
                    logging.debug(f"Error procesando memory key {key}: {e}")
                    continue

            return {
                # Top 5 más relevantes
                "relevant_memory": relevant_memories[:5],
                "has_semantic_memory": len(relevant_memories) > 0,
                "total_memories_checked": len(memory_keys)
            }

        except Exception as e:
            logging.error(f"❌ Error recuperando semantic context: {e}")
            return {"relevant_memory": [], "has_semantic_memory": False, "error": str(e)}

    def _get_search_context(self, user_message: str, session_id: str) -> Dict[str, Any]:
        """Recupera contexto de búsquedas previas desde search:*"""
        try:
            search_pattern = f"search:*"
            search_keys = self.redis_client.keys(search_pattern)

            if not search_keys:
                return {"search_results": [], "has_search_history": False}

            relevant_searches = []
            user_message_lower = user_message.lower()

            for key in search_keys[-10:]:  # Últimas 10 búsquedas
                try:
                    search_data = self.redis_client.get(
                        key.decode() if isinstance(key, bytes) else key)
                    if search_data:
                        search_obj = json.loads(search_data) if isinstance(
                            search_data, str) else search_data

                        if isinstance(search_obj, dict):
                            query = search_obj.get("query", "")
                            results = search_obj.get("results", [])

                            # Verificar si la búsqueda es relevante para la consulta actual
                            if self._is_content_relevant(query, user_message_lower):
                                relevant_searches.append({
                                    "query": query,
                                    "results_count": len(results) if isinstance(results, list) else 0,
                                    "timestamp": search_obj.get("timestamp", ""),
                                    "key": key.decode() if isinstance(key, bytes) else key
                                })

                except Exception as e:
                    logging.debug(f"Error procesando search key {key}: {e}")
                    continue

            return {
                # Top 3 búsquedas relevantes
                "search_results": relevant_searches[:3],
                "has_search_history": len(relevant_searches) > 0,
                "total_searches_checked": len(search_keys)
            }

        except Exception as e:
            logging.error(f"❌ Error recuperando search context: {e}")
            return {"search_results": [], "has_search_history": False, "error": str(e)}

    def _is_content_relevant(self, content: str, user_message_lower: str) -> bool:
        """Determina si el contenido es relevante para el mensaje del usuario"""
        if not content or not user_message_lower:
            return False

        content_lower = content.lower()

        # CRITERIOS MÁS PERMISIVOS para evitar descartar memoria válida

        # 1. Siempre incluir si el contenido es sustancial (>50 chars)
        if len(content.strip()) > 50:
            return True

        # 2. Buscar palabras clave técnicas comunes
        technical_keywords = ['redis', 'cache', 'memoria', 'context',
                              'session', 'agente', 'agent', 'copiloto', 'foundry']
        if any(keyword in content_lower or keyword in user_message_lower for keyword in technical_keywords):
            return True

        # 3. Extraer palabras clave significativas (>2 caracteres, umbral más bajo)
        user_keywords = [
            word for word in user_message_lower.split() if len(word) > 2]

        # Verificar si hay coincidencias de palabras clave
        matches = sum(
            1 for keyword in user_keywords if keyword in content_lower)

        # UMBRAL MÁS PERMISIVO: Es relevante si tiene al menos 1 coincidencia
        # O si ambos contenidos son cortos (probablemente relevantes)
        threshold = 1 if len(user_keywords) <= 5 else 2
        if matches >= threshold:
            return True

        # 4. Si ambos mensajes son cortos, probablemente están relacionados
        if len(user_message_lower) < 50 and len(content) < 100:
            return True

        return False

    def _build_enriched_context(self, user_message: str, thread_context: Dict[str, Any],
                                semantic_context: Dict[str, Any], search_context: Dict[str, Any],
                                session_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Construye el contexto enriquecido final para inyectar en el prompt"""

        # Construir resumen narrativo del contexto
        context_summary = []

        # 1. Historial de conversación
        if thread_context.get("has_history"):
            messages = thread_context.get("messages", [])
            if messages:
                context_summary.append(
                    f"🧵 CONTINUIDAD: Esta conversación tiene {len(messages)} intercambios previos.")

                # Agregar los últimos 3 mensajes más relevantes
                recent_messages = messages[-3:] if len(
                    messages) > 3 else messages

                # LOG DETALLADO para debugging
                logging.info(
                    f"🔍 [ContextBuilder] Processing {len(recent_messages)} recent messages")

                for i, msg in enumerate(recent_messages):
                    if msg.get("content"):
                        snippet = msg["content"][:150] + \
                            ("..." if len(msg["content"]) > 150 else "")
                        context_summary.append(f"• Anterior: {snippet}")
                        logging.debug(f"   Message {i+1}: {snippet[:50]}...")
                    else:
                        logging.debug(f"   Message {i+1}: Sin contenido")

        # 2. Memoria semántica
        if semantic_context.get("has_semantic_memory"):
            memories = semantic_context.get("relevant_memory", [])
            if memories:
                context_summary.append(
                    f"🧠 MEMORIA: Tienes {len(memories)} recuerdos relevantes sobre este tema.")

                # LOG DETALLADO para debugging
                logging.info(
                    f"🔍 [ContextBuilder] Processing {len(memories)} semantic memories")

                for i, mem in enumerate(memories[:2]):  # Top 2 memorias
                    if mem.get("content"):
                        snippet = mem["content"][:100] + \
                            ("..." if len(mem["content"]) > 100 else "")
                        context_summary.append(f"• Recuerdo: {snippet}")
                        logging.debug(f"   Memory {i+1}: {snippet[:50]}...")
                    else:
                        logging.debug(f"   Memory {i+1}: Sin contenido")

        # 3. Historial de búsquedas
        if search_context.get("has_search_history"):
            searches = search_context.get("search_results", [])
            if searches:
                context_summary.append(
                    f"🔍 BÚSQUEDAS: Has realizado {len(searches)} búsquedas relacionadas.")
                for search in searches[:2]:  # Top 2 búsquedas
                    if search.get("query"):
                        context_summary.append(
                            f"• Búsqueda previa: {search['query']}")

        # Construir el contexto conversacional para inyección
        conversational_prompt = ""
        # CRITERIO MÁS PERMISIVO: incluir contexto si hay AL MENOS 1 elemento relevante
        has_meaningful_context = len(context_summary) >= 1

        if has_meaningful_context:
            conversational_prompt = """
🔄 CONTEXTO CONVERSACIONAL (usar sutilmente en tu respuesta):

""" + "\n".join(context_summary) + """

📋 INSTRUCCIONES PARA LA RESPUESTA:
• Si hay intercambios previos, puedes referenciarlos naturalmente ("Como mencioné antes...", "Continuando con lo que hablábamos...", etc.)
• Si hay memoria relevante, úsala para enriquecer tu respuesta sin hacerlo explícito
• Mantén un tono conversacional que refleje continuidad sin sonar robótico
• NO menciones que tienes "memoria" o "contexto" - simplemente úsalo naturalmente

"""

        return {
            "has_context": has_meaningful_context,
            "context_summary": "\n".join(context_summary),
            "conversational_prompt": conversational_prompt,
            "thread_stats": thread_context,
            "semantic_stats": semantic_context,
            "search_stats": search_context,
            "injection_timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "agent_id": agent_id or "unknown"
        }

    def _log_context_injection(self, enriched_context: Dict[str, Any], session_id: str):
        """Registra la inyección de contexto para debugging"""
        try:
            has_context = enriched_context.get("has_context", False)
            thread_messages = enriched_context.get(
                "thread_stats", {}).get("total_messages", 0)
            semantic_memories = len(enriched_context.get(
                "semantic_stats", {}).get("relevant_memory", []))
            search_results = len(enriched_context.get(
                "search_stats", {}).get("search_results", []))

            logging.info(
                f"🔄 [ConversationalContinuity] Session: {session_id[:8]}... | "
                f"Context: {'YES' if has_context else 'NO'} | "
                f"Thread: {thread_messages} msgs | "
                f"Memory: {semantic_memories} items | "
                f"Search: {search_results} results"
            )

            # Log detallado en debug
            if has_context and logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
                logging.debug(
                    f"📝 Context injected: {enriched_context.get('context_summary', '')[:200]}...")

        except Exception as e:
            logging.debug(f"Error logging context injection: {e}")


# Instancia global del middleware
conversational_continuity = ConversationalContinuityMiddleware()


def inject_conversational_context(user_message: str, session_id: str,
                                  agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Función helper para inyectar contexto conversacional.
    Diseñada para ser llamada desde memory_route_wrapper.
    """
    return conversational_continuity.inject_conversational_context(
        user_message=user_message,
        session_id=session_id,
        agent_id=agent_id
    )


def build_context_enriched_prompt(original_prompt: str, user_message: str,
                                  session_id: str, agent_id: Optional[str] = None) -> str:
    """
    Construye un prompt enriquecido con contexto conversacional.

    Args:
        original_prompt: Prompt original del usuario
        user_message: Mensaje del usuario
        session_id: ID de sesión
        agent_id: ID del agente

    Returns:
        Prompt enriquecido con contexto conversacional inyectado
    """
    try:
        # Inyectar contexto conversacional
        context = inject_conversational_context(
            user_message, session_id, agent_id)

        if context.get("has_context", False):
            conversational_prompt = context.get("conversational_prompt", "")

            # Construir prompt enriquecido
            enriched_prompt = f"""{conversational_prompt}

🎯 CONSULTA ACTUAL DEL USUARIO:
{original_prompt}

---
Responde de manera natural, integrando el contexto conversacional cuando sea relevante."""

            return enriched_prompt
        else:
            # No hay contexto suficiente, devolver prompt original
            return original_prompt

    except Exception as e:
        logging.error(f"❌ Error construyendo prompt enriquecido: {e}")
        return original_prompt  # Fallback seguro


def get_context_stats(session_id: str) -> Dict[str, Any]:
    """Obtiene estadísticas del contexto conversacional para debugging"""
    try:
        context = inject_conversational_context("test", session_id)
        return {
            "has_context": context.get("has_context", False),
            "thread_messages": context.get("thread_stats", {}).get("total_messages", 0),
            "semantic_memories": len(context.get("semantic_stats", {}).get("relevant_memory", [])),
            "search_results": len(context.get("search_stats", {}).get("search_results", [])),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"error": str(e), "has_context": False}
