# -*- coding: utf-8 -*-
# Código para leer archivos de Blob Storage

import os
from azure.storage.blob import BlobServiceClient

# Configuración de conexión
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Función para leer un archivo

def leer_archivo(nombre_archivo):
    try:
        # Obtener el contenedor
        container_name = 'boat-rental-project'
        container_client = blob_service_client.get_container_client(container_name)

        # Leer el blob
        blob_client = container_client.get_blob_client(nombre_archivo)
        blob_data = blob_client.download_blob()
        return blob_data.readall()
    except Exception as e:
        print(f'Error al leer el archivo: {e}')  

# Ejemplo de uso
if __name__ == '__main__':
    archivo = 'thread_fallback_session_1763388347.json'
    contenido = leer_archivo(archivo)
    print(contenido)