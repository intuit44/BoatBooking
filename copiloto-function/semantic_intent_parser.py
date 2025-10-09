#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser semántico de intenciones - Convierte lenguaje natural a comandos
Sin predefiniciones, completamente dinámico
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class SemanticIntentParser:
    """Parser que convierte lenguaje natural a comandos ejecutables"""
    
    def __init__(self):
        # Patrones semánticos dinámicos (no predefinidos)
        self.action_patterns = {
            # Acciones de instalación
            "install": {
                "keywords": ["instalar", "install", "añadir", "agregar", "descargar"],
                "context_clues": ["paquete", "librería", "biblioteca", "módulo"],
                "command_template": "pip install {package}"
            },
            "upgrade": {
                "keywords": ["actualizar", "upgrade", "update", "mejorar"],
                "context_clues": ["versión", "nueva", "última"],
                "command_template": "pip install --upgrade {package}"
            },
            "uninstall": {
                "keywords": ["desinstalar", "uninstall", "remove", "eliminar", "quitar"],
                "context_clues": ["paquete", "librería"],
                "command_template": "pip uninstall {package}",
                "requires_confirmation": True
            },
            # Acciones Azure
            "list_resources": {
                "keywords": ["listar", "mostrar", "ver", "estado", "recursos"],
                "context_clues": ["azure", "recursos", "infraestructura"],
                "command_template": "az resource list --output table"
            },
            "monitor_logs": {
                "keywords": ["logs", "analizar", "app insights", "monitor"],
                "context_clues": ["aplicación", "errores", "métricas"],
                "command_template": "az monitor app-insights query",
                "requires_grounding": True
            }
        }
        
        # Patrones de entidades (paquetes, recursos, etc.)
        self.entity_patterns = {
            "python_packages": [
                "numpy", "pandas", "matplotlib", "requests", "flask", "django",
                "tensorflow", "pytorch", "scikit-learn", "opencv", "pillow"
            ],
            "azure_resources": [
                "storage", "function", "webapp", "cosmos", "sql", "keyvault"
            ]
        }
    
    def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """Parsea la intención del usuario y genera comando apropiado"""
        if not user_input or not user_input.strip():
            return self._fallback_response("Input vacío")
        
        text = user_input.lower().strip()
        
        # 1. Detectar acción principal
        detected_action = self._detect_action(text)
        
        # 2. Extraer entidades (paquetes, recursos, etc.)
        entities = self._extract_entities(text)
        
        # 3. Generar comando basado en acción y entidades
        command_result = self._generate_command(detected_action or "unknown", entities, text)
        
        # 4. Evaluar si necesita confirmación o grounding
        command_result.update({
            "original_input": user_input,
            "parsed_action": detected_action,
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        })
        
        return command_result
    
    def _detect_action(self, text: str) -> Optional[str]:
        """Detecta la acción principal en el texto"""
        # Primero buscar palabras exactas más específicas
        if any(word in text for word in ["desinstalar", "uninstall", "remove", "eliminar", "quitar"]):
            return "uninstall"
        elif any(word in text for word in ["actualizar", "upgrade", "update"]):
            return "upgrade"
        elif any(word in text for word in ["instalar", "install"]):
            return "install"
        elif any(word in text for word in ["listar", "mostrar", "ver", "estado", "recursos"]):
            return "list_resources"
        elif any(word in text for word in ["logs", "analizar", "app insights", "monitor"]):
            return "monitor_logs"
        
        # Fallback al método original
        best_action = None
        best_score = 0
        
        for action, patterns in self.action_patterns.items():
            score = 0
            
            # Buscar keywords de acción
            for keyword in patterns["keywords"]:
                if keyword in text:
                    score += 2
            
            # Buscar claves de contexto
            for clue in patterns.get("context_clues", []):
                if clue in text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action if best_score > 0 else None
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrae entidades del texto (paquetes, recursos, etc.)"""
        entities = {
            "packages": [],
            "resources": [],
            "unknown": [],
            "dangerous_words": [],
            "ambiguous_words": []
        }
        
        # Detectar palabras peligrosas
        dangerous_words = ["todo", "all", "everything", "system", "root", "admin", "*"]
        ambiguous_words = ["todo", "all", "everything", "system"]
        
        text_lower = text.lower()
        
        # Buscar palabras peligrosas
        for word in dangerous_words:
            if word in text_lower:
                entities["dangerous_words"].append(word)
        
        # Buscar palabras ambiguas
        for word in ambiguous_words:
            if word in text_lower:
                entities["ambiguous_words"].append(word)
        
        # Buscar paquetes Python conocidos
        for package in self.entity_patterns["python_packages"]:
            if package in text:
                entities["packages"].append(package)
        
        # Buscar recursos Azure conocidos
        for resource in self.entity_patterns["azure_resources"]:
            if resource in text:
                entities["resources"].append(resource)
        
        # Buscar entidades desconocidas (palabras que podrían ser paquetes)
        # PERO excluir palabras peligrosas/ambiguas
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]*\b', text)
        excluded_words = ["quiero", "como", "instalar", "actualizar", "desinstalar", "todo", "all", "everything"]
        
        for word in words:
            if (len(word) > 2 and 
                word.lower() not in excluded_words and
                word not in entities["packages"] and 
                word not in entities["resources"] and
                word.lower() not in dangerous_words):
                entities["unknown"].append(word)
        
        return entities
    
    def _generate_command(self, action: str, entities: Dict, original_text: str) -> Dict[str, Any]:
        """Genera el comando apropiado basado en acción y entidades"""
        
        if not action or action == "unknown":
            return self._handle_vague_query(original_text)
        
        action_config = self.action_patterns.get(action, {})
        template = action_config.get("command_template", "")
        
        # Casos específicos por acción
        if action == "install":
            package = self._get_primary_entity(entities)
            if package:
                return {
                    "command": f"pip install {package}",
                    "type": "python",
                    "confidence": 0.9,
                    "requires_confirmation": False,
                    "explanation": f"Instalar el paquete Python '{package}'"
                }
        
        elif action == "upgrade":
            # Verificar si hay palabras peligrosas/ambiguas
            if entities.get("dangerous_words") or entities.get("ambiguous_words"):
                return {
                    "requires_grounding": True,
                    "grounding_query": f"actualizar específicamente qué: {original_text}",
                    "context": "ambiguous_update",
                    "explanation": "'Actualizar todo' es ambiguo. ¿Qué específicamente quieres actualizar?",
                    "suggested_clarifications": [
                        "actualizar [nombre_paquete_específico]",
                        "actualizar todos los paquetes Python: pip list --outdated",
                        "actualizar sistema operativo",
                        "actualizar Azure CLI: az upgrade"
                    ]
                }
            
            package = self._get_primary_entity(entities)
            if package:
                return {
                    "command": f"pip install --upgrade {package}",
                    "type": "python", 
                    "confidence": 0.9,
                    "requires_confirmation": False,
                    "explanation": f"Actualizar el paquete Python '{package}' a la última versión"
                }
        
        elif action == "uninstall":
            # Verificar si hay palabras peligrosas
            if entities.get("dangerous_words"):
                return {
                    "requires_grounding": True,
                    "grounding_query": f"desinstalar específicamente qué: {original_text}",
                    "context": "dangerous_uninstall",
                    "explanation": "Desinstalar 'todo' es peligroso. Especifica qué paquete exacto quieres desinstalar.",
                    "warning": "⚠️ Operación potencialmente destructiva detectada"
                }
            
            package = self._get_primary_entity(entities)
            if package:
                return {
                    "command": f"pip uninstall {package}",
                    "type": "python",
                    "confidence": 0.8,
                    "requires_confirmation": True,
                    "confirmation_message": f"¿Confirmas que quieres desinstalar '{package}'?",
                    "explanation": f"Desinstalar el paquete Python '{package}'"
                }
        
        elif action == "list_resources":
            return {
                "command": "az resource list --output table",
                "type": "azure_cli",
                "confidence": 0.8,
                "requires_confirmation": False,
                "explanation": "Listar todos los recursos de Azure"
            }
        
        elif action == "monitor_logs":
            return {
                "requires_grounding": True,
                "grounding_query": original_text,
                "context": "azure_monitoring",
                "explanation": "Esta consulta requiere información específica sobre tu configuración de App Insights",
                "suggested_commands": [
                    "az monitor app-insights query --help",
                    "az monitor log-analytics query --help"
                ]
            }
        
        # Fallback si no se pudo generar comando específico
        return self._handle_vague_query(original_text)
    
    def _get_primary_entity(self, entities: Dict) -> Optional[str]:
        """Obtiene la entidad principal del contexto"""
        # Priorizar paquetes conocidos
        if entities["packages"]:
            return entities["packages"][0]
        
        # Luego entidades desconocidas (posibles paquetes)
        if entities["unknown"]:
            return entities["unknown"][0]
        
        return None
    
    def _handle_vague_query(self, original_text: str) -> Dict[str, Any]:
        """Maneja consultas vagas que necesitan grounding"""
        return {
            "requires_grounding": True,
            "grounding_query": original_text,
            "context": "general_help",
            "confidence": 0.3,
            "explanation": "Tu consulta necesita más información específica",
            "suggestions": [
                "Sé más específico sobre qué quieres hacer",
                "Menciona el nombre exacto del paquete o recurso",
                "Usa comandos como 'instalar X', 'actualizar Y', etc."
            ]
        }
    
    def _fallback_response(self, reason: str) -> Dict[str, Any]:
        """Respuesta de fallback segura"""
        return {
            "error": f"No se pudo procesar la solicitud: {reason}",
            "requires_grounding": True,
            "suggestions": [
                "Reformula tu consulta",
                "Sé más específico",
                "Usa comandos directos como 'pip install numpy'"
            ]
        }

# Instancia global
semantic_parser = SemanticIntentParser()

def parse_natural_language(user_input: str) -> Dict[str, Any]:
    """Función principal para parsear lenguaje natural"""
    try:
        result = semantic_parser.parse_intent(user_input)
        logging.info(f"Intent parsed: {result.get('command', 'no_command')} (confidence: {result.get('confidence', 0)})")
        return result
    except Exception as e:
        logging.error(f"Error parsing intent: {e}")
        return {
            "error": str(e),
            "requires_grounding": True,
            "fallback": True
        }

def should_trigger_bing_grounding(parsed_result: Dict[str, Any]) -> bool:
    """Determina si se debe activar Bing Grounding"""
    return (
        parsed_result.get("requires_grounding", False) or
        parsed_result.get("confidence", 1.0) < 0.5 or
        "error" in parsed_result
    )

def enhance_hybrid_parser(user_input: str) -> Dict[str, Any]:
    """Mejora el parser híbrido con capacidades semánticas"""
    # Primero intentar parsing semántico
    semantic_result = parse_natural_language(user_input)
    
    # Si tiene comando directo, usarlo
    if "command" in semantic_result:
        return {
            "endpoint": "ejecutar-comando",
            "method": "POST",
            "data": {
                "comando": semantic_result["command"]
            },
            "requires_confirmation": semantic_result.get("requires_confirmation", False),
            "explanation": semantic_result.get("explanation", ""),
            "confidence": semantic_result.get("confidence", 0.8)
        }
    
    # Si requiere grounding, activarlo
    if should_trigger_bing_grounding(semantic_result):
        return {
            "endpoint": "bing-grounding", 
            "method": "POST",
            "data": {
                "query": semantic_result.get("grounding_query", user_input),
                "contexto": semantic_result.get("context", "general")
            },
            "requires_grounding": True,
            "explanation": semantic_result.get("explanation", "Necesita información adicional")
        }
    
    # Fallback a status
    return {
        "endpoint": "status",
        "method": "GET",
        "explanation": "No se pudo interpretar la solicitud"
    }