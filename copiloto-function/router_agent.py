#!/usr/bin/env python3
"""
Router Agent: Módulo de orquestación multi-agente basado en intenciones semánticas.
Se integra con memory_route_wrapper como helper para delegar tareas al agente correcto.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone
import os

# Configuración de agentes disponibles
AGENT_REGISTRY = {
    "correccion": {
        "agent_id": "Agent975",  # Agente corrector de código
        "model": "mistral-large-2411",  # Excelente para código y precisión técnica
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_MAIN", "yellowstone413g-9987"),
        "capabilities": ["code_fixing", "syntax_correction", "file_editing"],
        "description": "Agente especializado en corrección de código y archivos"
    },
    "diagnostico": {
        "agent_id": "Agent914",  # Agente de diagnóstico
        # Excelente para análisis y razonamiento complejo
        "model": "claude-3-5-sonnet-20241022",
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_MAIN", "yellowstone413g-9987"),
        "capabilities": ["system_diagnosis", "health_check", "monitoring"],
        "description": "Agente especializado en diagnóstico de sistemas"
    },
    "boat_management": {
        "agent_id": "BookingAgent",  # Agente de gestión de embarcaciones
        # Excelente para interacción con clientes y gestión de reservas
        "model": "gpt-4o-2024-11-20",
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_BOOKING", "booking-agents"),
        "capabilities": ["booking", "reservation", "boat_info", "availability"],
        "description": "Agente especializado en gestión de reservas de embarcaciones"
    },
    "ejecucion_cli": {
        "agent_id": "Agent975",  # Reutilizar agente executor
        "model": "gpt-4-2024-11-20",  # Sólido para comandos CLI y Azure tooling
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_MAIN", "yellowstone413g-9987"),
        "capabilities": ["cli_execution", "command_line", "azure_cli"],
        "description": "Agente especializado en ejecución de comandos CLI"
    },
    "operacion_archivo": {
        "agent_id": "Agent975",  # Reutilizar agente corrector para archivos
        # Especializado en operaciones con archivos y código
        "model": "codestral-2024-10-29",
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_MAIN", "yellowstone413g-9987"),
        "capabilities": ["file_operations", "read_write", "file_management"],
        "description": "Agente especializado en operaciones con archivos"
    },
    "conversacion_general": {
        "agent_id": "Agent914",  # Agente general por defecto
        "model": "gpt-4o-mini-2024-07-18",  # Eficiente y rápido para conversación general
        "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT", "https://boatRentalFoundry-dev.services.ai.azure.com"),
        "project_id": os.getenv("AI_PROJECT_ID_MAIN", "yellowstone413g-9987"),
        "capabilities": ["general_chat", "information", "assistance"],
        "description": "Agente de propósito general para conversaciones"
    }
}


class AgentRouter:
    """Orquestador de agentes basado en intenciones semánticas."""

    def __init__(self):
        self.agent_registry = AGENT_REGISTRY.copy()
        self.routing_history: List[Dict[str, Any]] = []

    def route_to_agent(self, intent: str, confidence: float, user_message: str,
                       session_id: Optional[str] = None,
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Rutas una intención detectada al agente apropiado.

        Args:
            intent: Intención detectada (ej: "correccion", "diagnostico")
            confidence: Nivel de confianza de la clasificación
            user_message: Mensaje original del usuario
            session_id: ID de sesión para tracking
            context: Contexto adicional de la conversación

        Returns:
            Dict con información del agente seleccionado y metadatos de routing
        """
        try:
            # 1. Buscar agente específico para la intención
            agent_info = self.agent_registry.get(intent)

            # 2. Fallback a agente general si no hay match específico
            if not agent_info:
                logging.warning(
                    f"[AgentRouter] Intención '{intent}' no tiene agente específico, usando fallback")
                agent_info = self.agent_registry.get("conversacion_general")

            if not agent_info:
                raise ValueError("No hay agentes disponibles en el registry")

            # 3. Preparar información de routing
            routing_result = {
                "agent_id": agent_info["agent_id"],
                "endpoint": agent_info["endpoint"],
                "project_id": agent_info["project_id"],
                # Modelo asignado o fallback
                "model": agent_info.get("model", "gpt-4o-mini-2024-07-18"),
                "capabilities": agent_info["capabilities"],
                "description": agent_info["description"],
                "routing_metadata": {
                    "intent": intent,
                    "confidence": confidence,
                    # Modelo para trazabilidad
                    "model": agent_info.get("model", "gpt-4o-mini-2024-07-18"),
                    "routing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_message_length": len(user_message) if user_message else 0,
                    "session_id": session_id,
                    "fallback_used": intent not in self.agent_registry,
                    "original_intent": intent
                }
            }

            # 4. Registrar en historial de routing
            self.routing_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "selected_agent": agent_info["agent_id"],
                "fallback_used": intent not in self.agent_registry
            })

            # 5. Mantener solo últimas 100 entradas en historial
            if len(self.routing_history) > 100:
                self.routing_history = self.routing_history[-100:]

            logging.info(
                f"[AgentRouter] Intent '{intent}' (conf: {confidence:.2f}) → Agent: {agent_info['agent_id']}")

            return routing_result

        except Exception as e:
            logging.error(f"[AgentRouter] Error en routing: {e}")
            # Fallback de emergencia
            fallback_model = self.agent_registry.get(
                "conversacion_general", {}).get("model", "gpt-4o-mini-2024-07-18")
            return {
                "agent_id": "Agent914",
                "endpoint": self.agent_registry.get("conversacion_general", {}).get("endpoint", ""),
                "project_id": self.agent_registry.get("conversacion_general", {}).get("project_id", ""),
                "model": fallback_model,
                "capabilities": ["fallback"],
                "description": "Agente de emergencia por error en routing",
                "routing_metadata": {
                    "intent": intent,
                    "confidence": 0.0,
                    "model": fallback_model,
                    "routing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                    "emergency_fallback": True
                }
            }

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un agente específico por ID."""
        for intent, info in self.agent_registry.items():
            if info["agent_id"] == agent_id:
                return {
                    "intent": intent,
                    **info
                }
        return None

    def get_routing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de routing."""
        if not self.routing_history:
            return {"total_routings": 0}

        total = len(self.routing_history)
        fallback_count = sum(
            1 for r in self.routing_history if r.get("fallback_used"))

        # Agrupar por intención
        intent_counts = {}
        agent_counts = {}
        for r in self.routing_history:
            intent = r.get("intent", "unknown")
            agent = r.get("selected_agent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "total_routings": total,
            "fallback_count": fallback_count,
            "fallback_rate": fallback_count / total if total > 0 else 0,
            "intent_distribution": intent_counts,
            "agent_distribution": agent_counts,
            "recent_routings": self.routing_history[-5:] if total > 0 else []
        }


# Instancia global del router
agent_router = AgentRouter()


def route_by_semantic_intent(user_message: str, session_id: Optional[str] = None,
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper function que integra clasificación semántica + routing de agentes.
    Diseñado para ser llamado desde memory_route_wrapper.

    Args:
        user_message: Mensaje del usuario a procesar
        session_id: ID de sesión para tracking
        context: Contexto adicional

    Returns:
        Dict con agente seleccionado e información de routing
    """
    try:
        # 1. Sanitizar user_message para evitar errores de encoding
        if user_message:
            # Limpiar caracteres problemáticos que causan charmap errors
            user_message_clean = user_message.encode('ascii', 'replace').decode('ascii')
            user_message_clean = user_message_clean.replace('?', '')  # Remove replacement chars
        else:
            user_message_clean = user_message
            
        # 2. Clasificar intención usando el clasificador existente
        from semantic_intent_classifier import classify_user_intent

        intent_result = classify_user_intent(user_message_clean)
        intent = intent_result.get("intent", "conversacion_general")
        confidence = intent_result.get("confidence", 0.0)

        # 2. Usar el router para seleccionar agente
        routing_result = agent_router.route_to_agent(
            intent=intent,
            confidence=confidence,
            user_message=user_message,
            session_id=session_id,
            context=context
        )

        # 3. Agregar información de clasificación al resultado
        routing_result["intent_classification"] = intent_result

        logging.info(
            f"[SemanticRouter] '{user_message[:50]}...' → {intent} → {routing_result['agent_id']}")

        return routing_result

    except Exception as e:
        logging.error(f"[SemanticRouter] Error en routing semántico: {e}")
        # Fallback de emergencia
        fallback_model = AGENT_REGISTRY.get("conversacion_general", {}).get(
            "model", "gpt-4o-mini-2024-07-18")
        return {
            "agent_id": "Agent914",
            "endpoint": AGENT_REGISTRY.get("conversacion_general", {}).get("endpoint", ""),
            "project_id": AGENT_REGISTRY.get("conversacion_general", {}).get("project_id", ""),
            "model": fallback_model,
            "capabilities": ["emergency_fallback"],
            "description": "Routing de emergencia",
            "routing_metadata": {
                "model": fallback_model,
                "error": str(e),
                "emergency_fallback": True
            }
        }


def register_custom_agent(intent: str, agent_config: Dict[str, Any]) -> bool:
    """
    Registra un agente personalizado para una intención específica.

    Args:
        intent: Intención a manejar
        agent_config: Configuración del agente

    Returns:
        True si se registró exitosamente
    """
    try:
        required_fields = ["agent_id", "endpoint",
                           "project_id", "capabilities", "description"]
        if not all(field in agent_config for field in required_fields):
            logging.error(
                f"[AgentRouter] Configuración de agente incompleta para '{intent}'")
            return False

        agent_router.agent_registry[intent] = agent_config
        logging.info(
            f"[AgentRouter] Agente personalizado registrado: {intent} → {agent_config['agent_id']}")
        return True

    except Exception as e:
        logging.error(
            f"[AgentRouter] Error registrando agente personalizado: {e}")
        return False


# Funciones de utilidad para integración con memory_route_wrapper
def get_agent_for_message(user_message: str, session_id: Optional[str] = None) -> str:
    """Obtiene solo el agent_id para un mensaje (función simple para el wrapper)."""
    try:
        routing = route_by_semantic_intent(user_message, session_id)
        return routing.get("agent_id", "Agent914")
    except:
        return "Agent914"  # Fallback seguro


def get_routing_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del router (para debugging y monitoring)."""
    return agent_router.get_routing_stats()
