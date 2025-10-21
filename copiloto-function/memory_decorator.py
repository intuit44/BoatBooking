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

            # 🧩 Bypass SOLO para verificar-cosmos (mantener historial-interacciones activo)
            if "/api/verificar-cosmos" in url:
                logging.info(f"[wrapper] 🧩 Bypass registrar_memoria para {url}")
                return func(req)
            
            # === 1️⃣ Consultar contexto previo GLOBAL antes de ejecutar ===
            try:
                from cosmos_memory_direct import consultar_memoria_cosmos_directo
                memoria_global = consultar_memoria_cosmos_directo(req)
                setattr(req, "memoria_global", memoria_global)
                
                if memoria_global and memoria_global.get("tiene_historial"):
                    logging.info(f"[wrapper] 🌍 Memoria global: {memoria_global['total_interacciones']} interacciones para {memoria_global.get('agent_id')}")
                else:
                    logging.info("[wrapper] 📝 Sin memoria global previa")
            except Exception as e:
                logging.warning(f"[wrapper] ⚠️ No se pudo consultar memoria global: {e}")
                setattr(req, "memoria_global", None)

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

                # 🌍 Extraer agent_id para memoria global
                agent_id = (
                    req.headers.get("Agent-ID") or
                    req.headers.get("X-Agent-ID") or
                    input_data.get("agent_id") or
                    input_data.get("agent_name") or
                    "GlobalAgent"
                )

                # 🧠 Generar texto semántico enriquecido para memoria global
                if not output_data.get("texto_semantico", "").strip():
                    endpoint_name = url.split('/')[-1] if '/' in url else source
                    output_data["texto_semantico"] = (
                        f"[{agent_id}] Ejecutó '{endpoint_name}' con éxito: {'✅' if response.status_code == 200 else '❌'}. "
                        f"Respuesta: {str(output_data.get('mensaje', output_data.get('resultado', 'procesado')))[:100]}..."
                    )

                # Guardar en memoria semántica
                memory_service.record_interaction(
                    agent_id=agent_id,
                    source=source,
                    input_data=input_data,
                    output_data=output_data
                )
                logging.info(f"[wrapper] 💾 Interacción registrada en memoria global para agente {agent_id}")
            except Exception as e:
                logging.warning(f"[wrapper] ⚠️ Fallo al registrar en memoria global {source}: {e}")

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