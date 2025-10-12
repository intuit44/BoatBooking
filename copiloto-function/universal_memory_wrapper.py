# -*- coding: utf-8 -*-
"""
Universal Memory Wrapper - Intercepta TODAS las respuestas para agregar memoria automáticamente
"""

import json
import logging
from typing import Any
import azure.functions as func

def wrap_response_with_memory(original_response: Any, req: func.HttpRequest) -> Any:
    """
    Envuelve cualquier respuesta para agregar información de memoria automáticamente
    """
    try:
        # Solo procesar HttpResponse
        if not isinstance(original_response, func.HttpResponse):
            return original_response
        
        # Solo procesar JSON responses
        if not original_response.mimetype == "application/json":
            return original_response
        
        # Obtener el body actual
        try:
            body_bytes = original_response.get_body()
            if not body_bytes:
                return original_response
            
            body_text = body_bytes.decode('utf-8')
            response_data = json.loads(body_text)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            return original_response
        
        # Agregar memoria automáticamente
        try:
            from memory_helpers import agregar_memoria_a_respuesta
            enhanced_data = agregar_memoria_a_respuesta(response_data, req)
            
            # Crear nueva respuesta con memoria
            return func.HttpResponse(
                json.dumps(enhanced_data, ensure_ascii=False),
                mimetype="application/json",
                status_code=original_response.status_code,
                headers=dict(original_response.headers) if hasattr(original_response, 'headers') else {}
            )
            
        except Exception as e:
            logging.warning(f"Error agregando memoria a respuesta: {e}")
            return original_response
            
    except Exception as e:
        logging.warning(f"Error en wrap_response_with_memory: {e}")
        return original_response

def apply_universal_memory_wrapper(app: func.FunctionApp) -> None:
    """
    Aplica wrapper universal de memoria que intercepta TODAS las respuestas
    """
    try:
        # Guardar referencia al método original
        original_route = app.route
        
        def enhanced_route(*args, **kwargs):
            def decorator(func_ref):
                def wrapper(req):
                    # Ejecutar función original
                    response = func_ref(req)
                    
                    # Envolver respuesta con memoria
                    enhanced_response = wrap_response_with_memory(response, req)
                    
                    return enhanced_response
                
                # Aplicar decorador original de Azure Functions
                return original_route(*args, **kwargs)(wrapper)
            
            return decorator
        
        # Reemplazar app.route con la versión mejorada
        app.route = enhanced_route
        
        logging.info("🧠 Universal Memory Wrapper aplicado - TODAS las respuestas tendrán memoria")
        
    except Exception as e:
        logging.error(f"Error aplicando Universal Memory Wrapper: {e}")