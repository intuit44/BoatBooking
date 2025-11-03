# -*- coding: utf-8 -*-
"""
Memory Decorator - Sistema de memoria automático para Azure Functions
Registra automáticamente las llamadas a endpoints en el sistema de memoria.
"""

import logging
import json
from datetime import datetime
from typing import Callable, Any, Dict, Optional
from functools import wraps

try:
    import azure.functions as func
except ImportError:
    # Mock para testing
    class MockFunc:
        class HttpRequest:
            def __init__(self):
                self.method = "GET"
                self.url = "http://test"
                self.params = {}
            def get_json(self):
                return {}
        
        class HttpResponse:
            def __init__(self, body, status_code=200, mimetype="text/plain"):
                self.body = body
                self.status_code = status_code
                self.mimetype = mimetype
            def get_body(self):
                return self.body.encode() if isinstance(self.body, str) else self.body
    
    func = MockFunc()

# Cache en memoria para evitar múltiples importaciones
_memory_service = None

def get_memory_service():
    """Obtiene el servicio de memoria de forma lazy"""
    global _memory_service
    if _memory_service is None:
        try:
            from services.memory_service import MemoryService
            _memory_service = MemoryService()
            logging.info("✅ MemoryService inicializado correctamente")
        except ImportError as e:
            logging.warning(f"⚠️ No se pudo importar MemoryService: {e}")
            _memory_service = MockMemoryService()
        except Exception as e:
            logging.error(f"❌ Error inicializando MemoryService: {e}")
            _memory_service = MockMemoryService()
    
    return _memory_service


class MockMemoryService:
    """Servicio de memoria mock para cuando no está disponible el real"""
    
    def registrar_llamada(self, source: str, endpoint: str, method: str, 
                         params: Dict, response_data: Any, success: bool) -> bool:
        """Mock que solo hace logging"""
        logging.info(f"🧠 [MOCK] Memoria: {method} {endpoint} -> {success}")
        return True
    
    def obtener_historial(self, source: str, limit: int = 10) -> list:
        """Mock que retorna lista vacía"""
        return []
    
    def obtener_estadisticas(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """Mock que retorna estadísticas vacías"""
        return {
            "total_llamadas": 0,
            "llamadas_exitosas": 0,
            "llamadas_fallidas": 0,
            "fuentes_activas": [],
            "ultimo_registro": None,
            "servicio": "mock"
        }
    
    def limpiar_registros(self, source_name: Optional[str] = None) -> bool:
        """Mock que simula limpiar registros"""
        logging.info("🧠 [MOCK] Memoria limpiada")
        return True


def registrar_memoria(source_name: str):
    """
    Decorador que registra automáticamente las llamadas en el sistema de memoria,
    consulta memoria previa Y SEMÁNTICA para continuidad de sesión Y detecta intención para redirección automática.
    
    FUNCIONALIDADES AUTOMÁTICAS:
    - Consulta memoria cronológica y semántica
    - Inyecta contexto enriquecido en el request
    - Registra snapshots semánticos automáticamente
    - Mantiene coherencia conversacional
    
    Args:
        source_name: Nombre identificador del endpoint/función
        
    Returns:
        Decorador que envuelve la función con registro de memoria semántica completa
    """
    def decorator(func_ref: Callable) -> Callable:
        @wraps(func_ref)
        def wrapper(req) -> Any:  # Usar Any para evitar problemas de tipo
            logging.info(f"🧠 WRAPPER MEMORIA EJECUTÁNDOSE: {source_name} - {req.method} {req.url}")
            start_time = datetime.now()
            memory_service = get_memory_service()
            
            # Extraer información de la request
            method = req.method
            endpoint = req.url
            
            # 🧠 DETECCIÓN DE INTENCIÓN Y REDIRECCIÓN AUTOMÁTICA

            try:
                from services.semantic_intent_parser import aplicar_deteccion_intencion
                
                fue_redirigido, respuesta_redirigida = aplicar_deteccion_intencion(req, endpoint)
                
                if fue_redirigido and respuesta_redirigida:
                    logging.info(f"🔄 Redirección automática aplicada desde {source_name}")
                    
                    # Registrar la redirección en memoria Y Cosmos
                    try:
                        # Extraer session_id y agent_id ANTES de registrar redirección
                        redirect_session_id = (
                            req.headers.get("Session-ID") or
                            req.headers.get("X-Session-ID") or
                            req.params.get("Session-ID") or
                            f"auto_{int(__import__('time').time())}"
                        )
                        
                        redirect_agent_id = (
                            req.headers.get("Agent-ID") or
                            req.headers.get("X-Agent-ID") or
                            req.params.get("Agent-ID") or
                            "unknown_agent"
                        )
                        
                        memory_service.registrar_llamada(
                            source=f"{source_name}_redirected",
                            endpoint=endpoint,
                            method=method,
                            params={
                                "redireccion_automatica": True, 
                                "endpoint_original": endpoint,
                                "session_id": redirect_session_id,
                                "agent_id": redirect_agent_id
                            },
                            response_data={"redirigido": True, "exito": True},
                            success=True
                        )
                        
                        # Loggear en Cosmos cada redirección semántica
                        try:
                            from cosmos_memory_direct import registrar_redireccion_cosmos
                            registrar_redireccion_cosmos(req, endpoint, fue_redirigido, respuesta_redirigida)
                        except Exception as cosmos_err:
                            logging.warning(f"⚠️ Error logging Cosmos redirección: {cosmos_err}")
                            
                    except Exception as e:
                        logging.warning(f"⚠️ Error registrando redirección: {e}")
                    
                    return respuesta_redirigida
                    
            except Exception as e:
                logging.warning(f"⚠️ Error en detección de intención: {e}")
                # Continuar con flujo normal si falla la detección
            
            # Extraer parámetros de forma segura
            try:
                params = dict(req.params) if req.params else {}
                
                # Intentar obtener body si es POST/PUT/PATCH
                if method in ['POST', 'PUT', 'PATCH']:
                    try:
                        body = req.get_json()
                        if body:
                            params.update({"body": body})
                    except:
                        pass  # Ignorar errores de parsing JSON
                        
            except Exception as e:
                logging.warning(f"⚠️ Error extrayendo parámetros: {e}")
                params = {}
            
            # 🧠 CONSULTAR MEMORIA PREVIA Y SEMÁNTICA AUTOMÁTICAMENTE
            memoria_contexto = None
            contexto_semantico = {}
            session_id = None
            agent_id = None
            
            try:
                # DETECCIÓN AUTOMÁTICA de session_id y agent_id - PRIORIZAR HEADERS
                session_id = (
                    getattr(req, "headers", {}).get("Session-ID")
                    or getattr(req, "headers", {}).get("X-Session-ID")
                    or getattr(req, "headers", {}).get("x-session-id")
                    or getattr(req, "params", {}).get("Session-ID")
                    or getattr(req, "params", {}).get("session_id")
                    or (getattr(req, "get_json", lambda: {})() or {}).get("session_id")
                    or f"auto_{int(__import__('time').time())}"
                )

                agent_id = (
                    getattr(req, "headers", {}).get("Agent-ID")
                    or getattr(req, "headers", {}).get("X-Agent-ID")
                    or getattr(req, "headers", {}).get("x-agent-id")
                    or getattr(req, "params", {}).get("Agent-ID")
                    or getattr(req, "params", {}).get("agent_id")
                    or (getattr(req, "get_json", lambda: {})() or {}).get("agent_id")
                    or "unknown_agent"
                )

                if session_id.startswith("auto_"):
                    logging.warning(f"⚠️ Session ID no encontrado en headers ni params, generado fallback: {session_id}")
                else:
                    logging.info(f"✅ Session ID preservado: {session_id}")

                logging.info(f"🔍 IDs detectados - Session: {session_id}, Agent: {agent_id}")

                # CONSULTAR MEMORIA CRONOLÓGICA
                if session_id and agent_id:
                    from services.session_memory import consultar_memoria_sesion, generar_contexto_prompt
                    
                    resultado_memoria = consultar_memoria_sesion(session_id, agent_id)
                    if resultado_memoria.get("exito"):
                        memoria_contexto = resultado_memoria["memoria"]
                        logging.info(f"🧠 Memoria cronológica: {memoria_contexto.get('total_interacciones_sesion', 0)} interacciones")
                    else:
                        logging.info(f"🆕 Nueva sesión detectada: {session_id[:8]}.../{agent_id[:10]}...")
                
                # 🧠 CONSULTAR MEMORIA SEMÁNTICA AUTOMÁTICAMENTE
                try:
                    from services.semantic_memory import obtener_estado_sistema, obtener_contexto_agente
                    from services.cognitive_supervisor import CognitiveSupervisor
                    
                    estado_resultado = obtener_estado_sistema(24)
                    if estado_resultado.get("exito"):
                        contexto_semantico["estado_sistema"] = estado_resultado["estado"]
                    
                    contexto_agente = obtener_contexto_agente(agent_id, 5)
                    if contexto_agente.get("exito"):
                        contexto_semantico["contexto_agente"] = contexto_agente["contexto"]
                    
                    supervisor = CognitiveSupervisor()
                    conocimiento = supervisor.get_latest_knowledge()
                    if conocimiento.get("exito"):
                        contexto_semantico["conocimiento_cognitivo"] = conocimiento["conocimiento"]
                        
                    logging.info(f"🧠 Contexto semántico enriquecido: {len(contexto_semantico)} fuentes")
                    
                except Exception as e:
                    logging.warning(f"⚠️ Error obteniendo contexto semántico: {e}")
                    contexto_semantico = {"error": str(e)}

                
                # INYECTAR CONTEXTO EN REQUEST PARA USO DEL ENDPOINT
                if hasattr(req, '__dict__'):
                    req.__dict__["_memoria_contexto"] = memoria_contexto
                    req.__dict__["_contexto_semantico"] = contexto_semantico
                    req.__dict__["_session_id"] = session_id
                    req.__dict__["_agent_id"] = agent_id
                    if memoria_contexto:
                        from services.session_memory import generar_contexto_prompt
                        req.__dict__["_memoria_prompt"] = generar_contexto_prompt(memoria_contexto)
                    
                    # Marcar que el wrapper semántico está activo
                    req.__dict__["_semantic_wrapper_active"] = True
                
            except Exception as e:
                logging.warning(f"⚠️ Error consultando memoria: {e}")
            
            # Ejecutar función original
            response = None
            success = False
            response_data = None
            
            try:
                response = func_ref(req)
                success = True
                
                # Intentar extraer datos de respuesta
                try:
                    if hasattr(response, 'get_body'):
                        body_bytes = response.get_body()
                        if body_bytes:
                            response_text = body_bytes.decode('utf-8')
                            response_data = json.loads(response_text)
                except:
                    response_data = {"status_code": getattr(response, 'status_code', 200)}
                    
            except Exception as e:
                success = False
                response_data = {"error": str(e), "type": type(e).__name__}
                logging.error(f"❌ Error en función {source_name}: {e}")
                
                # Crear respuesta de error
                try:
                    response = func.HttpResponse(
                        json.dumps({
                            "error": str(e),
                            "source": source_name,
                            "timestamp": datetime.now().isoformat()
                        }),
                        status_code=500,
                        mimetype="application/json"
                    )
                except:
                    # Fallback si func.HttpResponse no está disponible
                    response = {"error": str(e), "source": source_name}
            
            # 🧠 REGISTRAR EN MEMORIA CRONOLÓGICA Y SEMÁNTICA
            try:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # Obtener session_id y agent_id preservados
                final_session_id = session_id or "unknown"
                final_agent_id = agent_id or "unknown_agent"
                
                # Agregar session_id y agent_id al registro
                enhanced_params = params.copy()
                enhanced_params["session_id"] = final_session_id
                enhanced_params["agent_id"] = final_agent_id
                
                # MEMORIA CRONOLÓGICA
                memory_service.registrar_llamada(
                    source=source_name,
                    endpoint=endpoint,
                    method=method,
                    params=enhanced_params,
                    response_data=response_data,
                    success=success
                )
                
                # 🧠 MEMORIA SEMÁNTICA AUTOMÁTICA CON CONTEXTO ENRIQUECIDO
                try:
                    from services.semantic_memory import registrar_snapshot_semantico
                    
                    # 🔥 GENERAR TEXTO SEMÁNTICO RICO
                    texto_semantico = f"Interacción en '{source_name}' ejecutada por {final_agent_id}. "
                    texto_semantico += f"Éxito: {'✅' if success else '❌'}. "
                    texto_semantico += f"Endpoint: {source_name}. "
                    
                    # Agregar contexto previo si está disponible
                    if memoria_contexto and isinstance(memoria_contexto, dict):
                        resumen = memoria_contexto.get('resumen_ultimo') or memoria_contexto.get('ultimo_tema')
                        if resumen:
                            texto_semantico += f"Contexto previo: {str(resumen)[:150]}. "
                    
                    # Agregar estado del sistema si está disponible
                    if contexto_semantico and not contexto_semantico.get("error"):
                        texto_semantico += f"Estado del sistema: {len(contexto_semantico)} fuentes activas. "
                    
                    # Agregar detalles del response
                    if response_data and isinstance(response_data, dict):
                        if "mensaje" in response_data:
                            msg = str(response_data["mensaje"])[:200]
                            texto_semantico += f"Resultado: {msg}. "
                        if "error" in response_data:
                            texto_semantico += f"Error: {str(response_data['error'])[:100]}. "
                    
                    snapshot_data = {
                        "endpoint": source_name,
                        "method": method,
                        "success": success,
                        "duration_ms": duration_ms,
                        "timestamp": datetime.now().isoformat(),
                        "contexto_semantico_disponible": bool(contexto_semantico and not contexto_semantico.get("error")),
                        "texto_semantico": texto_semantico  # ← CLAVE: Texto rico para búsqueda
                    }
                    
                    # Agregar datos específicos del response si están disponibles
                    if response_data and isinstance(response_data, dict):
                        if "intencion" in str(response_data).lower():
                            snapshot_data["tiene_intencion"] = True
                        if "exito" in response_data:
                            snapshot_data["resultado_exito"] = response_data["exito"]
                    
                    registrar_snapshot_semantico(
                        session_id=final_session_id,
                        agent_id=final_agent_id,
                        tipo="context_snapshot",  # ← Tipo específico para snapshots de contexto
                        contenido=snapshot_data,
                        metadata={"endpoint": source_name, "wrapper": "automatico"}
                    )
                    
                    logging.debug(f"🧠 Memoria semántica registrada automáticamente")
                    
                except Exception as e:
                    logging.warning(f"⚠️ Error registrando memoria semántica: {e}")
                
                logging.debug(f"🧠 Memoria registrada: {source_name} ({duration_ms:.1f}ms)")
                
            except Exception as e:
                logging.warning(f"⚠️ Error registrando en memoria: {e}")
            
            return response
        
        return wrapper
    return decorator


def crear_wrapper_memoria(app: Any):
    """
    DEPRECATED: Usar memory_route_wrapper.py en su lugar.
    Esta función se mantiene por compatibilidad.
    """
    logging.warning("⚠️ crear_wrapper_memoria está deprecated. Usar memory_route_wrapper.py")
    
    def wrapper_func(*args, **kwargs):
        def decorator(func):
            return registrar_memoria("deprecated")(func)
        return decorator
    
    return wrapper_func



# Función de utilidad para obtener estadísticas de memoria
def obtener_estadisticas_memoria(source_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas del sistema de memoria.
    
    Args:
        source_name: Filtrar por fuente específica (opcional)
        
    Returns:
        Diccionario con estadísticas
    """
    try:
        memory_service = get_memory_service()
        
        if hasattr(memory_service, 'obtener_estadisticas'):
            return memory_service.obtener_estadisticas(source_name)
        else:
            # Fallback para mock service
            return {
                "total_llamadas": 0,
                "llamadas_exitosas": 0,
                "llamadas_fallidas": 0,
                "fuentes_activas": [],
                "ultimo_registro": None,
                "servicio": "mock"
            }
            
    except Exception as e:
        logging.error(f"❌ Error obteniendo estadísticas de memoria: {e}")
        return {
            "error": str(e),
            "servicio": "error"
        }


# Función para limpiar memoria (útil para testing)
def limpiar_memoria(source_name: Optional[str] = None) -> bool:
    """
    Limpia registros de memoria.
    
    Args:
        source_name: Limpiar solo una fuente específica (opcional)
        
    Returns:
        True si se limpió correctamente
    """
    try:
        memory_service = get_memory_service()
        
        if hasattr(memory_service, 'limpiar_registros'):
            return memory_service.limpiar_registros(source_name)
        else:
            logging.info("🧠 [MOCK] Memoria limpiada")
            return True
            
    except Exception as e:
        logging.error(f"❌ Error limpiando memoria: {e}")
        return False