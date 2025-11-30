#!/usr/bin/env python3
"""
Pre-Response Intelligence Interceptor

Este módulo intercepta TODAS las consultas del usuario ANTES de que el modelo responda,
sin depender de que se invoquen endpoints. Reutiliza toda la lógica existente de:
- Continuidad conversacional (Redis)
- Búsqueda semántica (AI Search)  
- Validación de GitHub
- Cache de contexto

🎯 OBJETIVO: Zero-duplication, máxima reutilización de lógica existente
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

# Reutilizar módulos existentes SIN duplicar lógica
from conversational_continuity_middleware import ConversationalContinuityMiddleware
from services.redis_buffer_service import redis_buffer


@dataclass
class IntelligenceContext:
    """Contexto enriquecido para la respuesta del modelo"""
    user_query: str
    session_id: str
    agent_id: str

    # Contexto conversacional (Redis)
    conversation_context: Optional[Dict[str, Any]] = None

    # Información de GitHub
    github_context: Optional[Dict[str, Any]] = None

    # Búsqueda semántica
    semantic_results: Optional[List[Dict[str, Any]]] = None

    # Decisión de routing
    recommended_action: Optional[str] = None

    # Prompt enriquecido final
    enriched_prompt: Optional[str] = None


class PreResponseIntelligence:
    """
    Interceptor inteligente que analiza consultas ANTES de la respuesta del modelo

    Reutiliza toda la lógica existente sin duplicación:
    - ConversationalContinuityMiddleware para Redis
    - GitHub tools para repositorio  
    - AI Search para semántica
    - Router semántico para decisiones
    """

    def __init__(self):
        self.continuity_middleware = ConversationalContinuityMiddleware()
        self.enabled = True

    def should_intercept(self, user_query: str, session_id: str) -> bool:
        """Determina si la consulta necesita interceptación inteligente"""
        if not self.enabled or not user_query or len(user_query.strip()) < 5:
            return False

        # Solo interceptar consultas sustanciales
        return len(user_query.strip()) > 10

    def analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Analiza la intención de la consulta para determinar qué fuentes consultar
        REUTILIZA: semantic_intent_classifier existente
        """
        try:
            from semantic_intent_classifier import classify_user_intent

            intent_result = classify_user_intent(user_query)

            # Mapear intenciones a fuentes de datos
            intent_mapping = {
                "buscar_codigo": ["github", "semantic_search"],
                "revisar_logs": ["semantic_search", "conversation"],
                "consultar_historial": ["conversation", "redis"],
                "validar_informacion": ["github", "semantic_search"],
                "preguntar_general": ["conversation", "semantic_search"],
                "ejecutar_comando": ["conversation", "github"]
            }

            intent_name = intent_result.get("intent", "preguntar_general")
            required_sources = intent_mapping.get(
                intent_name, ["conversation"])

            return {
                "intent": intent_name,
                "confidence": intent_result.get("confidence", 0.5),
                "required_sources": required_sources,
                "analysis": intent_result
            }

        except Exception as e:
            logging.warning(f"Error analizando intención: {e}")
            return {
                "intent": "preguntar_general",
                "confidence": 0.3,
                "required_sources": ["conversation"],
                "analysis": {}
            }

    def gather_conversation_context(self, user_query: str, session_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        REUTILIZA: ConversationalContinuityMiddleware para obtener contexto de Redis
        """
        try:
            context = self.continuity_middleware.inject_conversational_context(
                user_message=user_query,
                session_id=session_id,
                agent_id=agent_id
            )

            if context.get("has_context"):
                logging.info(
                    f"🔄 Contexto conversacional recuperado para pre-respuesta")
                return context

            return None

        except Exception as e:
            logging.warning(f"Error recuperando contexto conversacional: {e}")
            return None

    def gather_github_context(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        REUTILIZA: Herramientas GitHub existentes para validar información del repositorio
        """
        try:
            # Detectar si la consulta requiere información de GitHub
            github_keywords = [
                "código", "archivo", "función", "clase", "implementación",
                "repository", "repo", "github", "commit", "branch",
                "file", "code", "implementation"
            ]

            query_lower = user_query.lower()
            needs_github = any(
                keyword in query_lower for keyword in github_keywords)

            if not needs_github:
                return None

            # TODO: Integrar con herramientas GitHub existentes
            # Aquí se llamaría a las tools de GitHub que ya tienes implementadas
            logging.info(
                f"🐙 Consulta requiere validación GitHub: {user_query[:50]}...")

            return {
                "needs_github": True,
                "suggested_action": "github_search",
                "query_analysis": "Consulta relacionada con código/repositorio"
            }

        except Exception as e:
            logging.warning(f"Error analizando contexto GitHub: {e}")
            return None

    def gather_semantic_context(self, user_query: str, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        REUTILIZA: AI Search existente para búsqueda semántica
        """
        try:
            from endpoints_search_memory import buscar_memoria_endpoint

            # Usar el endpoint existente de búsqueda
            search_payload = {
                "query": user_query,
                "top": 5,
                "session_id": session_id
            }

            results = buscar_memoria_endpoint(search_payload)

            if results.get("exito") and results.get("documentos"):
                docs = results["documentos"][:3]  # Top 3 más relevantes
                logging.info(
                    f"🔍 {len(docs)} resultados semánticos para pre-respuesta")
                return docs

            return None

        except Exception as e:
            logging.warning(f"Error en búsqueda semántica: {e}")
            return None

    def build_enriched_context(self, intelligence_context: IntelligenceContext) -> str:
        """
        Construye prompt enriquecido REUTILIZANDO lógica del ConversationalContinuityMiddleware
        """
        try:
            # Si hay contexto conversacional, usar el builder existente
            if intelligence_context.conversation_context:
                from conversational_continuity_middleware import build_context_enriched_prompt

                enriched = build_context_enriched_prompt(
                    original_prompt=intelligence_context.user_query,
                    user_message=intelligence_context.user_query,
                    session_id=intelligence_context.session_id,
                    agent_id=intelligence_context.agent_id
                )

                # Agregar contexto adicional si existe
                additional_context = []

                if intelligence_context.github_context:
                    additional_context.append(
                        "📋 Información del repositorio disponible para consulta")

                if intelligence_context.semantic_results:
                    count = len(intelligence_context.semantic_results)
                    additional_context.append(
                        f"🔍 {count} resultados de búsqueda semántica relevantes")

                if additional_context:
                    enriched += "\n\n" + "\n".join(additional_context)

                return enriched

            # Fallback: construir prompt básico
            return intelligence_context.user_query

        except Exception as e:
            logging.warning(f"Error construyendo contexto enriquecido: {e}")
            return intelligence_context.user_query

    def intercept_and_enrich(self, user_query: str, session_id: str, agent_id: str) -> IntelligenceContext:
        """
        MÉTODO PRINCIPAL: Intercepta consulta y la enriquece con toda la inteligencia disponible

        REUTILIZA toda la lógica existente sin duplicación
        """
        context = IntelligenceContext(
            user_query=user_query,
            session_id=session_id,
            agent_id=agent_id
        )

        if not self.should_intercept(user_query, session_id):
            context.enriched_prompt = user_query
            return context

        logging.info(
            f"🧠 [PreResponse] Interceptando consulta para enriquecimiento: {user_query[:50]}...")

        # 1. Analizar intención de la consulta
        intent_analysis = self.analyze_query_intent(user_query)
        required_sources = intent_analysis["required_sources"]

        # 2. Reunir contexto según las fuentes requeridas
        if "conversation" in required_sources or "redis" in required_sources:
            context.conversation_context = self.gather_conversation_context(
                user_query, session_id, agent_id
            )

        if "github" in required_sources:
            context.github_context = self.gather_github_context(user_query)

        if "semantic_search" in required_sources:
            context.semantic_results = self.gather_semantic_context(
                user_query, session_id)

        # 3. Construir prompt enriquecido
        context.enriched_prompt = self.build_enriched_context(context)

        # 4. Determinar acción recomendada
        if context.github_context and context.github_context.get("needs_github"):
            context.recommended_action = "consult_github"
        elif context.semantic_results and len(context.semantic_results) > 2:
            context.recommended_action = "use_semantic_results"
        elif context.conversation_context:
            context.recommended_action = "continue_conversation"
        else:
            context.recommended_action = "direct_response"

        logging.info(
            f"🎯 [PreResponse] Enriquecimiento completado: {context.recommended_action}")

        return context


# Instancia global para reutilización
pre_response_intelligence = PreResponseIntelligence()


def enrich_user_query_before_response(user_query: str, session_id: str, agent_id: str = "foundry_user") -> str:
    """
    FUNCIÓN PÚBLICA: Enriquece consulta del usuario ANTES de que el modelo responda

    Esta función puede ser llamada desde:
    - System prompts
    - Middleware de Foundry
    - Interceptores de request
    - Cualquier punto ANTES de la respuesta del modelo

    Retorna el prompt enriquecido para el modelo
    """
    try:
        context = pre_response_intelligence.intercept_and_enrich(
            user_query, session_id, agent_id
        )

        return context.enriched_prompt or user_query

    except Exception as e:
        logging.error(f"Error en enriquecimiento pre-respuesta: {e}")
        return user_query


def get_intelligence_context(user_query: str, session_id: str, agent_id: str = "foundry_user") -> IntelligenceContext:
    """
    FUNCIÓN PÚBLICA: Obtiene contexto completo de inteligencia

    Para casos donde se necesita más información que solo el prompt enriquecido
    """
    try:
        return pre_response_intelligence.intercept_and_enrich(
            user_query, session_id, agent_id
        )
    except Exception as e:
        logging.error(f"Error obteniendo contexto de inteligencia: {e}")
        return IntelligenceContext(
            user_query=user_query,
            session_id=session_id,
            agent_id=agent_id,
            enriched_prompt=user_query
        )
