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
from datetime import datetime, timezone

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
    if not text:
        return ""

    try:
        # Asegurar que el texto es string válido
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')

        # Normalizar unicode y convertir a ASCII seguro
        normalized = unicodedata.normalize("NFKD", str(text))
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.lower()
        ascii_text = re.sub(r"\s+", " ", ascii_text)
        return ascii_text.strip()
    except (UnicodeError, UnicodeEncodeError, UnicodeDecodeError) as e:
        # Fallback seguro en caso de problemas de encoding
        logging.warning(f"Error de encoding en normalize_text: {e}")
        safe_text = str(text).encode(
            'utf-8', errors='replace').decode('utf-8', errors='replace')
        safe_text = re.sub(r'[^\x00-\x7F]+', '', safe_text)  # Solo ASCII
        return safe_text.lower().strip()


def preprocess_text(text: str) -> str:
    """Limpia texto eliminando puntuacion y stopwords para mejorar senal semantica."""
    try:
        normalized = normalize_text(text)
        tokens = re.findall(r"[a-z0-9_/\-]+", normalized)
        filtered = [token for token in tokens if len(
            token) > 2 and token not in STOPWORDS]
        return " ".join(filtered)
    except Exception as e:
        logging.warning(f"Error en preprocess_text: {e}")
        # Fallback seguro
        safe_text = str(text or "").lower()
        safe_text = re.sub(r'[^\w\s\-/]', ' ', safe_text)
        tokens = safe_text.split()
        return " ".join(token for token in tokens if len(token) > 2)


def _looks_like_log_request(cleaned_text: str) -> bool:
    """Heuristica ligera para detectar intenciones de revisar logs/errores."""
    if not cleaned_text:
        return False
    tokens = set(cleaned_text.split())
    log_markers = {
        "log",
        "logs",
        "errores",
        "error",
        "fallos",
        "trazas",
        "traza",
        "stacktrace",
        "crash",
        "exceptions",
    }
    return bool(tokens & log_markers)


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
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv(
            "AZURE_OPENAI_KEY")
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

    def __init__(self, threshold: float = 0.45, high_confidence: float = 0.75):
        # Ejemplos semanticos base para cada intencion
        self.intent_examples = {
            "listar_storage": [
                "mostrar cuentas de almacenamiento",
                "ver storage accounts",
                "listar mis storages en azure",
                "que cuentas de storage tengo configuradas",
                "necesito revisar los recursos de almacenamiento en la suscripcion"
            ],
            "listar_cosmos": [
                "mostrar bases de datos cosmos",
                "ver cuentas cosmos db",
                "listar mis instancias de cosmos",
                "que bases cosmos tengo disponibles",
                "cosmos db disponibles en mi suscripcion"
            ],
            "listar_functions": [
                "mostrar mis function apps",
                "que aplicaciones de funcion estan corriendo",
                "listar los azure functions desplegados",
                "ver las functions activas",
                "apps de funcion registradas"
            ],
            "diagnostico": [
                "diagnosticar el estado del sistema",
                "revisar salud de recursos",
                "hay algun problema con los servicios",
                "verificar infraestructura completa",
                "hacer chequeo general"
            ],
            "correccion": [
                "aplicar correccion en archivo",
                "arreglar bug en el codigo",
                "reparar configuracion que falla",
                "necesito un fix para este error",
                "solicitar correccion puntual"
            ],
            "operacion_archivo": [
                "escribir archivo en blob",
                "leer archivo de configuracion",
                "actualizar requirements txt",
                "crear script en scripts folder",
                "modificar settings json"
            ],
            "ejecucion_cli": [
                "ejecutar comando az",
                "necesito correr script en cli",
                "lanzar comando en terminal",
                "usar ejecutar cli endpoint",
                "mandar instruccion bash"
            ],
            "revisar_logs": [
                "ver logs recientes",
                "revisar errores en app insights",
                "traer logs de function app",
                "consultar stacktrace reciente",
                "buscar trazas de error"
            ],
            "boat_management": [
                "gestionar reservas de embarcaciones",
                "ver alquileres de barcos",
                "administrar yates y lanchas",
                "clientes con reservas activas",
                "actualizar booking de embarcacion"
            ],
            "ayuda_general": [
                "necesito ayuda general",
                "no se que comando usar",
                "ayudame con algo",
                "tengo una duda generica",
                "me puedes orientar"
            ]
        }

        # Mapeo de intenciones a comandos Azure CLI
        self.intent_to_command = {
            "correccion": "intent:aplicar_correccion",
            "diagnostico": "intent:diagnosticar_sistema",
            "operacion_archivo": "intent:operacion_archivo",
            "ejecucion_cli": "intent:ejecutar_cli",
            "boat_management": "intent:gestionar_embarcaciones",
            "listar_storage": "az storage account list --output json",
            "listar_cosmos": "az cosmosdb list --output json",
            "listar_functions": "az functionapp list --output json",
            "listar_resources": "az group list --output json",
            "diagnosticar_sistema": "az resource list --output json",
            "revisar_logs": "intent:revisar_logs",
            "ayuda_general": "az --help"
        }

        self.threshold = threshold
        self.high_confidence = high_confidence
        self.max_examples_per_intent = 40

        # Lazy loading de embeddings - solo calcular cuando se necesiten
        self.intent_embeddings: Dict[str, List[List[float]]] = {}
        self._embeddings_computed = False

    def _ensure_embeddings_computed(self):
        """Lazy loading: calcula embeddings solo cuando se necesitan por primera vez."""
        if not self._embeddings_computed:
            logging.info(
                "[SemanticIntent] Calculando embeddings por primera vez (lazy loading)...")
            for intent, examples in self.intent_examples.items():
                self.intent_embeddings[intent] = []
                for example in examples:
                    cleaned = preprocess_text(example)
                    self.intent_embeddings[intent].append(
                        get_text_embedding(cleaned))
            self._embeddings_computed = True
            logging.info(
                f"[SemanticIntent] Embeddings calculados: {len(self.intent_examples)} intents, {sum(len(examples) for examples in self.intent_examples.values())} ejemplos")

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

        # 🛡️ PROTECCIÓN CONTRA ERRORES DE ENCODING
        try:
            # Sanitizar input para evitar errores charmap
            if isinstance(user_input, bytes):
                user_input = user_input.decode('utf-8', errors='replace')

            # Asegurar string válido y limpio
            user_input = str(user_input).strip()

            # Remover caracteres problemáticos que pueden causar charmap errors
            user_input = user_input.encode(
                'utf-8', errors='replace').decode('utf-8', errors='replace')

        except (UnicodeError, UnicodeEncodeError, UnicodeDecodeError) as e:
            # 🛡️ PROTECCIÓN CONTRA CHARMAP EN LOGGING
            try:
                logging.error(f"Error en clasificacion semantica: {e}")
            except (UnicodeError, UnicodeEncodeError):
                safe_error = str(e).encode(
                    'utf-8', errors='replace').decode('utf-8', errors='replace')
                logging.error(
                    f"Error en clasificacion semantica: {safe_error}")

            safe_error_str = str(e).encode(
                'utf-8', errors='replace').decode('utf-8', errors='replace')
            return {
                "intent": "ayuda_general",
                "confidence": 0.3,
                "command": self.intent_to_command["ayuda_general"],
                "method": "encoding_error_fallback",
                "requires_grounding": True,
                "error": f"Encoding error: {safe_error_str}"
            }

        threshold = self.threshold if threshold is None else threshold

        # Asegurar que los embeddings estén calculados (lazy loading)
        self._ensure_embeddings_computed()

        # 🔥 DETECCIÓN PREVIA DE PALABRAS CLAVE SÓLIDAS
        try:
            input_lower = user_input.lower()
        except Exception as e:
            logging.error(f"Error al convertir a minúsculas: {e}")
            input_lower = str(user_input).lower()

        # Palabras clave de diagnóstico (PRIORIDAD ALTA - antes que corrección)
        if any(kw in input_lower for kw in ["diagnosticar", "diagnóstico", "verificar estado", "comprobar funcionamiento", "revisar salud"]):
            if any(kw in input_lower for kw in ["sistema", "completo", "servicios", "salud", "recursos", "infraestructura"]):
                return {
                    "intent": "diagnostico",
                    "confidence": 0.96,
                    "command": self.intent_to_command.get("diagnostico", "run_diagnostic"),
                    "method": "keyword_detection_diagnostic",
                    "requires_grounding": False
                }

        # Palabras clave de corrección muy específicas
        if any(kw in input_lower for kw in ["corrección", "corregir", "fix", "arreglar", "reparar", "aplicar fix", "aplicar corrección"]):
            if any(kw in input_lower for kw in ["archivo", "línea", "config", "error", "bug", "código"]):
                return {
                    "intent": "correccion",
                    "confidence": 0.95,
                    "command": self.intent_to_command.get("correccion", "apply_fix"),
                    "method": "keyword_detection_strong",
                    "requires_grounding": False
                }        # Palabras clave de boat management específicas
        if any(kw in input_lower for kw in ["reserva", "booking", "alquiler", "embarcación", "barco", "yate", "lancha"]):
            if any(kw in input_lower for kw in ["gestionar", "crear", "procesar", "confirmar", "cancelar", "cliente"]):
                return {
                    "intent": "boat_management",
                    "confidence": 0.90,
                    "command": self.intent_to_command.get("boat_management", "manage_boat"),
                    "method": "keyword_detection_boat",
                    "requires_grounding": False
                }

        # Palabras clave de operación archivo específicas
        if any(kw in input_lower for kw in ["escribir archivo", "leer archivo", "archivo de configuración", "settings.json", "package.json", "requirements.txt"]):
            return {
                "intent": "operacion_archivo",
                "confidence": 0.88,
                "command": self.intent_to_command.get("operacion_archivo", "file_operation"),
                "method": "keyword_detection_file",
                "requires_grounding": False
            }

        # 🛡️ PROCESAMIENTO SEGURO DE TEXTO
        try:
            cleaned_text = preprocess_text(user_input)
            if not cleaned_text:
                return {
                    "intent": "ayuda_general",
                    "confidence": 0.4,
                    "command": self.intent_to_command["ayuda_general"],
                    "method": "empty_after_preprocess",
                    "requires_grounding": True
                }
        except Exception as e:
            logging.error(f"Error en procesamiento de texto: {e}")
            return {
                "intent": "ayuda_general",
                "confidence": 0.3,
                "command": self.intent_to_command["ayuda_general"],
                "method": "text_processing_error",
                "requires_grounding": True,
                "error": f"Text processing error: {str(e)}"
            }

        try:
            user_embedding = get_text_embedding(cleaned_text)
        except Exception as e:
            logging.error(f"Error al obtener embedding: {e}")
            return {
                "intent": "ayuda_general",
                "confidence": 0.3,
                "command": self.intent_to_command["ayuda_general"],
                "method": "embedding_error",
                "requires_grounding": True,
                "error": f"Embedding error: {str(e)}"
            }

        # Heuristica: si el texto parece peticion de logs, favorecer revisar_logs
        if _looks_like_log_request(cleaned_text):
            return {
                "intent": "revisar_logs",
                "confidence": max(0.8, self.threshold + 0.3),
                "command": self.intent_to_command["revisar_logs"],
                "method": "log_heuristic",
                "all_scores": {"revisar_logs": 1.0},
                "requires_grounding": False,
                "preprocessed_input": cleaned_text
            }

        best_intent = None
        best_confidence = 0.0
        intent_scores: Dict[str, float] = {}

        # ⚡ Si no hay ejemplos (diccionario vacío), usar solo keywords detection
        if not self.intent_embeddings:
            return {
                "intent": "ayuda_general",
                "confidence": 0.6,
                "command": self.intent_to_command["ayuda_general"],
                "method": "keywords_only_no_examples",
                "requires_grounding": True,
                "preprocessed_input": cleaned_text
            }

        # Calcular similitud con cada intencion (solo si hay ejemplos)
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

            # Re-calcular embeddings para este intent específico (solo si ya estaban calculados)
            if self._embeddings_computed:
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

# 🚀 Variable global para controlar si ya se pre-computaron los embeddings
_embeddings_precomputed = False


def _ensure_global_embeddings():
    """Asegura que los embeddings se calculen solo una vez globalmente."""
    global _embeddings_precomputed
    if not _embeddings_precomputed:
        try:
            semantic_classifier._ensure_embeddings_computed()
            _embeddings_precomputed = True
            print("[SemanticIntent] Embeddings pre-computados exitosamente")
        except Exception as e:
            print(f"⚠️ Error pre-computando embeddings: {e}")
            # Los embeddings se calcularán en el primer uso si hay error


def classify_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Funcion principal para clasificar intencion del usuario.
    """
    try:
        # Sanitizar input para evitar problemas de encoding
        if user_input:
            user_input = user_input.encode('utf-8', 'replace').decode('utf-8')

        # Asegurar que los embeddings estén pre-computados antes de usar
        _ensure_global_embeddings()
        result = semantic_classifier.classify_intent(user_input)

        # Anadir metadata
        result.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_length": len(user_input),
            "classification_method": "semantic_embeddings"
        })

        # Log con encoding seguro para evitar errores de charmap
        try:
            logging.info(
                f"Intencion clasificada: {result['intent']} (confianza: {result['confidence']:.3f})")
        except UnicodeEncodeError:
            logging.info(f"Intencion clasificada: {result['intent']} (confianza: {result['confidence']:.3f})".encode(
                'utf-8', 'replace').decode('utf-8'))

        return result

    except Exception as exc:
        # 🛡️ PROTECCIÓN CONTRA CHARMAP EN LOGGING
        try:
            error_msg = str(exc)
            logging.error(f"Error en clasificacion semantica: {error_msg}")
        except (UnicodeError, UnicodeEncodeError):
            # Fallback seguro para logging
            safe_error = str(exc).encode(
                'utf-8', errors='replace').decode('utf-8', errors='replace')
            logging.error(f"Error en clasificacion semantica: {safe_error}")

        # Fallback seguro con error sanitizado
        safe_error_str = str(exc).encode(
            'utf-8', errors='replace').decode('utf-8', errors='replace')
        return {
            "intent": "ayuda_general",
            "confidence": 0.1,
            "command": "az --help",
            "method": "error_fallback",
            "error": safe_error_str,
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


def classify_text(text: str, endpoint: str = "", response_data: Optional[Dict[str, Any]] = None, success: bool = True) -> Dict[str, Any]:
    """
    Función de compatibilidad para memory_service - clasifica texto con contexto adicional.
    """
    try:
        # Usar el clasificador principal
        result = classify_user_intent(text)

        # Ajustar intención basado en contexto del endpoint y éxito
        if not success:
            # Si la operación falló, probablemente sea un error
            result["intent"] = "error_endpoint"
            result["confidence"] = 0.9
            result["method"] = "failure_context_override"

        # Contexto del endpoint para mejor clasificación
        if endpoint:
            endpoint_lower = endpoint.lower()
            if "correccion" in endpoint_lower or "fix" in endpoint_lower:
                if result["confidence"] < 0.8:  # Solo si no estamos muy seguros
                    result["intent"] = "correccion"
                    result["confidence"] = max(result["confidence"], 0.7)
                    result["method"] = "endpoint_context_boost"
            elif "diagnostico" in endpoint_lower or "health" in endpoint_lower:
                if result["confidence"] < 0.8:
                    result["intent"] = "diagnostico"
                    result["confidence"] = max(result["confidence"], 0.7)
                    result["method"] = "endpoint_context_boost"

        # Información adicional del response_data
        if response_data and isinstance(response_data, dict):
            # Buscar señales en la respuesta
            response_text = str(response_data.get(
                "respuesta_usuario", "")).lower()
            metadata_text = str(response_data.get("metadata", {})).lower()
            combined_text = f"{response_text} {metadata_text}"

            # Detección específica de correcciones (alta prioridad)
            correction_signals = ["corrección", "fix", "arreglar",
                                  "corregir", "solucionar", "reparar", "rollback", "revertir"]
            if any(signal in combined_text for signal in correction_signals):
                result["intent"] = "correccion"
                result["confidence"] = max(result["confidence"], 0.85)
                result["method"] = "response_correction_boost"

            # Detección de diagnósticos
            elif any(signal in combined_text for signal in ["diagnóstico", "estado", "salud", "verificar", "comprobar", "analizar"]):
                result["intent"] = "diagnostico"
                result["confidence"] = max(result["confidence"], 0.8)
                result["method"] = "response_diagnostic_boost"

        return {
            "tipo": result["intent"],
            "confianza": result["confidence"],
            "metodo": result.get("method", "semantic_classification"),
            "clasificacion_completa": result
        }

    except Exception as e:
        logging.error(f"Error en classify_text: {e}")
        return {
            "tipo": "interaccion",
            "confianza": 0.1,
            "metodo": "error_fallback",
            "error": str(e)
        }
