#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clasificador de intención semántica basado en embeddings
Sin dependencia de palabras clave predefinidas
"""

import json
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Simulación de embeddings (en producción usar OpenAI/Azure OpenAI)
def get_text_embedding(text: str) -> List[float]:
    """
    Simula embeddings de texto. En producción reemplazar con:
    - OpenAI embeddings API
    - Azure OpenAI embeddings
    - Sentence transformers local
    """
    # Simulación simple basada en hash para consistencia
    import hashlib
    hash_obj = hashlib.md5(text.lower().encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convertir hash a vector de 384 dimensiones (simulado)
    embedding = []
    for i in range(0, len(hash_hex), 2):
        val = int(hash_hex[i:i+2], 16) / 255.0
        embedding.append(val)
    
    # Rellenar hasta 384 dimensiones
    while len(embedding) < 384:
        embedding.extend(embedding[:min(len(embedding), 384-len(embedding))])
    
    return embedding[:384]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcula similitud coseno entre dos vectores"""
    try:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)
    except:
        return 0.0

class SemanticIntentClassifier:
    """Clasificador de intención basado en similitud semántica"""
    
    def __init__(self):
        # Intenciones base con ejemplos semánticamente diversos
        self.intent_examples = {
            "listar_storage": [
                "mostrar cuentas de almacenamiento",
                "ver storage accounts",
                "listar almacenamiento azure",
                "qué cuentas de storage tengo",
                "mostrar mis storages",
                "ver todas las cuentas de almacenamiento"
            ],
            "listar_cosmos": [
                "mostrar bases de datos cosmos",
                "ver cuentas cosmos db",
                "listar cosmos database",
                "qué bases cosmos tengo",
                "mostrar mis cosmos",
                "ver todas las cuentas de cosmos"
            ],
            "listar_functions": [
                "mostrar function apps",
                "ver aplicaciones de función",
                "listar functions azure",
                "qué functions tengo corriendo",
                "mostrar mis funciones",
                "ver todas las function apps"
            ],
            "listar_resources": [
                "mostrar recursos azure",
                "ver todos mis recursos",
                "listar resource groups",
                "qué recursos tengo",
                "mostrar mis grupos de recursos",
                "ver toda mi infraestructura"
            ],
            "diagnosticar_sistema": [
                "hay problemas en mi sistema",
                "verificar estado de recursos",
                "diagnosticar mi infraestructura",
                "revisar salud de servicios",
                "comprobar si todo funciona",
                "analizar estado general"
            ],
            "ayuda_general": [
                "no sé qué hacer",
                "necesito ayuda con azure",
                "no tengo idea cómo empezar",
                "ayúdame con comandos",
                "qué puedo hacer aquí",
                "guíame por favor"
            ]
        }
        
        # Mapeo de intenciones a comandos Azure CLI
        self.intent_to_command = {
            "listar_storage": "az storage account list --output json",
            "listar_cosmos": "az cosmosdb list --output json", 
            "listar_functions": "az functionapp list --output json",
            "listar_resources": "az group list --output json",
            "diagnosticar_sistema": "az resource list --output json",
            "ayuda_general": "az --help"
        }
        
        # Pre-calcular embeddings de ejemplos
        self.intent_embeddings = {}
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """Pre-calcula embeddings de todos los ejemplos"""
        for intent, examples in self.intent_examples.items():
            self.intent_embeddings[intent] = []
            for example in examples:
                embedding = get_text_embedding(example)
                self.intent_embeddings[intent].append(embedding)
    
    def classify_intent(self, user_input: str, threshold: float = 0.3) -> Dict[str, Any]:
        """
        Clasifica la intención del usuario basado en similitud semántica
        """
        if not user_input or not user_input.strip():
            return {
                "intent": "ayuda_general",
                "confidence": 0.5,
                "command": self.intent_to_command["ayuda_general"],
                "method": "fallback"
            }
        
        user_embedding = get_text_embedding(user_input.lower().strip())
        
        best_intent = None
        best_confidence = 0.0
        intent_scores = {}
        
        # Calcular similitud con cada intención
        for intent, embeddings in self.intent_embeddings.items():
            max_similarity = 0.0
            
            # Tomar la máxima similitud con cualquier ejemplo de esta intención
            for example_embedding in embeddings:
                similarity = cosine_similarity(user_embedding, example_embedding)
                max_similarity = max(max_similarity, similarity)
            
            intent_scores[intent] = max_similarity
            
            if max_similarity > best_confidence:
                best_confidence = max_similarity
                best_intent = intent
        
        # Si la confianza es muy baja, usar ayuda general
        if best_confidence < threshold:
            return {
                "intent": "ayuda_general",
                "confidence": best_confidence,
                "command": self.intent_to_command["ayuda_general"],
                "method": "low_confidence_fallback",
                "all_scores": intent_scores,
                "requires_grounding": True
            }
        
        return {
            "intent": best_intent or "ayuda_general",
            "confidence": best_confidence,
            "command": self.intent_to_command[best_intent or "ayuda_general"],
            "method": "semantic_similarity",
            "all_scores": intent_scores,
            "requires_grounding": best_confidence < 0.7  # Grounding si confianza media
        }
    
    def add_learning_example(self, user_input: str, correct_intent: str, command_used: str):
        """
        Añade un ejemplo de aprendizaje para mejorar la clasificación
        """
        if correct_intent in self.intent_examples:
            # Añadir nuevo ejemplo
            self.intent_examples[correct_intent].append(user_input.lower().strip())
            
            # Actualizar comando si es diferente
            if command_used and command_used != self.intent_to_command.get(correct_intent):
                self.intent_to_command[correct_intent] = command_used
            
            # Re-calcular embeddings para esta intención
            self.intent_embeddings[correct_intent] = []
            for example in self.intent_examples[correct_intent]:
                embedding = get_text_embedding(example)
                self.intent_embeddings[correct_intent].append(embedding)
            
            logging.info(f"Aprendizaje añadido: '{user_input}' -> {correct_intent}")
            return True
        
        return False

# Instancia global del clasificador
semantic_classifier = SemanticIntentClassifier()

def classify_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Función principal para clasificar intención del usuario
    """
    try:
        result = semantic_classifier.classify_intent(user_input)
        
        # Añadir metadata
        result.update({
            "timestamp": datetime.now().isoformat(),
            "input_length": len(user_input),
            "classification_method": "semantic_embeddings"
        })
        
        logging.info(f"Intención clasificada: {result['intent']} (confianza: {result['confidence']:.3f})")
        
        return result
        
    except Exception as e:
        logging.error(f"Error en clasificación semántica: {e}")
        
        # Fallback seguro
        return {
            "intent": "ayuda_general", 
            "confidence": 0.1,
            "command": "az --help",
            "method": "error_fallback",
            "error": str(e),
            "requires_grounding": True
        }

def should_use_grounding(classification: Dict[str, Any]) -> bool:
    """
    Determina si se debe usar Bing Grounding basado en la clasificación
    """
    # Usar grounding si:
    # 1. La clasificación lo requiere explícitamente
    # 2. La confianza es baja (< 0.7)
    # 3. La intención es ayuda general
    # 4. Hubo error en la clasificación
    
    return (
        classification.get("requires_grounding", False) or
        classification.get("confidence", 0) < 0.7 or
        classification.get("intent") == "ayuda_general" or
        "error" in classification
    )

def enhance_with_context(classification: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mejora la clasificación con contexto adicional
    """
    if context is None:
        context = {}
    
    # Ajustar confianza basado en contexto
    if context.get("previous_intent") == classification.get("intent"):
        classification["confidence"] = min(1.0, classification["confidence"] + 0.1)
        classification["context_boost"] = True
    
    # Añadir sugerencias relacionadas
    intent = classification.get("intent")
    if intent == "listar_storage":
        classification["related_commands"] = [
            "az storage container list",
            "az storage blob list"
        ]
    elif intent == "listar_cosmos":
        classification["related_commands"] = [
            "az cosmosdb database list",
            "az cosmosdb collection list"
        ]
    
    return classification