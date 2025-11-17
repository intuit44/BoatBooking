# -*- coding: utf-8 -*-
"""
Azure Search Client - Cliente con Búsqueda Vectorial Semántica
"""
import os
import logging
from typing import Dict, List, Any, Optional
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from datetime import datetime, timezone

_search_service_instance = None


class AzureSearchService:
    """Cliente para Azure AI Search usando Managed Identity o API Key (fallback)."""

    def __init__(self):
        self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        self.index_name = "agent-memory-index"
        if not self.endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT no configurado")

        search_key = os.environ.get("AZURE_SEARCH_KEY")

        if search_key:
            credential = AzureKeyCredential(search_key)
            logging.info("🔑 Azure Search: Usando API Key (desarrollo local)")
        else:
            credential = DefaultAzureCredential()
            logging.info("🔐 Azure Search: Usando Managed Identity")

        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=credential
        )

        # Cliente OpenAI para generar embeddings
        openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not openai_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT no está definido en las variables de entorno")

        self.openai_client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_KEY"),
            api_version="2024-02-01",
            azure_endpoint=openai_endpoint
        )

        self.embedding_model = os.environ.get(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

    def _generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding vectorial para el texto usando Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=texto,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            return []

    def _calcular_score_hibrido(self, doc: Dict[str, Any]) -> float:
        """Calcula score híbrido combinando @search.score con factor de recencia."""

        try:
            raw_score = doc.get("@search.score", 0)
            score = float(raw_score) if raw_score is not None else 0.0

            ts = doc.get("timestamp", "")
            if not ts:
                return score

            # Normalizar ISO Z -> +00:00 para fromisoformat
            if ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")

            dt = datetime.fromisoformat(ts)
            # Asegurar timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            edad_horas = (now - dt.astimezone(timezone.utc)
                          ).total_seconds() / 3600.0

            # Factores por recencia (ajustables)
            if edad_horas > 168:        # > 7 días
                factor = 0.5
            elif edad_horas > 48:       # > 2 días
                factor = 0.7
            elif edad_horas > 24:       # > 1 día
                factor = 0.85
            else:
                factor = 1.0

            return score * factor
        except Exception:
            # En caso de cualquier error, devolver el score original si existe
            try:
                return float(doc.get("@search.score", 0))
            except Exception:
                return 0.0

    def search(self, query: str, top: int = 10, filters: Optional[str] = None) -> Dict[str, Any]:
        """Búsqueda vectorial semántica usando embeddings.
        Postprocesa resultados aplicando orden híbrido (score × recencia) y
        opcionalmente filtra documentos demasiado antiguos mediante
        AZURE_SEARCH_MAX_ITEM_AGE_HOURS (env)."""

        try:
            # 1. Generar embedding de la consulta
            query_vector = self._generar_embedding(query)
            if not query_vector:
                logging.warning(
                    "⚠️ No se pudo generar embedding, usando búsqueda de texto")
                results = self.client.search(
                    search_text=query, top=top, filter=filters)
                documentos = [doc for doc in results]
                return {"exito": True, "total": len(documentos), "documentos": documentos}

            # 2. Crear consulta vectorial
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top,
                fields="vector"
            )

            # 3. Ejecutar búsqueda vectorial
            logging.info(
                f"🔍 Búsqueda vectorial: '{query}' (dim={len(query_vector)})")
            results = self.client.search(
                search_text=None,  # Solo búsqueda vectorial
                vector_queries=[vector_query],
                filter=filters,
                top=top
            )

            # Materializar resultados
            documentos_raw = [doc for doc in results]
            logging.info(
                f"🔎 Recuperados {len(documentos_raw)} documentos desde Azure Search")

            # Nota: se desactiva el filtrado por edad (AZURE_SEARCH_MAX_ITEM_AGE_HOURS).
            # La recencia seguirá influyendo en el orden mediante _calcular_score_hibrido,
            # pero no eliminaremos documentos por antigüedad en este punto.

            # 5. Ordenar por score híbrido (similitud × recencia)
            documentos = sorted(
                documentos_raw, key=self._calcular_score_hibrido, reverse=True)
            logging.info(
                f"✅ Ordenados {len(documentos)} documentos por score híbrido")

            return {"exito": True, "total": len(documentos), "documentos": documentos}

        except Exception as e:
            logging.error(f"Error en búsqueda vectorial: {e}")
            return {"exito": False, "error": str(e)}

    def upload_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Subir documentos al índice"""
        try:
            result = self.client.upload_documents(documents=documents)
            return {
                "exito": True,
                "documentos_subidos": len(documents),
                "resultado": str(result)
            }
        except Exception as e:
            logging.error(f"Error subiendo documentos: {e}")
            return {"exito": False, "error": str(e)}

    # 🔹 Alias para compatibilidad con el indexador
    def indexar_documentos(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Alias de upload_documents para compatibilidad con el indexador."""
        return self.upload_documents(documents)

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Obtener un documento por ID"""
        try:
            doc = self.client.get_document(key=doc_id)
            return {"exito": True, "documento": doc}
        except Exception as e:
            logging.error(f"Error obteniendo documento: {e}")
            return {"exito": False, "error": str(e)}

    def delete_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Eliminar documentos del índice"""
        try:
            docs = [{"id": doc_id} for doc_id in doc_ids]
            result = self.client.delete_documents(documents=docs)
            return {"exito": True, "documentos_eliminados": len(doc_ids), "resultado": str(result)}
        except Exception as e:
            logging.error(f"Error eliminando documentos: {e}")
            return {"exito": False, "error": str(e)}

    def eliminar_documentos(self, docs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Alias que acepta lista de dicts con 'id'"""
        doc_ids = [doc["id"] for doc in docs if "id" in doc]
        return self.delete_documents(doc_ids)


def get_search_service() -> AzureSearchService:
    """Obtiene una instancia singleton del cliente de Azure Search."""
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = AzureSearchService()
    return _search_service_instance
