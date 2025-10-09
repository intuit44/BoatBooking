"""
Hooks inteligentes para integrar Bing Grounding en puntos críticos del sistema
Se activa automáticamente cuando el sistema interno no puede continuar
"""
import os
import json
import logging
import requests
from datetime import datetime

def should_trigger_bing_grounding(error_info: dict, contexto: str) -> bool:
    """
    Determina dinámicamente si debe activarse Bing Grounding
    Basado en detección de insuficiencia interna
    """
    triggers = {
        # Comandos CLI fallidos
        "COMMAND_NOT_FOUND": True,
        "SyntaxError": True, 
        "MissingParameter": bool(error_info.get("memoria_consultada", False)) and not error_info.get("memoria_encontrada", False),

        
        # Herramientas desconocidas
        "tool_not_found": "tool not found" in contexto.lower(),
        "accion_no_mapeada": "acción no mapeada" in contexto.lower(),
        
        # Errores de API/SDK
        "APIError": True,
        "InvalidConfig": True,
        "AuthenticationError": True,
        
        # Ambigüedad o falta de documentación
        "ambiguedad": "múltiples opciones" in contexto.lower(),
        "funcion_no_documentada": "sin definición" in contexto.lower(),
        
        # Optimización solicitada
        "optimization_request": "optimiz" in contexto.lower() or "mejor" in contexto.lower()
    }
    
    error_type = error_info.get("tipo_error", "")
    
    # Evaluar triggers dinámicamente
    for trigger, condition in triggers.items():
        if trigger == error_type:
            if isinstance(condition, bool):
                return condition
            elif callable(condition):
                return condition()
    
    # Triggers adicionales basados en contexto
    if any(keyword in contexto.lower() for keyword in ["no sé", "desconozco", "no encontrado", "fallo", "error"]):
        return True
    
    return False

def llamar_bing_grounding(query: str, contexto: str, intencion_original: str = "", prioridad: str = "normal") -> dict:
    """
    Llama al endpoint de Bing Grounding de forma inteligente
    """
    try:
        payload = {
            "query": query,
            "contexto": contexto,
            "intencion_original": intencion_original,
            "prioridad": prioridad
        }
        
        # Determinar URL base
        base_url = "http://localhost:7071"  # Local por defecto
        if os.environ.get("WEBSITE_SITE_NAME"):  # En Azure
            base_url = f"https://{os.environ.get('WEBSITE_SITE_NAME')}.azurewebsites.net"
        
        response = requests.post(
            f"{base_url}/api/bing-grounding",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "exito": False,
                "error": f"Bing Grounding error: {response.status_code}",
                "detalles": response.text[:200]
            }
            
    except Exception as e:
        logging.error(f"Error llamando Bing Grounding: {e}")
        return {"exito": False, "error": str(e)}

def construir_comando_desde_grounding(grounding_result: dict, comando_original: str = "") -> str:
    """
    Construye nuevo comando basado en resultado de Bing Grounding
    """
    if not grounding_result.get("exito"):
        return comando_original
    
    resultado = grounding_result.get("resultado", {})
    comando_sugerido = resultado.get("comando_sugerido", "")
    
    if comando_sugerido:
        # Si hay comando sugerido específico, usarlo
        return comando_sugerido
    
    # Si no, intentar extraer de resumen
    resumen = resultado.get("resumen", "")
    if "az " in resumen:
        import re
        match = re.search(r'az [a-z-]+ [a-z-]+ [^\n\r.]+', resumen)
        if match:
            return match.group(0)
    
    return comando_original

# Hook para /api/ejecutar-cli
def hook_ejecutar_cli_bing(error_info: dict, comando: str, intentos_log: list) -> dict:
    """
    Hook específico para ejecutar-cli que activa Bing cuando no puede continuar
    """
    contexto = f"comando fallido en ejecutar-cli: {comando}"
    
    if should_trigger_bing_grounding(error_info, contexto):
        logging.info(f"🔍 Activando Bing Grounding para comando: {comando}")
        
        # Generar query inteligente
        campo_faltante = error_info.get("campo_faltante", "")
        if campo_faltante:
            query = f"cómo usar {campo_faltante} en comando Azure CLI {comando}"
        else:
            query = f"cómo arreglar error en comando Azure CLI: {comando}"
        
        grounding_result = llamar_bing_grounding(
            query=query,
            contexto=contexto,
            intencion_original="ejecutar comando CLI",
            prioridad="alta"
        )
        
        if grounding_result.get("exito"):
            comando_mejorado = construir_comando_desde_grounding(grounding_result, comando)
            
            return {
                "exito": True,
                "comando_original": comando,
                "comando_mejorado": comando_mejorado,
                "fuente": "bing_grounding",
                "aprendizaje_aplicado": True,
                "grounding_data": grounding_result
            }
    
    return {"exito": False, "bing_consultado": False}

# Hook para /api/hybrid
def hook_hybrid_bing(parsed_command: dict, error_context: str) -> dict:
    """
    Hook para hybrid que activa Bing cuando no puede procesar comando
    """
    if "error" in parsed_command or "no se identificó" in error_context.lower():
        contexto = f"comando no reconocido en hybrid: {parsed_command}"
        
        if should_trigger_bing_grounding({"tipo_error": "COMMAND_NOT_FOUND"}, contexto):
            query = f"cómo interpretar comando: {parsed_command.get('endpoint', 'unknown')}"
            
            grounding_result = llamar_bing_grounding(
                query=query,
                contexto=contexto,
                intencion_original="procesar comando híbrido"
            )
            
            if grounding_result.get("exito"):
                return {
                    "exito": True,
                    "comando_interpretado": True,
                    "sugerencia": grounding_result.get("resultado", {}).get("resumen", ""),
                    "fuente": "bing_grounding"
                }
    
    return {"exito": False}

# Hook para /api/render-error  
def hook_render_error_bing(error_code: str, error_message: str) -> dict:
    """
    Hook para render-error que busca soluciones cuando no hay respuesta interna
    """
    contexto = f"error no documentado: {error_code}"
    
    if should_trigger_bing_grounding({"tipo_error": "funcion_no_documentada"}, contexto):
        query = f"cómo resolver error {error_code} en Azure: {error_message}"
        
        grounding_result = llamar_bing_grounding(
            query=query,
            contexto=contexto,
            intencion_original="resolver error"
        )
        
        if grounding_result.get("exito"):
            return {
                "exito": True,
                "solucion_encontrada": True,
                "solucion": grounding_result.get("resultado", {}).get("resumen", ""),
                "fuentes": grounding_result.get("resultado", {}).get("fuentes", [])
            }
    
    return {"exito": False}