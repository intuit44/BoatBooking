# -*- coding: utf-8 -*-
import logging

class ErrorHandler:
    @staticmethod
    def log_connection_error(e: Exception):
        logging.error(f"Error de conexión a Cosmos DB: {str(e)}")
        return "Error de conexión a Cosmos DB. Verifique las credenciales y la configuración."

    @staticmethod
    def log_event_error(event: dict, e: Exception):
        logging.error(f"Error al guardar el evento en Cosmos DB: {str(e)}")
        logging.error(f"Evento que falló: {event}")
        return "Error al guardar el evento en Cosmos DB."

    @staticmethod
    def log_query_error(e: Exception):
        logging.error(f"Error al consultar Cosmos DB: {str(e)}")
        return "Error al consultar Cosmos DB."

    @staticmethod
    def log_general_error(e: Exception):
        logging.error(f"Error general: {str(e)}")
        return "Ocurrió un error inesperado."
