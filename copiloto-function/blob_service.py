# -*- coding: utf-8 -*-
"""
Servicio de Blob Storage - Funciones auxiliares para listar y leer blobs
"""
import os
import logging
from azure.storage.blob import BlobServiceClient
from typing import List, Dict, Optional


class BlobService:
    """Encapsula operaciones básicas sobre Azure Blob Storage."""

    def __init__(self, connection_string: Optional[str] = None, container_name: str = "boat-rental-project"):
        """
        Inicializa el servicio. Si no se provee connection_string, se lee de la variable de entorno
        AzureWebJobsStorage.
        """
        self.connection_string = connection_string or os.getenv(
            "AzureWebJobsStorage")
        if not self.connection_string:
            raise ValueError("AzureWebJobsStorage no configurado")
        self.container_name = container_name
        self._client: BlobServiceClient = BlobServiceClient.from_connection_string(
            self.connection_string)
        self._container_client = self._client.get_container_client(
            self.container_name)

    @classmethod
    def from_env(cls, container_name: str = "boat-rental-project"):
        """Conveniencia para crear instancia usando la variable de entorno."""
        return cls(connection_string=None, container_name=container_name)

    def listar_blobs(self, prefix: str = "", top: int = 10) -> List[Dict]:
        """Lista blobs con un prefijo dado, limitado a `top` resultados."""
        try:
            blobs = []
            for blob in self._container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if getattr(blob, "last_modified", None) else None
                })
                if len(blobs) >= top:
                    break
            return blobs
        except Exception as e:
            logging.error(f"Error listando blobs (prefijo={prefix}): {e}")
            return []

    def leer_blob(self, blob_name: str) -> Optional[str]:
        """Lee y devuelve el contenido de un blob como texto UTF-8."""
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            contenido = blob_client.download_blob().readall()
            return contenido.decode("utf-8")
        except Exception as e:
            logging.error(f"Error leyendo blob {blob_name}: {e}")
            return None
