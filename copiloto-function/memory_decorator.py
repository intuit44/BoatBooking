# -*- coding: utf-8 -*-
"""
Decorador universal para registro automático en memoria
"""
import logging
import json
from functools import wraps
from typing import Any, Callable
import azure.functions as azfunc
from services.memory_service import CosmosMemoryStore

def registrar_memoria(source: str):
    """Decorador para registrar automáticamente interacciones en memoria"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(req: azfunc.HttpRequest) -> azfunc.HttpResponse:
            # 1️⃣ Consultar contexto previo antes de ejecutar
            try:
                cosmos = CosmosMemoryStore()
                agent_id = req.headers.get("X-Agent-Auth", "System")
                contexto_prev = cosmos.query(agent_id, limit=5)
                setattr(req, "contexto_prev", contexto_prev)
            except Exception as e:
                logging.warning(f"[memoria] No se pudo consultar memoria previa: {e}")
                setattr(req, "contexto_prev", [])
            
            # Ejecutar función original
            response = func(req)
            
            # Registrar en memoria después de la ejecución
            try:
                from services.memory_service import memory_service
                
                # Extraer datos de entrada
                input_data = {}
                try:
                    if req.method in ["POST", "PUT", "PATCH"]:
                        input_data = req.get_json() or {}
                    else:
                        input_data = dict(req.params)
                except:
                    input_data = {"method": req.method, "url": req.url}
                
                # Extraer datos de salida
                output_data = {}
                try:
                    if response.get_body():
                        output_data = json.loads(response.get_body().decode())
                    else:
                        output_data = {"status_code": response.status_code}
                except:
                    output_data = {"status_code": response.status_code, "raw": True}
                
                # Determinar agent_id
                agent_id = "System"
                if isinstance(input_data, dict):
                    agent_id = (input_data.get("agent_name") or 
                              input_data.get("origen") or 
                              req.headers.get("X-Agent-Auth", "System"))
                
                # Registrar interacción
                memory_service.record_interaction(
                    agent_id=agent_id,
                    source=source,
                    input_data=input_data,
                    output_data=output_data
                )
                
            except Exception as e:
                logging.warning(f"[memoria] Fallo al registrar {source}: {e}")
            
            return response
        return wrapper
    return decorator

# Wrapper para app.route que aplica automáticamente el decorador
def create_memory_wrapper(original_app):
    """Crea wrapper que aplica automáticamente registro de memoria"""
    
    original_route = original_app.route
    
    def route_with_memory(route: str, methods=None, auth_level=None, **kwargs):
        def decorator(func: Callable) -> Callable:
            # Generar source name desde la ruta
            source_name = route.replace("/", "_").replace("-", "_").strip("_")
            if source_name.startswith("api_"):
                source_name = source_name[4:]  # Remover "api_"
            
            # Aplicar decorador de memoria
            wrapped_func = registrar_memoria(source_name)(func)
            
            # Aplicar decorador original de Azure Functions
            return original_route(route=route, methods=methods, auth_level=auth_level, **kwargs)(wrapped_func)
        
        return decorator
    
    return route_with_memory