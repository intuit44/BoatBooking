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
                logging.info(
                    f"[wrapper] 🧩 Bypass registrar_memoria para {url}")
                return func(req)

            # === 1️⃣ Consultar contexto previo GLOBAL antes de ejecutar ===
            try:
                from cosmos_memory_direct import consultar_memoria_cosmos_directo
                memoria_global = consultar_memoria_cosmos_directo(req)
                setattr(req, "memoria_global", memoria_global)

                if memoria_global and memoria_global.get("tiene_historial"):
                    logging.info(
                        f"[wrapper] 🌍 Memoria global: {memoria_global['total_interacciones']} interacciones para {memoria_global.get('agent_id')}")
                else:
                    logging.info("[wrapper] 📝 Sin memoria global previa")
            except Exception as e:
                logging.warning(
                    f"[wrapper] ⚠️ No se pudo consultar memoria global: {e}")
                setattr(req, "memoria_global", None)

            # === 🔍 BÚSQUEDA SEMÁNTICA AUTOMÁTICA (sin depender del body) ===
            try:
                # Extraer session_id y agent_id de headers/params (Foundry envía body vacío)
                session_id = (
                    req.headers.get("Session-ID") or
                    req.headers.get("X-Session-ID") or
                    req.params.get("Session-ID") or
                    req.params.get("session_id")
                )

                agent_id = (
                    req.headers.get("Agent-ID") or
                    req.headers.get("X-Agent-ID") or
                    req.params.get("Agent-ID") or
                    req.params.get("agent_id") or
                    "GlobalAgent"
                )

                # Detectar endpoint desde URL
                endpoint_detectado = url.split(
                    '/')[-1] if '/' in url else source

                # 🔥 BÚSQUEDA SEMÁNTICA: Basada en endpoint + session_id (sin body)
                if session_id and agent_id:
                    from azure.cosmos import CosmosClient
                    import os

                    cosmos_endpoint = os.environ.get("COSMOSDB_ENDPOINT")
                    cosmos_key = os.environ.get("COSMOSDB_KEY")

                    if cosmos_endpoint and cosmos_key:
                        client = CosmosClient(cosmos_endpoint, cosmos_key)
                        database = client.get_database_client(
                            os.environ.get("COSMOSDB_DATABASE", "agentMemory"))
                        container = database.get_container_client("memory")

                        # Query semántica: buscar por endpoint + agent_id (sin depender del body)
                        query = """
                        SELECT TOP 10 c.texto_semantico, c.endpoint, c.timestamp, c.data.respuesta_resumen
                        FROM c
                        WHERE c.agent_id = @agent_id
                          AND (c.endpoint = @endpoint OR CONTAINS(c.endpoint, @endpoint))
                          AND IS_DEFINED(c.texto_semantico)
                          AND LENGTH(c.texto_semantico) > 30
                        ORDER BY c._ts DESC
                        """

                        items = list(container.query_items(
                            query=query,
                            parameters=[
                                {"name": "@agent_id", "value": agent_id},
                                {"name": "@endpoint", "value": endpoint_detectado}
                            ],
                            enable_cross_partition_query=True
                        ))

                        if items:
                            # Construir contexto semántico enriquecido
                            contexto_semantico = {
                                "interacciones_similares": len(items),
                                "endpoint": endpoint_detectado,
                                "resumen": " | ".join([item.get("texto_semantico", "")[:100] for item in items[:3]]),
                                "ultima_ejecucion": items[0].get("timestamp") if items else None
                            }
                            setattr(req, "contexto_semantico",
                                    contexto_semantico)
                            logging.info(
                                f"[wrapper] 🔍 Búsqueda semántica: {len(items)} interacciones similares en '{endpoint_detectado}' para {agent_id}")
                        else:
                            logging.info(
                                f"[wrapper] 🔍 Sin memoria semántica previa para '{endpoint_detectado}'")
                            setattr(req, "contexto_semantico", None)
                    else:
                        logging.warning(
                            "[wrapper] ⚠️ Cosmos DB no configurado para búsqueda semántica")
                        setattr(req, "contexto_semantico", None)
                else:
                    logging.info(
                        "[wrapper] ⏭️ Sin session_id/agent_id válidos, búsqueda semántica omitida")
                    setattr(req, "contexto_semantico", None)

            except Exception as e:
                logging.warning(
                    f"[wrapper] ⚠️ Error en búsqueda semántica automática: {e}")
                setattr(req, "contexto_semantico", None)

            # === 2️⃣ Ejecutar función original (con contexto disponible en req.contexto_prev) ===
            response = func(req)

            # === 🔥 ENRIQUECER RESPUESTA (sin romper formato de Foundry) ===
            try:
                if response and response.get_body():
                    response_data = json.loads(response.get_body().decode())
                    
                    # Solo loguear, NO modificar la respuesta
                    tiene_respuesta_usuario = "respuesta_usuario" in response_data
                    tiene_mensaje = "mensaje" in response_data
                    
                    logging.info(f"[wrapper] 📊 Respuesta: respuesta_usuario={tiene_respuesta_usuario}, mensaje={tiene_mensaje}, status={response.status_code}")
                    
                    if not tiene_respuesta_usuario and not tiene_mensaje:
                        logging.warning(f"[wrapper] ⚠️ Respuesta sin campos esperados por Foundry")
            except Exception as e:
                logging.warning(f"[wrapper] ⚠️ Error analizando respuesta: {e}")

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
                    output_data = {
                        "status_code": response.status_code, "raw": True}

                # 🔍 Agregar metadata de búsqueda semántica al output
                contexto_semantico = getattr(req, "contexto_semantico", None)
                if contexto_semantico:
                    if "metadata" not in output_data:
                        output_data["metadata"] = {}
                    output_data["metadata"]["busqueda_semantica"] = {
                        "aplicada": True,
                        "interacciones_encontradas": contexto_semantico.get("interacciones_similares", 0),
                        "endpoint_buscado": contexto_semantico.get("endpoint"),
                        "resumen_contexto": contexto_semantico.get("resumen", "")[:200]
                    }
                else:
                    if "metadata" not in output_data:
                        output_data["metadata"] = {}
                    output_data["metadata"]["busqueda_semantica"] = {
                        "aplicada": False,
                        "razon": "sin_session_id_o_sin_resultados"
                    }

                # 🌍 Extraer agent_id para memoria global
                agent_id = (
                    req.headers.get("Agent-ID") or
                    req.headers.get("X-Agent-ID") or
                    input_data.get("agent_id") or
                    input_data.get("agent_name") or
                    "GlobalAgent"
                )

                # 🧠 Generar texto semántico enriquecido para memoria global
                texto_sem = output_data.get("texto_semantico", "")
                if not str(texto_sem).strip():
                    endpoint_name = url.split(
                        '/')[-1] if '/' in url else source
                    output_data["texto_semantico"] = (
                        f"[{agent_id}] Ejecutó '{endpoint_name}' con éxito: {'✅' if response.status_code == 200 else '❌'}. "
                        f"Respuesta: {str(output_data.get('mensaje', output_data.get('resultado', 'procesado')))[:100]}..."
                    )

                # 🔍 Enriquecer output con contexto semántico si existe
                contexto_semantico = getattr(req, "contexto_semantico", None)
                if contexto_semantico:
                    output_data["contexto_semantico_aplicado"] = contexto_semantico
                    output_data["memoria_semantica_activa"] = True
                    logging.info(
                        f"[wrapper] 🧠 Contexto semántico aplicado: {contexto_semantico['interacciones_similares']} interacciones")

                # Guardar en memoria semántica
                memory_service.record_interaction(
                    agent_id=agent_id,
                    source=source,
                    input_data=input_data,
                    output_data=output_data
                )
                logging.info(
                    f"[wrapper] 💾 Interacción registrada en memoria global para agente {agent_id}")
            except Exception as e:
                logging.warning(
                    f"[wrapper] ⚠️ Fallo al registrar en memoria global {source}: {e}")

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
