"""
Registrador del endpoint /api/guardar-memoria
"""

import azure.functions as func
from endpoint_guardar_memoria import guardar_memoria_http

def register_endpoint(app):
    """Registra el endpoint en la app de Azure Functions"""
    
    @app.function_name(name="guardar_memoria_http")
    @app.route(route="guardar-memoria", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def guardar_memoria_wrapper(req: func.HttpRequest) -> func.HttpResponse:
        return guardar_memoria_http(req)
    
    return app
