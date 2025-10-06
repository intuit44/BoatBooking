# -*- coding: utf-8 -*-
"""
Memory Route Wrapper - Fábrica de decoradores para Azure Functions
Envuelve app.route para aplicar memoria automáticamente sin cambiar la firma original.
"""

import logging
from typing import Callable, Any
import azure.functions as func

def memory_route(app: func.FunctionApp) -> Callable:
    """
    Fábrica que envuelve app.route para aplicar memoria automáticamente.
    
    Args:
        app: Instancia de FunctionApp
        
    Returns:
        Decorador compatible con app.route que aplica memoria automáticamente
    """
    # Guardar referencia al método original
    original_route = app.route
    
    def route_with_memory(*args, **kwargs) -> Callable:
        """
        Envuelve app.route para aplicar memoria automáticamente.
        Mantiene la misma firma que el método original.
        """
        def decorator(func_ref: Callable) -> Callable:
            try:
                # Extraer información de la ruta para generar source_name
                route_path = kwargs.get("route", "")
                if isinstance(route_path, str):
                    source_name = route_path.strip("/").replace("-", "_") or "root"
                else:
                    source_name = func_ref.__name__ if hasattr(func_ref, '__name__') else "unknown"
                
                # Importar registrar_memoria dinámicamente para evitar dependencias circulares
                try:
                    from services.memory_decorator import registrar_memoria
                    
                    # Aplicar el decorador de memoria
                    func_with_memory = registrar_memoria(source_name)(func_ref)
                    
                    logging.info(f"✅ Memoria aplicada automáticamente a endpoint: {route_path} -> {source_name}")
                    
                except ImportError as e:
                    logging.warning(f"⚠️ No se pudo importar registrar_memoria: {e}")
                    logging.warning("Usando función original sin memoria")
                    func_with_memory = func_ref
                except Exception as e:
                    logging.error(f"❌ Error aplicando memoria a {route_path}: {e}")
                    logging.warning("Usando función original sin memoria")
                    func_with_memory = func_ref
                
                # Aplicar el decorador original de Azure Functions
                return original_route(*args, **kwargs)(func_with_memory)
                
            except Exception as e:
                logging.error(f"💥 Error crítico en memory_route wrapper: {e}")
                # Fallback: usar decorador original sin memoria
                return original_route(*args, **kwargs)(func_ref)
        
        return decorator
    
    return route_with_memory


def apply_memory_wrapper(app: func.FunctionApp) -> None:
    """
    Aplica el wrapper de memoria a una instancia de FunctionApp.
    
    Args:
        app: Instancia de FunctionApp a modificar
    """
    try:
        # Verificar que app.route existe y es callable
        if not hasattr(app, 'route') or not callable(app.route):
            logging.error("❌ app.route no existe o no es callable")
            return
        
        # Aplicar el wrapper
        app.route = memory_route(app)
        
        logging.info("🧠 Memory wrapper aplicado exitosamente a app.route")
        
    except Exception as e:
        logging.error(f"💥 Error aplicando memory wrapper: {e}")
        logging.warning("La aplicación continuará sin memoria automática")


# Función de conveniencia para uso directo
def wrap_function_app_with_memory(app: func.FunctionApp) -> func.FunctionApp:
    """
    Envuelve una FunctionApp con memoria automática y la retorna.
    
    Args:
        app: FunctionApp original
        
    Returns:
        La misma FunctionApp pero con memoria automática aplicada
    """
    apply_memory_wrapper(app)
    return app