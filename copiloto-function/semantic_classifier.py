"""
🧠 Clasificador Semántico Robusto para LLM Comercial
Implementa clasificación multi-patrón sin dependencias externas pesadas
"""

import re
from typing import Dict, List, Any, Tuple
from collections import Counter
import logging

class SemanticClassifier:
    """Clasificador semántico basado en patrones y heurísticas avanzadas"""
    
    def __init__(self):
        # Patrones de intención por categorías
        self.intention_patterns = {
            "diagnostico": [
                r"verificar|check|status|estado|health|ping|test",
                r"app.?insights|sistema|recursos|diagnostic"
            ],
            "ejecucion": [
                r"ejecutar|run|start|launch|deploy|install",
                r"cli|command|script|bash|powershell"
            ],
            "consulta": [
                r"historial|history|log|consultar|buscar|search",
                r"listar|list|show|get|fetch"
            ],
            "configuracion": [
                r"config|setup|init|create|modify|update",
                r"azure|aws|cloud|container|database"
            ],
            "hybrid": [
                r"hybrid|mixed|combined|integration|merge",
                r"fallback|grounding|bing|external"
            ],
            "error_recovery": [
                r"error|fail|exception|retry|recover|fix",
                r"timeout|connection|auth|permission"
            ]
        }
        
        # Pesos de relevancia por contexto
        self.context_weights = {
            "reciente": 1.0,      # Últimas 3 interacciones
            "medio": 0.7,         # 4-10 interacciones
            "lejano": 0.3,        # 11+ interacciones
            "relacionado": 1.5,   # Mismo patrón de intención
            "critico": 2.0        # Errores o fallos
        }

    def classify_interaction(self, texto_semantico: str, endpoint: str) -> Dict[str, Any]:
        """Clasifica una interacción individual"""
        
        # Detectar intención principal
        intention = self._detect_intention(texto_semantico, endpoint)
        
        # Detectar criticidad
        criticality = self._detect_criticality(texto_semantico)
        
        # Detectar contexto temático
        theme = self._extract_theme(texto_semantico, endpoint)
        
        return {
            "intention": intention,
            "criticality": criticality,
            "theme": theme,
            "endpoint": endpoint,
            "semantic_score": self._calculate_semantic_score(intention, criticality)
        }

    def _detect_intention(self, texto: str, endpoint: str) -> str:
        """Detecta la intención usando patrones regex"""
        texto_lower = texto.lower()
        endpoint_lower = endpoint.lower()
        combined_text = f"{texto_lower} {endpoint_lower}"
        
        scores = {}
        for intention, patterns in self.intention_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text))
                score += matches
            scores[intention] = score
        
        # Retornar la intención con mayor score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "general"

    def _detect_criticality(self, texto: str) -> str:
        """Detecta nivel de criticidad"""
        texto_lower = texto.lower()
        
        if any(word in texto_lower for word in ["error", "fail", "exception", "timeout"]):
            return "high"
        elif any(word in texto_lower for word in ["warning", "retry", "fallback"]):
            return "medium"
        elif any(word in texto_lower for word in ["success", "completed", "ok"]):
            return "low"
        return "normal"

    def _extract_theme(self, texto: str, endpoint: str) -> str:
        """Extrae tema principal de la interacción"""
        # Combinar texto y endpoint para análisis
        combined = f"{texto} {endpoint}".lower()
        
        # Temas técnicos principales
        themes = {
            "azure": ["azure", "cosmosdb", "storage", "function"],
            "system": ["system", "diagnostic", "health", "status"],
            "memory": ["memory", "historial", "context", "session"],
            "execution": ["cli", "command", "script", "run"],
            "api": ["api", "endpoint", "request", "response"],
            "hybrid": ["hybrid", "grounding", "bing", "fallback"]
        }
        
        for theme, keywords in themes.items():
            if any(keyword in combined for keyword in keywords):
                return theme
        
        return "general"

    def _calculate_semantic_score(self, intention: str, criticality: str) -> float:
        """Calcula score semántico para priorización"""
        base_scores = {
            "error_recovery": 1.0,
            "ejecucion": 0.9,
            "configuracion": 0.8,
            "diagnostico": 0.7,
            "hybrid": 0.6,
            "consulta": 0.5
        }
        
        criticality_multiplier = {
            "high": 1.5,
            "medium": 1.2,
            "normal": 1.0,
            "low": 0.8
        }
        
        base = base_scores.get(intention, 0.5)
        multiplier = criticality_multiplier.get(criticality, 1.0)
        
        return base * multiplier

class ContextController:
    """Controlador de contexto que decide qué memoria pasar al modelo"""
    
    def __init__(self, classifier: SemanticClassifier):
        self.classifier = classifier
        self.max_context_items = 10  # Máximo de interacciones a incluir

    def select_relevant_context(self, interacciones: List[Dict], current_input: str = "") -> Dict[str, Any]:
        """Selecciona contexto relevante basado en la entrada actual"""
        
        if not interacciones:
            return {"mode": "new_session", "context": [], "summary": "Nueva sesión"}
        
        # Clasificar todas las interacciones
        classified = []
        for i, interaccion in enumerate(interacciones):
            classification = self.classifier.classify_interaction(
                interaccion.get("texto_semantico", ""),
                interaccion.get("endpoint", "")
            )
            classification["position"] = i
            classification["timestamp"] = interaccion.get("timestamp")
            classification["raw_data"] = interaccion
            classified.append(classification)
        
        # Detectar modo de operación basado en input actual
        mode = self._detect_operation_mode(current_input, classified[:3])
        
        # Seleccionar contexto según el modo
        selected_context = self._select_by_mode(mode, classified)
        
        # Generar resumen inteligente
        summary = self._generate_intelligent_summary(selected_context, mode)
        
        return {
            "mode": mode,
            "context": selected_context,
            "summary": summary,
            "total_analyzed": len(classified),
            "context_selected": len(selected_context)
        }

    def _detect_operation_mode(self, current_input: str, recent_interactions: List[Dict]) -> str:
        """Detecta el modo de operación actual"""
        
        if not current_input:
            return "continuation"
        
        input_lower = current_input.lower()
        
        # Detectar modos específicos
        if any(word in input_lower for word in ["error", "fix", "problem", "issue"]):
            return "error_correction"
        elif any(word in input_lower for word in ["execute", "run", "command", "cli"]):
            return "execution"
        elif any(word in input_lower for word in ["history", "what", "previous", "before"]):
            return "information_retrieval"
        elif any(word in input_lower for word in ["configure", "setup", "create", "modify"]):
            return "configuration"
        
        # Analizar interacciones recientes para contexto
        if recent_interactions:
            recent_intentions = [item.get("intention", "") for item in recent_interactions]
            if "error_recovery" in recent_intentions:
                return "error_correction"
            elif "ejecucion" in recent_intentions:
                return "execution"
        
        return "general"

    def _select_by_mode(self, mode: str, classified: List[Dict]) -> List[Dict]:
        """Selecciona contexto según el modo de operación"""
        
        if mode == "error_correction":
            # Priorizar errores y recuperaciones recientes
            relevant = [item for item in classified if item["criticality"] in ["high", "medium"]]
            relevant.extend([item for item in classified[:5] if item not in relevant])
            
        elif mode == "execution":
            # Priorizar ejecuciones y configuraciones
            relevant = [item for item in classified if item["intention"] in ["ejecucion", "configuracion"]]
            relevant.extend([item for item in classified[:3] if item not in relevant])
            
        elif mode == "information_retrieval":
            # Incluir más contexto histórico
            relevant = classified[:self.max_context_items]
            
        else:  # general, continuation
            # Contexto balanceado con score semántico
            sorted_by_score = sorted(classified, key=lambda x: x["semantic_score"], reverse=True)
            relevant = sorted_by_score[:self.max_context_items]
        
        # Limitar y ordenar por timestamp
        selected = relevant[:self.max_context_items]
        selected.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return selected

    def _generate_intelligent_summary(self, context: List[Dict], mode: str) -> str:
        """Genera resumen inteligente del contexto seleccionado"""
        
        if not context:
            return "Sin contexto previo relevante"
        
        # Analizar patrones en el contexto seleccionado
        intentions = [item["intention"] for item in context]
        themes = [item["theme"] for item in context]
        criticalities = [item["criticality"] for item in context]
        
        intention_counts = Counter(intentions)
        theme_counts = Counter(themes)
        
        # Generar resumen según el modo
        if mode == "error_correction":
            errors = len([c for c in criticalities if c == "high"])
            top_themes = [item[0] for item in theme_counts.most_common(2)]
            return f"Contexto de corrección: {errors} errores detectados. Temas principales: {', '.join(top_themes)}"
        
        elif mode == "execution":
            executions = intention_counts.get("ejecucion", 0)
            return f"Contexto de ejecución: {executions} comandos ejecutados. Último tema: {themes[0] if themes else 'general'}"
        
        else:
            main_intention = intention_counts.most_common(1)[0][0] if intention_counts else "general"
            main_theme = theme_counts.most_common(1)[0][0] if theme_counts else "general"
            return f"Sesión activa: {len(context)} interacciones. Patrón: {main_intention} en {main_theme}"

# Instancia global para uso en el sistema
semantic_classifier = SemanticClassifier()
context_controller = ContextController(semantic_classifier)

def get_intelligent_context(interacciones: List[Dict], current_input: str = "") -> Dict[str, Any]:
    """Función principal para obtener contexto inteligente"""
    return context_controller.select_relevant_context(interacciones, current_input)