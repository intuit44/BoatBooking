# -*- coding: utf-8 -*-
"""
Clasificador Semántico de Intención
Usa embeddings + similitud coseno para detectar intención sin regex
"""
import logging
import numpy as np
from typing import Dict, List, Tuple


# Dataset de entrenamiento: ejemplos por intención
DATASET_INTENCIONES = {
    "resumen_conversacion": [
        "en qué estábamos",
        "qué hicimos",
        "dame un resumen",
        "qué estuvimos haciendo",
        "recuérdame lo que hablamos",
        "cuál fue lo último",
        "qué quedamos",
        "resumen de la conversación",
        "recap",
        "qué fue lo último que hicimos",
    ],
    "leer_threads": [
        "lee la conversación anterior",
        "muestra las conversaciones pasadas",
        "valida con las conversaciones anteriores",
        "revisa el historial de chat",
        "qué dijimos en la última conversación",
        "lee el thread anterior",
        "muestra los threads guardados",
    ],
    "historial_acciones": [
        "qué archivos leímos",
        "qué comandos ejecutamos",
        "muestra las acciones realizadas",
        "qué endpoints usamos",
        "historial de operaciones",
        "qué hicimos con Azure",
    ],
    "sin_contexto": [
        "no tengo información",
        "no sé de qué hablas",
        "no hay contexto",
        "parece que no tengo datos",
        "no encuentro información previa",
    ]
}


class ClasificadorIntencion:
    def __init__(self):
        self.embeddings_cache = {}
        self.umbral_confianza = 0.75
        self._inicializar_embeddings()

    def _inicializar_embeddings(self):
        """Genera embeddings del dataset una sola vez"""
        try:
            from embedding_generator import generar_embedding

            for intencion, ejemplos in DATASET_INTENCIONES.items():
                self.embeddings_cache[intencion] = []
                for ejemplo in ejemplos:
                    emb = generar_embedding(ejemplo)
                    if emb:
                        self.embeddings_cache[intencion].append({
                            "texto": ejemplo,
                            "embedding": np.array(emb)
                        })

            logging.info(
                f"✅ Clasificador inicializado: {len(self.embeddings_cache)} intenciones")
        except Exception as e:
            logging.warning(f"⚠️ Error inicializando clasificador: {e}")

    def clasificar(self, mensaje: str) -> Dict:
        """
        Clasifica la intención del mensaje usando similitud coseno.

        Returns:
            {
                "requiere_memoria": bool,
                "intencion": str,
                "confianza": float,
                "accion_sugerida": str,
                "ejemplo_similar": str
            }
        """
        if not mensaje or not isinstance(mensaje, str):
            return {"requiere_memoria": False, "intencion": None, "confianza": 0.0}

        try:
            from embedding_generator import generar_embedding

            # Generar embedding del mensaje
            mensaje_emb = generar_embedding(mensaje)
            if not mensaje_emb:
                return {"requiere_memoria": False, "intencion": None, "confianza": 0.0}

            mensaje_vec = np.array(mensaje_emb)

            # Calcular similitud con cada intención
            mejor_match = {"intencion": None, "confianza": 0.0, "ejemplo": ""}

            for intencion, ejemplos in self.embeddings_cache.items():
                for ejemplo_data in ejemplos:
                    similitud = self._similitud_coseno(
                        mensaje_vec, ejemplo_data["embedding"])

                    if similitud > mejor_match["confianza"]:
                        mejor_match = {
                            "intencion": intencion,
                            "confianza": float(similitud),
                            "ejemplo": ejemplo_data["texto"]
                        }

            # Determinar si requiere memoria
            requiere_memoria = mejor_match["confianza"] >= self.umbral_confianza

            resultado = {
                "requiere_memoria": requiere_memoria,
                "intencion": mejor_match["intencion"] if requiere_memoria else None,
                "confianza": mejor_match["confianza"],
                "accion_sugerida": self._mapear_accion(mejor_match["intencion"]) if requiere_memoria else None,
                "ejemplo_similar": mejor_match["ejemplo"]
            }

            logging.info(
                f"🎯 Clasificación: {resultado['intencion']} (confianza: {resultado['confianza']:.2f})")
            return resultado

        except Exception as e:
            logging.error(f"Error clasificando intención: {e}")
            return {"requiere_memoria": False, "intencion": None, "confianza": 0.0}

    def _similitud_coseno(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcula similitud coseno entre dos vectores"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _mapear_accion(self, intencion: str) -> str:
        """Mapea intención a acción concreta"""
        mapeo = {
            "resumen_conversacion": "historial_interacciones",
            "leer_threads": "listar_threads_recientes",
            "historial_acciones": "historial_interacciones",
            "sin_contexto": "listar_threads_recientes"
        }
        return mapeo.get(intencion, "historial_interacciones")


# Instancia global (singleton)
_clasificador = None


def get_clasificador() -> ClasificadorIntencion:
    """Obtiene instancia singleton del clasificador"""
    global _clasificador
    if _clasificador is None:
        _clasificador = ClasificadorIntencion()
    return _clasificador
