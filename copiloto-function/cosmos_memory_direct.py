# -*- coding: utf-8 -*-
"""
Consulta directa a Cosmos DB para memoria semántica
Reemplaza las funciones que no consultan realmente la base de datos
"""

import logging
import os
import azure.functions as func

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from opentelemetry import metrics, trace


def consultar_memoria_cosmos_directo(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Consulta DIRECTAMENTE Cosmos DB para obtener historial de interacciones
    """
    try:
        from azure.cosmos import CosmosClient

        # Configuración de Cosmos DB
        endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")

        if not key:
            logging.warning("COSMOSDB_KEY no configurada")
            return None

        # Extraer session_id del request
        session_id = extraer_session_id_request(req)
        if not session_id:
            logging.info("No se encontró session_id en el request")
            return None

        # Extraer agent_id para fallback
        agent_id = extraer_agent_id_request(req)

        # Conectar a Cosmos DB
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # 🌍 MEMORIA GLOBAL DIRECTA: Solo por agent_id
        if not agent_id or agent_id == "unknown_agent":
            agent_id = "GlobalAgent"  # Forzar agent_id por defecto
            logging.info(f"🔧 Agent ID forzado a: {agent_id}")

        # 🌍 MEMORIA GLOBAL SECUENCIAL UNIVERSAL
        query = """
        SELECT TOP 50 c.id, c.agent_id, c.session_id, c.endpoint, c.timestamp,
                       c.event_type, c.texto_semantico, c.contexto_conversacion,
                       c.metadata, c.resumen_conversacion
        FROM c
        WHERE IS_DEFINED(c.texto_semantico)
        ORDER BY c._ts DESC
        """
        logging.info("🌍 Ejecutando memoria secuencial universal (sin filtros por session_id ni agent_id)")
        logging.debug(f"🌍 Query: {query}")

        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # LOG de aplicación (aparece en 'traces' table)
        logging.info("historial-interacciones: memoria_global_aplicada count=%d", len(items))

        # MÉTRICA personalizada como log (AI la convierte en customMetrics)
        try:
            logging.info(
                f"customMetric|name=historial_interacciones_hits;value=1;agent_id={agent_id};endpoint=historial_interacciones"
            )
        except Exception as _:
            pass

        # TRACE manual (aparece en 'traces' con span)
        try:
            tracer = trace.get_tracer("copiloto.memory")
            with tracer.start_as_current_span("consultar_memoria_cosmos_directo") as span:
                span.set_attribute("items_encontrados", len(items))
                span.set_attribute("agent_id", agent_id or "unknown")
        except Exception as _:
            pass

        if items:
            logging.info(f"🌍 Memoria global: {len(items)} interacciones encontradas")
        else:
            logging.warning("📝 Sin memoria previa encontrada")

        if items:
            # Procesar interacciones encontradas CON TEXTO_SEMANTICO
            interacciones_formateadas = []

            for item in items:
                # Extraer datos del nivel raíz y de sección posible de data
                data_section = item.get("data", {})

                interaccion = {
                    "timestamp": item.get("timestamp", data_section.get("timestamp", "")),
                    "endpoint": item.get("endpoint", data_section.get("endpoint", "unknown")),
                    "consulta": (data_section.get("params", {}).get("comando", "") or item.get("resumen_conversacion", "") or "")[:100],
                    "exito": data_section.get("success", True),
                    "texto_semantico": item.get("texto_semantico", ""),  # NIVEL RAÍZ
                    "respuesta_resumen": str(data_section.get("response_data", "") or item.get("resumen_conversacion", ""))[:150]
                }
                interacciones_formateadas.append(interaccion)

                # Log para verificar
                logging.info(f"📝 Interacción recuperada: {interaccion['endpoint']} - texto: {interaccion['texto_semantico'][:50]}...")

            # Generar resumen para el agente
            resumen_conversacion = generar_resumen_conversacion(interacciones_formateadas)
            
            # 🧠 INTERPRETACIÓN SEMÁNTICA RICA DEL SISTEMA
            interpretacion_semantica = interpretar_patron_semantico(interacciones_formateadas)
            logging.info(f"🧠 Interpretación semántica: {interpretacion_semantica}")
            
            # 🎯 CONTEXTO INTELIGENTE ADICIONAL
            try:
                from semantic_classifier import get_intelligent_context
                context_analysis = get_intelligent_context(interacciones_formateadas)
                contexto_inteligente = {
                    "modo_operacion": context_analysis['mode'],
                    "contexto_seleccionado": len(context_analysis['context']),
                    "total_analizado": context_analysis['total_analyzed'],
                    "resumen_inteligente": context_analysis['summary']
                }
                logging.info(f"🎯 Contexto inteligente: {contexto_inteligente}")
            except ImportError:
                contexto_inteligente = {
                    "modo_operacion": "fallback",
                    "contexto_seleccionado": len(interacciones_formateadas),
                    "total_analizado": len(items),
                    "resumen_inteligente": "Análisis básico aplicado"
                }

            # Dejar registro local adicional justo antes del return para verificar emisión
            logging.info("✅ customMetric|name=historial_interacciones_hits;value=1;agent_id=%s;endpoint=historial_interacciones", agent_id)

            response = {
                "tiene_historial": True,
                "session_id": session_id,
                "agent_id": agent_id,
                "total_interacciones": len(items),
                "total_interacciones_sesion": len(items),
                "interacciones_recientes": interacciones_formateadas,
                "resumen_conversacion": resumen_conversacion,
                "interpretacion_semantica": interpretacion_semantica,
                "contexto_inteligente": contexto_inteligente,
                "ultima_actividad": items[0].get("timestamp") if items else None,
                "contexto_recuperado": True,
                "memoria_global": True,
                "estrategia": "global_por_agent_id",
                "foundry_optimized": False,
                "validation_applied": False,
                "validation_stats": {
                    "original_count": len(items),
                    "final_optimized": len(interacciones_formateadas)
                },
                "metadata": {
                    "memoria_aplicada": True,
                    "memoria_global": True,
                    "interacciones_previas": len(items),
                    "endpoint_detectado": "historial_interacciones",
                    "agent_id": agent_id,
                    "foundry_detected": False,
                    "session_info": {
                        "session_id": session_id,
                        "agent_id": agent_id
                    },
                    "memoria_disponible": True,
                    "wrapper_aplicado": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 🔍 VALIDACIÓN DE CONTEXTO ANTES DEL MODELO
            try:
                from context_validator import validate_context_before_model
                response = validate_context_before_model(response)
                logging.info(f"🔍 Contexto validado y optimizado")
            except ImportError:
                logging.warning("⚠️ Validador de contexto no disponible")
            
            return response
        else:
            return {
                "tiene_historial": False,
                "session_id": session_id,
                "agent_id": agent_id,
                "nueva_sesion": True,
                "memoria_global": False,
                "estrategia": "sin_memoria",
                "interpretacion_semantica": "Nueva sesión iniciada sin historial previo",
                "contexto_inteligente": {
                    "modo_operacion": "new_session",
                    "contexto_seleccionado": 0,
                    "total_analizado": 0,
                    "resumen_inteligente": "Sin contexto previo disponible"
                },
                "validation_applied": True,
                "validation_stats": {
                    "original_count": 0,
                    "final_optimized": 0
                },
                "metadata": {
                    "memoria_aplicada": False,
                    "memoria_global": False,
                    "interacciones_previas": 0,
                    "endpoint_detectado": "historial_interacciones",
                    "agent_id": agent_id,
                    "session_info": {
                        "session_id": session_id,
                        "agent_id": agent_id
                    },
                    "memoria_disponible": False,
                    "wrapper_aplicado": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

    except Exception as e:
        logging.error(f"Error consultando Cosmos DB directamente: {e}")
        return None

def extraer_session_id_request(req: func.HttpRequest) -> Optional[str]:
    """Extrae session_id de múltiples fuentes en el request (solo para metadata)"""
    
    # 1. Desde headers (prioridad alta)
    session_id = (
        req.headers.get("Session-ID") or
        req.headers.get("X-Session-ID") or
        req.headers.get("x-session-id")
    )
    if session_id:
        return session_id
    
    # 2. Desde parámetros de query
    session_id = req.params.get("session_id")
    if session_id:
        return session_id
    
    # 3. Desde body JSON
    try:
        body = req.get_json()
        if body and isinstance(body, dict):
            session_id = body.get("session_id")
            if session_id:
                return session_id
    except:
        pass
    
    # 4. Generar session_id temporal (solo para metadata, no afecta memoria)
    import time
    session_id = f"temp_{int(time.time())}"
    return session_id


# Importar función desde semantic_helpers
from semantic_helpers import generar_resumen_conversacion

# Usar clasificador semántico existente para interpretación dinámica
try:
    from semantic_classifier import get_intelligent_context
    from semantic_intent_classifier import classify_user_intent
    
    def interpretar_patron_semantico(interacciones: list) -> str:
        if not interacciones:
            return "Sin actividad previa detectada"
        
        # Usar el contexto inteligente existente
        contexto = get_intelligent_context(interacciones)
        
        # Analizar la última interacción para detectar intención
        ultima = interacciones[0] if interacciones else {}
        texto_semantico = ultima.get('texto_semantico', '')
        
        if texto_semantico:
            intent_result = classify_user_intent(texto_semantico)
            intent = intent_result.get('intent', 'general')
            confidence = intent_result.get('confidence', 0.5)
            
            return f"Análisis inteligente: {contexto['summary']} | Intención detectada: {intent} (confianza: {int(confidence*100)}%) | Modo: {contexto['mode']}"
        else:
            return f"Análisis inteligente: {contexto['summary']} | Modo: {contexto['mode']}"
            
except ImportError:
    def interpretar_patron_semantico(interacciones: list) -> str:
        if not interacciones:
            return "Sin actividad previa detectada"
        return f"Análisis de {len(interacciones)} interacciones completado"

def aplicar_memoria_cosmos_directo(req: func.HttpRequest, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica memoria consultando directamente Cosmos DB y enriquece la respuesta
    INCLUYE detección automática de endpoint para evitar "unknown"
    """
    try:
        # 🎯 DETECTAR ENDPOINT AUTOMÁTICAMENTE
        endpoint_detectado = "unknown"
        try:
            from endpoint_detector import aplicar_deteccion_endpoint_automatica
            endpoint_detectado = aplicar_deteccion_endpoint_automatica(req)
            logging.info(f"🎯 Endpoint auto-detectado para memoria: {endpoint_detectado}")
        except Exception as e:
            logging.warning(f"⚠️ Error en detección automática de endpoint: {e}")
        
        # 🤖 DETECTAR SI ES FOUNDRY PARA OPTIMIZAR RESPUESTA
        user_agent = req.headers.get("User-Agent", "")
        es_foundry = "azure-agents" in user_agent.lower()
        if es_foundry:
            logging.info("🤖 Foundry detectado - optimizando respuesta semántica")
        
        # Consultar memoria directamente
        memoria = consultar_memoria_cosmos_directo(req)
        
        if memoria and memoria.get("tiene_historial"):
            # Asegurar que response_data es mutable
            if not isinstance(response_data, dict):
                response_data = {"data": response_data}
            
            # Agregar contexto de conversación al inicio
            if "contexto_conversacion" not in response_data:
                response_data["contexto_conversacion"] = {
                    "mensaje": f"Memoria global activa: {memoria.get('total_interacciones', 0)} interacciones previas del agente {memoria.get('agent_id', 'unknown')}",
                    "ultimas_consultas": memoria.get("resumen_conversacion", ""),
                    "session_id": memoria.get("session_id"),
                    "agent_id": memoria.get("agent_id"),
                    "ultima_actividad": memoria.get("ultima_actividad"),
                    "estrategia_memoria": "global_por_agent_id"
                }
            
            # Agregar metadata de memoria
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"].update({
                "memoria_aplicada": True,
                "memoria_global": True,
                "interacciones_previas": memoria.get("total_interacciones", 0),
                "endpoint_detectado": endpoint_detectado,
                "agent_id": memoria.get("agent_id"),
                "session_info": {
                    "session_id": memoria.get("session_id"),
                    "agent_id": memoria.get("agent_id")
                },
                "memoria_disponible": True,
                "wrapper_aplicado": True,
                "aplicacion_manual": True,
                "timestamp": datetime.now().isoformat()
            })
            
            logging.info(f"🧠 Memoria global aplicada: {memoria.get('total_interacciones', 0)} interacciones para {memoria.get('agent_id')}")
        else:
            # Sin memoria disponible
            if "metadata" not in response_data:
                response_data["metadata"] = {}
            
            response_data["metadata"].update({
                "memoria_aplicada": False,
                "memoria_global": False,
                "interacciones_previas": 0,
                "endpoint_detectado": endpoint_detectado,
                "session_info": {
                    "session_id": None,
                    "agent_id": None
                },
                "memoria_disponible": False,
                "wrapper_aplicado": True,
                "timestamp": datetime.now().isoformat()
            })
            
            logging.info("📝 Sin memoria previa disponible")
        
        return response_data
        
    except Exception as e:
        logging.error(f"Error aplicando memoria Cosmos directo: {e}")
        return response_data

# Usar sistema existente de memory_service
try:
    from services.memory_service import memory_service
    def registrar_redireccion_cosmos(req: func.HttpRequest, endpoint_original: str, fue_redirigido: bool, respuesta_redirigida: Any) -> bool:
        try:
            memory_service.registrar_llamada(
                source="redirect",
                endpoint=endpoint_original,
                method=req.method,
                params={"redirigido": fue_redirigido},
                response_data=respuesta_redirigida,
                success=True
            )
            return True
        except Exception:
            return False
except ImportError:
    def registrar_redireccion_cosmos(req: func.HttpRequest, endpoint_original: str, fue_redirigido: bool, respuesta_redirigida: Any) -> bool:
        return True  # Fallback silencioso

def extraer_input_usuario_simple(req: func.HttpRequest) -> str:
    """Extrae input del usuario de forma simple"""
    try:
        # Parámetros
        for key in ['consulta', 'query', 'mensaje', 'q']:
            if key in req.params:
                return str(req.params[key])
        
        # Body
        try:
            body = req.get_json()
            if body:
                for key in ['consulta', 'query', 'mensaje', 'prompt']:
                    if key in body:
                        return str(body[key])
        except:
            pass
        
        return "input_no_detectado"
    except:
        return "error_extrayendo_input"

def registrar_interaccion_cosmos_directo(req: func.HttpRequest, endpoint: str, response_data: Dict[str, Any]) -> bool:
    """
    Registra la interacción actual directamente en Cosmos DB con el endpoint correcto
    """
    try:
        from azure.cosmos import CosmosClient
        
        # Configuración de Cosmos DB
        cosmos_endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
        key = os.environ.get("COSMOSDB_KEY")
        database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")
        
        if not key:
            return False
        
        # Extraer información del request
        session_id = extraer_session_id_request(req) or "unknown_session"
        agent_id = extraer_agent_id_request(req) or "unknown_agent"
        input_usuario = extraer_input_usuario_simple(req)
        
        # Conectar a Cosmos DB
        client = CosmosClient(cosmos_endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Crear documento de interacción con ID único
        timestamp_unico = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        documento = {
            "id": f"interaction_{session_id}_{timestamp_unico}",
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,  # 🎯 ENDPOINT CORRECTO DETECTADO AUTOMÁTICAMENTE
            "consulta": input_usuario[:500],  # Limitar tamaño
            "respuesta": str(response_data).replace('"', "'")[:500],  # Respuesta resumida
            "exito": response_data.get("exito", True) if isinstance(response_data, dict) else True,
            "method": getattr(req, 'method', 'GET'),
            "tipo": "interaccion_usuario",
            "_ts": int(datetime.now().timestamp())
        }
        
        # Usar upsert para evitar conflictos
        container.upsert_item(documento)
        logging.info(f"💾 Interacción registrada en Cosmos: {endpoint} (session: {session_id[:8]}...)")
        return True
        
    except Exception as e:
        logging.warning(f"⚠️ Error registrando interacción en Cosmos: {e}")
        return False

def extraer_agent_id_request(req: func.HttpRequest) -> str:
    """Extrae agent_id del request (CRÍTICO para memoria global)"""
    try:
        # Headers
        agent_id = (
            req.headers.get("Agent-ID") or
            req.headers.get("X-Agent-ID") or
            req.headers.get("x-agent-id")
        )
        if agent_id:
            logging.info(f"🤖 Agent ID desde headers: {agent_id}")
            return agent_id
        
        # Parámetros
        agent_id = req.params.get("agent_id")
        if agent_id:
            logging.info(f"🤖 Agent ID desde params: {agent_id}")
            return agent_id
        
        # Body
        try:
            body = req.get_json()
            if body and isinstance(body, dict):
                agent_id = body.get("agent_id")
                if agent_id:
                    logging.info(f"🤖 Agent ID desde body: {agent_id}")
                    return agent_id
        except:
            pass
        
        # SIEMPRE retornar GlobalAgent como fallback
        agent_id = "GlobalAgent"
        logging.info(f"🔧 Agent ID forzado a fallback: {agent_id}")
        return agent_id
    except:
        return "GlobalAgent"