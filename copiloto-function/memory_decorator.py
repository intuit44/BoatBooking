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
    """Decorador inteligente para registrar interacciones con memoria semántica."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(req: azfunc.HttpRequest) -> azfunc.HttpResponse:
            url = req.url or ""
            metodo = req.method.upper()

            # 🧩 Bypass para endpoints de solo lectura
            if any(endpoint in url for endpoint in [
                "/api/historial-interacciones",
                "/api/historial-directo",
                "/api/verificar-cosmos"
            ]):
                logging.info(f"[wrapper] 🧩 Bypass registrar_memoria para {url}")
                return func(req)
            
            # === 1️⃣ Consultar contexto previo antes de ejecutar ===
            try:
                cosmos = CosmosMemoryStore()
                agent_id = req.headers.get("X-Agent-Auth") or req.headers.get("Agent-ID") or "System"
                contexto_prev = cosmos.query_all(limit=10)
                setattr(req, "contexto_prev", contexto_prev)
                logging.info(f"[wrapper] 🧠 Contexto previo encontrado ({len(contexto_prev)}) para agente {agent_id}")
            except Exception as e:
                logging.warning(f"[wrapper] ⚠️ No se pudo consultar memoria previa: {e}")
                setattr(req, "contexto_prev", [])

            # === 2️⃣ Ejecutar función original (con contexto disponible en req.contexto_prev) ===
            response = func(req)

            # === 3️⃣ Registrar interacción en memoria (enriquecida) ===
            try:
                from services.memory_service import memory_service
                input_data = {}
                try:
                    if metodo in ["POST", "PUT", "PATCH"]:
                        input_data = req.get_json() or {}
                    else:
                        input_data = dict(req.params)
                except Exception:
                    input_data = {"method": metodo, "url": url}

                output_data = {}
                try:
                    if response.get_body():
                        output_data = json.loads(response.get_body().decode())
                    else:
                        output_data = {"status_code": response.status_code}
                except Exception:
                    output_data = {"status_code": response.status_code, "raw": True}

                agent_id = (
                    input_data.get("agent_name") or
                    input_data.get("origen") or
                    req.headers.get("Agent-ID") or
                    "System"
                )

                # 🧠 Generar texto semántico enriquecido (antes del guardado)
                if not output_data.get("texto_semantico", "").strip():
                    output_data["texto_semantico"] = (
                        f"Interacción en '{url}' ejecutada por {agent_id}. "
                        f"Éxito: {'✅' if response.status_code == 200 else '❌'}. "
                        f"Mensaje: {output_data.get('mensaje', 'sin mensaje')}."
                    )

                # Guardar en memoria semántica
                memory_service.record_interaction(
                    agent_id=agent_id,
                    source=source,
                    input_data=input_data,
                    output_data=output_data
                )
                logging.info(f"[wrapper] 💾 Interacción registrada correctamente para {source}")
            except Exception as e:
                logging.warning(f"[wrapper] ⚠️ Fallo al registrar interacción {source}: {e}")

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