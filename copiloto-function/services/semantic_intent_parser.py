# -*- coding: utf-8 -*-
"""
Semantic Intent Parser - Detecta intención del usuario y redirige al endpoint correcto
Intercepta consultas antes de que lleguen al endpoint incorrecto
"""

import re
import json
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime

def detectar_intencion(input_texto: str, endpoint_actual: str = "", contexto: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Detecta intención dinámicamente sin predefiniciones
    """
    
    if not input_texto or not isinstance(input_texto, str):
        return {"redirigir": False, "razon": "Input vacío"}
    
    texto = input_texto.lower().strip()
    
    # 🚫 GUARD CLAUSE: Prevenir redirección infinita
    if "revisar-correcciones" in endpoint_actual:
        # Si el input es genérico o de test, no redirigir
        if texto in ["revisar correcciones", "test", "ping", ""]:
            return {"redirigir": False, "razon": "Input genérico - evitando loop"}
    
    # Análisis semántico dinámico
    palabras_memoria = ["historial", "interacciones", "conversacion", "memoria", "chat", "ultimas", "hablamos", "dijiste", "sesion"]
    palabras_correcciones = ["correcciones", "fixes", "cambios", "errores", "codigo", "archivo", "sistema"]
    
    score_memoria = sum(1 for p in palabras_memoria if p in texto)
    score_correcciones = sum(1 for p in palabras_correcciones if p in texto)
    
    # Detección inteligente por contexto
    if "revisar-correcciones" in endpoint_actual and score_memoria > 0:
        return {
            "redirigir": True,
            "endpoint_destino": "/api/historial-interacciones",
            "razon": "Endpoint incorrecto detectado",
            "confianza": 0.9
        }
    
    if score_memoria > score_correcciones and score_memoria > 0:
        return {
            "redirigir": True,
            "endpoint_destino": "/api/historial-interacciones",
            "razon": "Consulta de memoria detectada",
            "confianza": 0.8
        }
    
    if score_correcciones > 0 and "revisar-correcciones" not in endpoint_actual:
        return {
            "redirigir": True,
            "endpoint_destino": "/api/revisar-correcciones",
            "razon": "Consulta de correcciones detectada",
            "confianza": 0.8
        }
    
    return {"redirigir": False, "razon": "Sin redirección necesaria"}





def invocar_endpoint_interno(endpoint_destino: str, payload_original: Dict, req_original: Any) -> Any:
    """
    Invoca internamente otro endpoint con el payload original
    
    Args:
        endpoint_destino: Endpoint al que redirigir
        payload_original: Payload original de la request
        req_original: Request original
    
    Returns:
        Respuesta del endpoint destino
    """
    
    try:
        # Mapeo de endpoints a funciones
        endpoint_map = {
            "/api/historial-interacciones": "historial_interacciones",
            "/api/revisar-correcciones": "revisar_correcciones_http", 
            "/api/status": "status",
            "/api/ejecutar": "ejecutar",
            "/api/copiloto": "copiloto",
            "/api/hybrid": "hybrid"
        }
        
        function_name = endpoint_map.get(endpoint_destino)
        if not function_name:
            logging.error(f"❌ Endpoint no mapeado: {endpoint_destino}")
            return crear_respuesta_error(f"Endpoint {endpoint_destino} no disponible")
        
        # Buscar función ejecutable real
        import function_app
        
        # Obtener la función real del FunctionBuilder
        function_builder = getattr(function_app, function_name, None)
        if function_builder and hasattr(function_builder, 'get_user_function'):
            target_function = function_builder.get_user_function()
        else:
            target_function = function_builder
        
        if not target_function or not callable(target_function):
            logging.error(f"❌ Función ejecutable no encontrada: {function_name}")
            return crear_respuesta_error(f"Función {function_name} no disponible")
        
        # Crear nueva request con payload modificado
        import azure.functions as func
        
        # Construir nuevo body si es necesario
        if payload_original:
            new_body = json.dumps(payload_original).encode('utf-8')
        else:
            new_body = b""
        
        # Crear request mock con los datos originales y headers preservados
        try:
            # Preservar headers críticos de sesión
            preserved_headers = dict(req_original.headers)
            preserved_params = dict(req_original.params)
            
            # Asegurar que Session-ID y Agent-ID se propaguen
            if "Session-ID" in req_original.headers and "Session-ID" not in preserved_params:
                preserved_params["Session-ID"] = req_original.headers["Session-ID"]
            if "Agent-ID" in req_original.headers and "Agent-ID" not in preserved_params:
                preserved_params["Agent-ID"] = req_original.headers["Agent-ID"]
            
            new_req = func.HttpRequest(
                method=req_original.method,
                url=endpoint_destino,
                headers={
                    **preserved_headers,
                    "Session-ID": req_original.headers.get("Session-ID", ""),
                    "Agent-ID": req_original.headers.get("Agent-ID", "")
                },
                params={
                    **preserved_params,
                    "Session-ID": req_original.headers.get("Session-ID", ""),
                    "Agent-ID": req_original.headers.get("Agent-ID", "")
                },
                body=new_body
            )
        except Exception as e:
            logging.error(f"Error creando HttpRequest: {e}")
            # Usar request original si falla
            new_req = req_original
        
        # Copiar atributos de memoria si existen
        if hasattr(req_original, '__dict__'):
            for key, value in req_original.__dict__.items():
                if key.startswith('_memoria') or key.startswith('_session') or key.startswith('_agent'):
                    setattr(new_req, key, value)
        
        logging.info(f"🔄 Redirigiendo internamente: {req_original.url} -> {endpoint_destino}")
        
        # Ejecutar función destino
        response = target_function(new_req)
        
        # Agregar metadata de redirección
        if hasattr(response, 'get_body'):
            try:
                body_bytes = response.get_body()
                if body_bytes:
                    response_data = json.loads(body_bytes.decode('utf-8'))
                    if isinstance(response_data, dict):
                        response_data["_redireccion"] = {
                            "desde": req_original.url,
                            "hacia": endpoint_destino,
                            "razon": "Detección automática de intención",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Crear nueva respuesta con metadata y headers de debug
                        headers = {
                            "X-Redirigido-Desde": req_original.url,
                            "X-Redireccion-Timestamp": datetime.now().isoformat(),
                            "X-Intencion-Detectada": "redireccion_automatica"
                        }
                        return func.HttpResponse(
                            json.dumps(response_data, ensure_ascii=False),
                            status_code=response.status_code,
                            mimetype="application/json",
                            headers=headers
                        )
            except:
                pass  # Si no se puede parsear, devolver respuesta original
        
        return response
        
    except Exception as e:
        logging.error(f"❌ Error en redirección interna: {e}")
        return crear_respuesta_error(f"Error en redirección: {str(e)}")


def crear_respuesta_error(mensaje: str) -> Any:
    """Crea una respuesta de error estándar"""
    try:
        import azure.functions as func
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": mensaje,
                "timestamp": datetime.now().isoformat(),
                "tipo": "error_redireccion"
            }, ensure_ascii=False),
            status_code=500,
            mimetype="application/json"
        )
    except:
        return {
            "exito": False,
            "error": mensaje,
            "timestamp": datetime.now().isoformat(),
            "tipo": "error_redireccion"
        }


def extraer_input_usuario(req: Any) -> str:
    """
    Extrae el input del usuario de diferentes fuentes de la request
    
    Args:
        req: Request object
    
    Returns:
        String con el input del usuario
    """
    
    inputs = []
    
    try:
        # 1. Parámetros de query
        if hasattr(req, 'params') and req.params:
            for key, value in req.params.items():
                if key.lower() in ['query', 'consulta', 'mensaje', 'q', 'search']:
                    inputs.append(str(value))
        
        # 2. Body JSON
        if hasattr(req, 'get_json'):
            try:
                body = req.get_json()
                if body and isinstance(body, dict):
                    for key in ['query', 'consulta', 'mensaje', 'prompt', 'text', 'input']:
                        if key in body and body[key]:
                            inputs.append(str(body[key]))
                    
                    # Si no hay campos específicos, usar todo el body como string
                    if not inputs and body:
                        inputs.append(json.dumps(body, ensure_ascii=False))
            except:
                pass
        
        # 3. Headers específicos
        if hasattr(req, 'headers') and req.headers:
            for header in ['X-Query', 'X-Message', 'User-Query']:
                if header in req.headers:
                    inputs.append(str(req.headers[header]))
        
        # 4. URL path como último recurso
        if hasattr(req, 'url') and not inputs:
            inputs.append(req.url)
    
    except Exception as e:
        logging.warning(f"⚠️ Error extrayendo input usuario: {e}")
    
    # Combinar todos los inputs encontrados
    combined_input = " ".join(inputs).strip()
    return combined_input[:500]  # Limitar longitud


def aplicar_deteccion_intencion(req: Any, endpoint_actual: str) -> Tuple[bool, Any]:
    """
    Aplica detección de intención y redirige si es necesario
    
    Args:
        req: Request object
        endpoint_actual: Endpoint actual
    
    Returns:
        Tuple (fue_redirigido: bool, respuesta: Any)
    """
    
    try:
        # Extraer input del usuario
        input_usuario = extraer_input_usuario(req)
        
        if not input_usuario:
            return False, None
        
        # Detectar intención
        deteccion = detectar_intencion(input_usuario, endpoint_actual)
        
        logging.info(f"🧠 Detección intención: {deteccion.get('intencion', 'unknown')} - Redirigir: {deteccion.get('redirigir', False)}")
        
        # Si no necesita redirección, continuar normal
        if not deteccion.get("redirigir", False):
            return False, None
        
        # Preparar payload para redirección
        payload_redireccion = deteccion.get("payload_sugerido", {})
        
        # Agregar input original al payload
        payload_redireccion["input_original"] = input_usuario
        payload_redireccion["deteccion_automatica"] = True
        
        # Ejecutar redirección
        endpoint_destino = deteccion["endpoint_destino"]
        respuesta = invocar_endpoint_interno(endpoint_destino, payload_redireccion, req)
        
        logging.info(f"✅ Redirección exitosa: {endpoint_actual} -> {endpoint_destino}")
        
        return True, respuesta
        
    except Exception as e:
        logging.error(f"❌ Error en detección de intención: {e}")
        return False, None


# Función de utilidad para testing
def test_deteccion_intencion():
    """Función para probar la detección de intención"""
    
    test_cases = [
        "cuáles fueron las últimas 5 interacciones",
        "muéstrame el historial de conversación",
        "qué correcciones se han aplicado",
        "ejecutar comando ls",
        "leer archivo README.md",
        "estado del sistema"
    ]
    
    print("🧪 Testing detección de intención:")
    for caso in test_cases:
        resultado = detectar_intencion(caso)
        print(f"  '{caso}' -> {resultado.get('intencion')} ({'redirigir' if resultado.get('redirigir') else 'continuar'})")


if __name__ == "__main__":
    test_deteccion_intencion()