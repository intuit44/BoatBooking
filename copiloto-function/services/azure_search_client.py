# -*- coding: utf-8 -*-
"""
Azure Search Client - Cliente con Managed Identity
"""
import os
import logging
from typing import Dict, List, Any, Optional
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


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

    def search(self, query: str, top: int = 10, filters: Optional[str] = None) -> Dict[str, Any]:
        """Buscar documentos en el índice"""
        try:
            results = self.client.search(search_text=query, top=top, filter=filters)
            documentos = [doc for doc in results]
            return {"exito": True, "total": len(documentos), "documentos": documentos}
        except Exception as e:
            logging.error(f"Error en búsqueda: {e}")
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
