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


def registrar_memoria(source_name: str):
    """
    Decorador que registra automáticamente las llamadas en el sistema de memoria
    y consulta memoria previa para continuidad de sesión.
    
    Args:
        source_name: Nombre identificador del endpoint/función
        
    Returns:
        Decorador que envuelve la función con registro de memoria
    """
    def decorator(func_ref: Callable) -> Callable:
        @wraps(func_ref)
        def wrapper(req) -> Any:  # Usar Any para evitar problemas de tipo
            start_time = datetime.now()
            memory_service = get_memory_service()
            
            # Extraer información de la request
            method = req.method
            endpoint = req.url
            
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
            
            # 🧠 CONSULTAR MEMORIA PREVIA AUTOMÁTICAMENTE
            memoria_contexto = None
            try:
                # DETECCIÓN AUTOMÁTICA de session_id y agent_id
                session_id = (
                    params.get("session_id") or 
                    params.get("body", {}).get("session_id") or
                    req.headers.get("X-Session-ID") or
                    req.headers.get("Session-ID") or
                    req.headers.get("x-session-id") or
                    # Generar session_id automático basado en User-Agent + IP
                    f"auto_{hash(req.headers.get('User-Agent', '') + req.headers.get('X-Forwarded-For', ''))}"
                )
                
                agent_id = (
                    params.get("agent_id") or 
                    params.get("body", {}).get("agent_id") or
                    req.headers.get("X-Agent-ID") or
                    req.headers.get("Agent-ID") or
                    req.headers.get("x-agent-id") or
                    req.headers.get("User-Agent", "UnknownAgent")[:50]  # Usar User-Agent como fallback
                )
                
                # SIEMPRE consultar memoria si tenemos identificadores
                if session_id and agent_id:
                    from services.session_memory import consultar_memoria_sesion, generar_contexto_prompt
                    
                    resultado_memoria = consultar_memoria_sesion(session_id, agent_id)
                    if resultado_memoria.get("exito"):
                        memoria_contexto = resultado_memoria["memoria"]
                        
                        # Agregar contexto al request para que la función lo use
                        if hasattr(req, '__dict__'):
                            req.__dict__["_memoria_contexto"] = memoria_contexto
                            req.__dict__["_memoria_prompt"] = generar_contexto_prompt(memoria_contexto)
                            req.__dict__["_session_id"] = session_id
                            req.__dict__["_agent_id"] = agent_id
                        
                        logging.info(f"🧠 Memoria auto-consultada: {session_id[:8]}.../{agent_id[:10]}... -> {memoria_contexto.get('total_interacciones_sesion', 0)} interacciones")
                    else:
                        # Primera vez - crear contexto vacío pero válido
                        if hasattr(req, '__dict__'):
                            req.__dict__["_session_id"] = session_id
                            req.__dict__["_agent_id"] = agent_id
                        logging.info(f"🆕 Nueva sesión detectada: {session_id[:8]}.../{agent_id[:10]}...")
                
            except Exception as e:
                logging.warning(f"⚠️ Error consultando memoria previa: {e}")
            
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
            
            # Registrar en memoria
            try:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # Agregar session_id y agent_id al registro
                enhanced_params = params.copy()
                if hasattr(req, '__dict__'):
                    if "_session_id" in req.__dict__:
                        enhanced_params["session_id"] = req.__dict__["_session_id"]
                    if "_agent_id" in req.__dict__:
                        enhanced_params["agent_id"] = req.__dict__["_agent_id"]
                
                memory_service.registrar_llamada(
                    source=source_name,
                    endpoint=endpoint,
                    method=method,
                    params=enhanced_params,
                    response_data=response_data,
                    success=success
                )
                
                logging.debug(f"🧠 Memoria registrada: {source_name} ({duration_ms:.1f}ms)")
                
            except Exception as e:
                logging.warning(f"⚠️ Error registrando en memoria: {e}")
            
            return response
        
        return wrapper
    return decorator


def crear_wrapper_memoria(app: func.FunctionApp):
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