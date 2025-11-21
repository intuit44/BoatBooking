#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clasificador de intencion semantica basado en embeddings.
Sin dependencia de palabras clave predefinidas.
"""

import logging
import hashlib
import os
import re
import unicodedata
from functools import lru_cache
from typing import Dict, Any, List, Optional
from datetime import datetime

# Stopwords basicos para reducir ruido en espanol/ingles
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "al",
    "en", "para", "por", "con", "sin", "sobre", "que", "como", "cual", "cuales",
    "cuando", "donde", "yo", "tu", "mi", "mis", "su", "sus", "lo", "se", "me", "te",
    "este", "esta", "esto", "estos", "estas", "the", "and", "or", "of", "to", "in",
    "on", "a", "an", "is", "it", "for", "from", "at", "by", "with", "about", "as",
    "that", "this", "these", "those"
}


def normalize_text(text: str) -> str:
    """Normaliza texto: minusculas, elimina acentos y colapsa espacios."""
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"\s+", " ", ascii_text)
    return ascii_text.strip()


def preprocess_text(text: str) -> str:
    """Limpia texto eliminando puntuacion y stopwords para mejorar senal semantica."""
    normalized = normalize_text(text)
    tokens = re.findall(r"[a-z0-9_/\-]+", normalized)
    filtered = [token for token in tokens if len(
        token) > 2 and token not in STOPWORDS]
    return " ".join(filtered)


def _hash_embedding(text: str) -> List[float]:
    """Embedding determinista basado en hash (fallback rapido y reproducible)."""
    hash_obj = hashlib.md5((text or "").encode())
    hash_hex = hash_obj.hexdigest()
    embedding: List[float] = []

    for i in range(0, len(hash_hex), 2):
        val = int(hash_hex[i:i+2], 16) / 255.0
        embedding.append(val)

    while len(embedding) < 384:
        embedding.extend(embedding[:min(len(embedding), 384 - len(embedding))])

    return embedding[:384]


@lru_cache(maxsize=2048)
def get_text_embedding(text: str) -> List[float]:
    """
    Obtiene embeddings usando Azure OpenAI text-embedding-3-large.
    Fallback a hash si falla.
    """
    cleaned_text = text or ""
    
    try:
        from openai import AzureOpenAI
        
        # Soportar ambos formatos de variable
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not endpoint:
            return _hash_embedding(cleaned_text)
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=endpoint
        )
        
        # Usar text-embedding-3-large que ya tienes desplegado
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=cleaned_text
        )
        
        embedding = response.data[0].embedding
        if embedding:
            return list(embedding)
            
    except Exception as exc:
        logging.debug(f"Fallback a hash embedding: {exc}")
    
    return _hash_embedding(cleaned_text)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcula similitud coseno entre dos vectores."""
    try:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
    except Exception:
        return 0.0


class SemanticIntentClassifier:
    """Clasificador de intencion basado en similitud semantica."""

    def __init__(self, threshold: float = 0.32, high_confidence: float = 0.72):
        # Intenciones base con ejemplos semanticos diversos
        self.intent_examples = {
            "listar_storage": [
                "mostrar cuentas de almacenamiento",
                "ver storage accounts",
                "listar almacenamiento azure",
                "que cuentas de storage tengo",
                "mostrar mis storages",
                "ver todas las cuentas de almacenamiento"
            ],
            "listar_cosmos": [
                "mostrar bases de datos cosmos",
                "ver cuentas cosmos db",
                "listar cosmos database",
                "que bases cosmos tengo",
                "mostrar mis cosmos",
                "ver todas las cuentas de cosmos"
            ],
            "listar_functions": [
                "mostrar function apps",
                "ver aplicaciones de funcion",
                "listar functions azure",
                "que functions tengo corriendo",
                "mostrar mis funciones",
                "ver todas las function apps"
            ],
            "listar_resources": [
                "mostrar recursos azure",
                "ver todos mis recursos",
                "listar resource groups",
                "que recursos tengo",
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
                "no se que hacer",
                "necesito ayuda con azure",
                "no tengo idea como empezar",
                "ayudame con comandos",
                "que puedo hacer aqui",
                "guiame por favor"
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

        self.threshold = threshold
        self.high_confidence = high_confidence
        self.max_examples_per_intent = 40

        # Pre-calcular embeddings de ejemplos
        self.intent_embeddings: Dict[str, List[List[float]]] = {}
        self._precompute_embeddings()

    def _precompute_embeddings(self):
        """Pre-calcula embeddings de todos los ejemplos."""
        for intent, examples in self.intent_examples.items():
            self.intent_embeddings[intent] = []
            for example in examples:
                cleaned = preprocess_text(example)
                self.intent_embeddings[intent].append(
                    get_text_embedding(cleaned))

    def classify_intent(self, user_input: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Clasifica la intencion del usuario basado en similitud semantica.
        """
        if not user_input or not user_input.strip():
            return {
                "intent": "ayuda_general",
                "confidence": 0.5,
                "command": self.intent_to_command["ayuda_general"],
                "method": "fallback",
                "requires_grounding": True
            }

        threshold = self.threshold if threshold is None else threshold
        cleaned_text = preprocess_text(user_input)
        if not cleaned_text:
            return {
                "intent": "ayuda_general",
                "confidence": 0.4,
                "command": self.intent_to_command["ayuda_general"],
                "method": "empty_after_preprocess",
                "requires_grounding": True
            }

        user_embedding = get_text_embedding(cleaned_text)

        best_intent = None
        best_confidence = 0.0
        intent_scores: Dict[str, float] = {}

        # Calcular similitud con cada intencion
        for intent, embeddings in self.intent_embeddings.items():
            max_similarity = 0.0

            # Tomar la maxima similitud con cualquier ejemplo de esta intencion
            for example_embedding in embeddings:
                similarity = cosine_similarity(
                    user_embedding, example_embedding)
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
                "requires_grounding": True,
                "preprocessed_input": cleaned_text
            }

        method = "semantic_similarity_azure_embeddings"

        return {
            "intent": best_intent or "ayuda_general",
            "confidence": best_confidence,
            "command": self.intent_to_command[best_intent or "ayuda_general"],
            "method": method,
            "all_scores": intent_scores,
            # Grounding si confianza media
            "requires_grounding": best_confidence < self.high_confidence,
            "preprocessed_input": cleaned_text
        }

    def add_learning_example(self, user_input: str, correct_intent: str, command_used: str):
        """
        Anade un ejemplo de aprendizaje para mejorar la clasificacion.
        """
        if correct_intent in self.intent_examples:
            cleaned_input = user_input.lower().strip()
            self.intent_examples[correct_intent].append(cleaned_input)

            # Mantener tamano acotado para evitar sobre-ajuste
            if len(self.intent_examples[correct_intent]) > self.max_examples_per_intent:
                self.intent_examples[correct_intent] = self.intent_examples[correct_intent][-self.max_examples_per_intent:]

            # Actualizar comando si es diferente
            if command_used and command_used != self.intent_to_command.get(correct_intent):
                self.intent_to_command[correct_intent] = command_used

            # Re-calcular embeddings para esta intencion
            self.intent_embeddings[correct_intent] = []
            for example in self.intent_examples[correct_intent]:
                cleaned_example = preprocess_text(example)
                self.intent_embeddings[correct_intent].append(
                    get_text_embedding(cleaned_example))

            logging.info(
                f"Aprendizaje anadido: '{user_input}' -> {correct_intent}")
            return True

        return False


# Instancia global del clasificador
semantic_classifier = SemanticIntentClassifier()


def classify_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Funcion principal para clasificar intencion del usuario.
    """
    try:
        result = semantic_classifier.classify_intent(user_input)

        # Anadir metadata
        result.update({
            "timestamp": datetime.now().isoformat(),
            "input_length": len(user_input),
            "classification_method": "semantic_embeddings"
        })

        logging.info(
            f"Intencion clasificada: {result['intent']} (confianza: {result['confidence']:.3f})")

        return result

    except Exception as exc:
        logging.error(f"Error en clasificacion semantica: {exc}")

        # Fallback seguro
        return {
            "intent": "ayuda_general",
            "confidence": 0.1,
            "command": "az --help",
            "method": "error_fallback",
            "error": str(exc),
            "requires_grounding": True
        }


def should_use_grounding(classification: Dict[str, Any]) -> bool:
    """
    Determina si se debe usar Bing Grounding basado en la clasificacion.
    """
    return (
        classification.get("requires_grounding", False) or
        classification.get("confidence", 0) < 0.7 or
        classification.get("intent") == "ayuda_general" or
        "error" in classification
    )


def enhance_with_context(classification: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mejora la clasificacion con contexto adicional.
    """
    if context is None:
        context = {}

    # Ajustar confianza basado en contexto
    if context.get("previous_intent") == classification.get("intent"):
        classification["confidence"] = min(
            1.0, classification.get("confidence", 0) + 0.1)
        classification["context_boost"] = True

    # Anadir sugerencias relacionadas
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
