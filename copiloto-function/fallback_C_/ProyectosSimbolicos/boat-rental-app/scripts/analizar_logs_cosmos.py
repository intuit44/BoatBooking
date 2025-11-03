# -*- coding: utf-8 -*-
import logging
import json
from azure.storage.blob import BlobServiceClient

# ConfiguraciÃ³n de logging
logging.basicConfig(level=logging.INFO)

# ConexiÃ³n a Blob Storage
blob_service_client = BlobServiceClient.from_connection_string("<CONNECTION_STRING>")
container_name = "logs-archive"

# FunciÃ³n para archivar logs

def archive_logs(log_data):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob="cosmos_logs.json")
        blob_client.upload_blob(json.dumps(log_data), overwrite=True)
        logging.info("Logs archivados exitosamente en Blob Storage.")
    except Exception as e:
        logging.error(f"Error al archivar logs: {e}")

# FunciÃ³n para analizar logs

def analyze_logs(logs):
    errors = []
    for log in logs:
        if 'ThroughputExceeded' in log.get('message', ''):
            errors.append(log)
    return errors

# FunciÃ³n principal

def main():
    # SimulaciÃ³n de lectura de logs de Cosmos DB
    logs = [
        {"timestamp": "2025-11-01T12:00:00Z", "message": "ThroughputExceeded: Request rate is too large."},
        {"timestamp": "2025-11-01T12:01:00Z", "message": "Some other log message."}
    ]

    # AnÃ¡lisis de logs
    errors = analyze_logs(logs)
    if errors:
        archive_logs(errors)
    else:
        logging.info("No se encontraron errores 'ThroughputExceeded' en los logs.")

if __name__ == '__main__':
    main()