#!/usr/bin/env python3
import logging
import time
"""
Integración del Pre-Response Intelligence con System Instructions

Este archivo puede ser usado para modificar instrucciones del sistema
o integrarse con el middleware de Foundry
"""


def get_enhanced_system_instructions() -> str:
    """
    Retorna instrucciones del sistema que incluyen el interceptor inteligente
    """
    return """
🧠 SISTEMA DE INTELIGENCIA PRE-RESPUESTA ACTIVO

Antes de responder a cualquier consulta del usuario, el sistema automáticamente:

1. ✅ ANALIZA la intención de la consulta
2. ✅ CONSULTA Redis para contexto conversacional  
3. ✅ VERIFICA si necesita información de GitHub
4. ✅ BUSCA semánticamente en memoria/documentos
5. ✅ ENRIQUECE tu contexto automáticamente

Tu respuesta debe ser natural e integrada. No mentions explícitamente estos procesos.

Si detectas que tu contexto incluye:
- 🔄 "CONTINUIDAD": Referencias naturalmente conversaciones previas
- 🐙 "GitHub disponible": Puedes validar información del repositorio  
- 🔍 "Búsqueda semántica": Usa resultados para respuestas más precisas

Responde de manera fluida incorporando toda la información contextual disponible.
"""


def enhance_user_query_for_model(user_query: str, session_id: str = None, agent_id: str = "foundry_user") -> str:
    """
    PUNTO DE INTEGRACIÓN: Enriquece consulta antes de enviar al modelo

    Esta función puede ser llamada desde:
    - Function apps antes de procesar
    - Middleware de Foundry
    - System prompts dinámicos
    """
    try:
        from pre_response_intelligence import enrich_user_query_before_response

        if not session_id:
            session_id = f"auto_{hash(user_query)}_{int(time.time())}"

        enriched_query = enrich_user_query_before_response(
            user_query, session_id, agent_id
        )

        return enriched_query

    except Exception as e:
        logging.warning(f"Error en enriquecimiento: {e}")
        return user_query
