# -*- coding: utf-8 -*-
"""
Detector automático de endpoints para el sistema de memoria
Soluciona el problema de "endpoint": "unknown" detectando automáticamente el endpoint correcto
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

def detectar_endpoint_automatico(req) -> str:
    """
    Detecta automáticamente el endpoint correcto desde la request
    
    Args:
        req: Azure Functions HttpRequest
        
    Returns:
        str: Endpoint detectado (ej: "historial_interacciones", "copiloto", etc.)
    """
    try:
        # 1. Desde la URL del request
        if hasattr(req, 'url') and req.url:
            endpoint_from_url = extraer_endpoint_desde_url(req.url)
            if endpoint_from_url and endpoint_from_url != "unknown":
                logging.info(f"🎯 Endpoint detectado desde URL: {endpoint_from_url}")
                return endpoint_from_url
        
        # 2. Desde route_params si está disponible
        if hasattr(req, 'route_params') and req.route_params:
            route = req.route_params.get("route")
            if route:
                endpoint_normalized = normalizar_endpoint(route)
                logging.info(f"🎯 Endpoint detectado desde route_params: {endpoint_normalized}")
                return endpoint_normalized
        
        # 3. Desde headers personalizados
        if hasattr(req, 'headers'):
            endpoint_header = req.headers.get("X-Endpoint") or req.headers.get("Endpoint")
            if endpoint_header:
                endpoint_normalized = normalizar_endpoint(endpoint_header)
                logging.info(f"🎯 Endpoint detectado desde headers: {endpoint_normalized}")
                return endpoint_normalized
        
        # 4. Desde parámetros de query
        if hasattr(req, 'params') and req.params:
            endpoint_param = req.params.get("endpoint")
            if endpoint_param:
                endpoint_normalized = normalizar_endpoint(endpoint_param)
                logging.info(f"🎯 Endpoint detectado desde params: {endpoint_normalized}")
                return endpoint_normalized
        
        # 5. Fallback: intentar desde el método y contexto
        logging.warning("⚠️ No se pudo detectar endpoint específico, usando fallback")
        return "unknown"
        
    except Exception as e:
        logging.error(f"❌ Error detectando endpoint: {e}")
        return "unknown"

def extraer_endpoint_desde_url(url: str) -> str:
    """
    Extrae el endpoint desde una URL completa
    
    Args:
        url: URL completa (ej: "http://localhost:7071/api/historial-interacciones")
        
    Returns:
        str: Endpoint normalizado
    """
    try:
        # Parsear la URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Remover /api/ del inicio si existe
        if path.startswith("/api/"):
            path = path[5:]  # Remover "/api/"
        elif path.startswith("api/"):
            path = path[4:]   # Remover "api/"
        
        # Limpiar path
        path = path.strip("/")
        
        if not path:
            return "root"
        
        # Normalizar el endpoint
        return normalizar_endpoint(path)
        
    except Exception as e:
        logging.error(f"❌ Error extrayendo endpoint desde URL {url}: {e}")
        return "unknown"

def normalizar_endpoint(endpoint_raw: str) -> str:
    """
    Normaliza un endpoint a formato estándar para el sistema de memoria
    
    Args:
        endpoint_raw: Endpoint en formato crudo
        
    Returns:
        str: Endpoint normalizado
    """
    try:
        if not endpoint_raw:
            return "unknown"
        
        # Limpiar el endpoint
        endpoint = str(endpoint_raw).strip().lower()
        
        # Remover prefijos comunes
        endpoint = re.sub(r'^(api/|/api/|/)', '', endpoint)
        
        # Mapeo de endpoints conocidos
        endpoint_map = {
            "historial-interacciones": "historial_interacciones",
            "historial_interacciones": "historial_interacciones",
            "revisar-correcciones": "revisar_correcciones", 
            "revisar_correcciones": "revisar_correcciones",
            "copiloto": "copiloto",
            "status": "status",
            "health": "health",
            "ejecutar": "ejecutar",
            "ejecutar-cli": "ejecutar_cli",
            "ejecutar_cli": "ejecutar_cli",
            "leer-archivo": "leer_archivo",
            "leer_archivo": "leer_archivo",
            "escribir-archivo": "escribir_archivo",
            "escribir_archivo": "escribir_archivo",
            "listar-blobs": "listar_blobs",
            "listar_blobs": "listar_blobs",
            "hybrid": "hybrid",
            "preparar-script": "preparar_script",
            "preparar_script": "preparar_script"
        }
        
        # Buscar mapeo exacto
        if endpoint in endpoint_map:
            return endpoint_map[endpoint]
        
        # Si no hay mapeo exacto, convertir guiones a guiones bajos
        normalized = endpoint.replace("-", "_")
        
        # Validar que sea un endpoint válido (solo letras, números y guiones bajos)
        if re.match(r'^[a-z0-9_]+$', normalized):
            return normalized
        
        # Si no es válido, devolver "unknown"
        logging.warning(f"⚠️ Endpoint no válido después de normalización: {endpoint_raw} -> {normalized}")
        return "unknown"
        
    except Exception as e:
        logging.error(f"❌ Error normalizando endpoint {endpoint_raw}: {e}")
        return "unknown"

def aplicar_deteccion_endpoint_automatica(req, endpoint_actual: str = "unknown") -> str:
    """
    Aplica detección automática de endpoint y devuelve el correcto
    
    Args:
        req: Azure Functions HttpRequest
        endpoint_actual: Endpoint actual (puede ser "unknown")
        
    Returns:
        str: Endpoint detectado automáticamente
    """
    try:
        # Si ya tenemos un endpoint válido, usarlo
        if endpoint_actual and endpoint_actual != "unknown":
            return endpoint_actual
        
        # Detectar automáticamente
        endpoint_detectado = detectar_endpoint_automatico(req)
        
        if endpoint_detectado != "unknown":
            logging.info(f"✅ Endpoint auto-detectado: {endpoint_detectado}")
            return endpoint_detectado
        
        # Último fallback: intentar desde el método HTTP
        method = getattr(req, 'method', 'GET')
        if method == 'GET':
            return "consulta_get"
        elif method == 'POST':
            return "accion_post"
        else:
            return f"metodo_{method.lower()}"
            
    except Exception as e:
        logging.error(f"❌ Error en detección automática: {e}")
        return "error_deteccion"

# Función de utilidad para testing
def test_deteccion_endpoint():
    """Función de testing para verificar la detección de endpoints"""
    
    test_cases = [
        ("http://localhost:7071/api/historial-interacciones", "historial_interacciones"),
        ("https://copiloto.azurewebsites.net/api/revisar-correcciones", "revisar_correcciones"),
        ("/api/copiloto", "copiloto"),
        ("api/status", "status"),
        ("ejecutar-cli", "ejecutar_cli"),
        ("leer-archivo", "leer_archivo"),
        ("", "unknown"),
        (None, "unknown")
    ]
    
    print("🧪 Testing detección de endpoints:")
    for url, expected in test_cases:
        if url:
            result = extraer_endpoint_desde_url(url)
        else:
            result = normalizar_endpoint(url)
        
        status = "✅" if result == expected else "❌"
        print(f"{status} {url} -> {result} (esperado: {expected})")
    
    return True

if __name__ == "__main__":
    test_deteccion_endpoint()