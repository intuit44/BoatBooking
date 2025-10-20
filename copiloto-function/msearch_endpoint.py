import azure.functions as func
import json
import logging
from datetime import datetime
from utils_helpers import get_run_id

def register_msearch_endpoint(app):
    """Registra el endpoint msearch en la app principal"""
    
    @app.function_name(name="msearch")
    @app.route(route="msearch", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def msearch_http(req: func.HttpRequest) -> func.HttpResponse:
        """Endpoint de búsqueda semántica avanzada para análisis de código"""
        
        run_id = get_run_id()
        
        try:
            # Validar JSON de entrada
            try:
                body = req.get_json()
                if body is None:
                    body = {}
            except ValueError:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": "JSON inválido en el cuerpo de la solicitud",
                        "run_id": run_id
                    }, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=400
                )
            
            # Importar y procesar solicitud
            try:
                from endpoints.msearch import process_msearch_request
                result = process_msearch_request(body)
            except ImportError:
                result = {
                    "exito": False,
                    "error": "Módulo de análisis semántico no disponible",
                    "campos_aceptados": ["file_path", "ruta", "path", "content", "contenido", "search_type", "tipo", "pattern", "patron"]
                }
            
            result["run_id"] = run_id
            result["timestamp"] = datetime.now().isoformat()
            
            # Determinar código de estado
            status_code = 200 if result.get("exito") else 400
            
            return func.HttpResponse(
                json.dumps(result, ensure_ascii=False, indent=2),
                mimetype="application/json",
                status_code=status_code
            )
        
        except Exception as e:
            logging.exception(f"[{run_id}] Error en msearch: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": f"Error interno: {str(e)}",
                    "error_type": type(e).__name__,
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=500
            )