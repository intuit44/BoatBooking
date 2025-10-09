"""
Módulo centralizado de fallback con Bing Grounding
Última línea de defensa antes de errores 500/422
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

def verifica_si_requiere_grounding(prompt: str, contexto: str, error_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Función centralizada que determina si se necesita Bing Grounding
    Actúa como última línea de defensa antes de fallar
    """
    
    # Detectar pérdida de conciencia del sistema
    triggers_criticos = [
        # Scripts y generación de código
        "script generation failed",
        "no template found", 
        "syntax error in generated code",
        "unknown script type",
        
        # Procesamiento de lenguaje natural
        "intent not recognized",
        "ambiguous request",
        "insufficient context",
        "no matching pattern",
        
        # Memoria insuficiente
        "no memory available",
        "empty memory result",
        "memory query failed",
        "no historical data",
        
        # Errores genéricos que indican pérdida de control
        "internal error",
        "unexpected failure",
        "operation not supported",
        "configuration missing"
    ]
    
    # Palabras clave en prompt que indican necesidad externa
    keywords_externos = [
        "no sé", "desconozco", "no entiendo", "no puedo",
        "help", "ayuda", "cómo", "how to", "example",
        "documentation", "best practice", "optimize"
    ]
    
    # Evaluar triggers
    contexto_lower = contexto.lower()
    prompt_lower = prompt.lower()
    
    # 1. Triggers críticos en contexto
    for trigger in triggers_criticos:
        if trigger in contexto_lower:
            return {
                "requiere_grounding": True,
                "razon": f"Trigger crítico detectado: {trigger}",
                "prioridad": "alta",
                "query_sugerida": _generar_query_inteligente(prompt, contexto, trigger)
            }
    
    # 2. Keywords en prompt
    for keyword in keywords_externos:
        if keyword in prompt_lower:
            return {
                "requiere_grounding": True,
                "razon": f"Solicitud de conocimiento externo: {keyword}",
                "prioridad": "normal",
                "query_sugerida": _generar_query_inteligente(prompt, contexto, keyword)
            }
    
    # 3. Error info específico
    if error_info:
        if error_info.get("tipo_error") in ["COMMAND_NOT_FOUND", "SyntaxError", "APIError"]:
            return {
                "requiere_grounding": True,
                "razon": f"Error no resoluble internamente: {error_info.get('tipo_error')}",
                "prioridad": "alta",
                "query_sugerida": _generar_query_desde_error(error_info, prompt)
            }
        
        # Memoria consultada pero sin resultado
        if (error_info.get("memoria_consultada") and 
            not error_info.get("memoria_encontrada")):
            return {
                "requiere_grounding": True,
                "razon": "Memoria insuficiente para resolver",
                "prioridad": "normal",
                "query_sugerida": _generar_query_inteligente(prompt, contexto, "memory_insufficient")
            }
    
    return {"requiere_grounding": False}

def ejecutar_grounding_fallback(prompt: str, contexto: str, error_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Ejecuta Bing Grounding como fallback y devuelve resultado procesado
    """
    
    verificacion = verifica_si_requiere_grounding(prompt, contexto, error_info)
    
    if not verificacion.get("requiere_grounding"):
        return {"exito": False, "razon": "No requiere grounding"}
    
    try:
        # Importar función de llamada a Bing
        from bing_integration_hooks import llamar_bing_grounding
        
        query = verificacion.get("query_sugerida", prompt)
        prioridad = verificacion.get("prioridad", "normal")
        
        logging.info(f"🔍 Fallback Guard activando Bing: {query}")
        
        resultado_bing = llamar_bing_grounding(
            query=query,
            contexto=contexto,
            intencion_original=prompt,
            prioridad=prioridad
        )
        
        if resultado_bing.get("exito"):
            return {
                "exito": True,
                "fuente": "bing_grounding_fallback",
                "resultado": resultado_bing.get("resultado", {}),
                "accion_sugerida": resultado_bing.get("accion_sugerida", ""),
                "metadata": {
                    "trigger_razon": verificacion.get("razon"),
                    "query_usada": query,
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            return {
                "exito": False,
                "error": "Bing Grounding falló",
                "detalles": resultado_bing.get("error", "")
            }
            
    except Exception as e:
        logging.error(f"Error en fallback guard: {e}")
        return {
            "exito": False,
            "error": f"Fallback guard error: {str(e)}"
        }

def _generar_query_inteligente(prompt: str, contexto: str, trigger: str) -> str:
    """Genera query inteligente según el trigger detectado"""
    
    queries_por_trigger = {
        "script generation failed": f"how to generate script for: {prompt}",
        "no template found": f"template example for: {prompt}",
        "syntax error": f"fix syntax error in: {prompt}",
        "intent not recognized": f"how to interpret: {prompt}",
        "memory_insufficient": f"Azure documentation for: {prompt}",
        "no sé": f"how to {prompt} in Azure",
        "cómo": f"Azure CLI example: {prompt}",
        "help": f"Azure help documentation: {prompt}"
    }
    
    return queries_por_trigger.get(trigger, f"Azure {prompt} documentation example")

def _generar_query_desde_error(error_info: Dict, prompt: str) -> str:
    """Genera query específica desde información de error"""
    
    tipo_error = error_info.get("tipo_error", "")
    campo_faltante = error_info.get("campo_faltante", "")
    
    if tipo_error == "MissingParameter" and campo_faltante:
        return f"Azure CLI {campo_faltante} parameter example: {prompt}"
    elif tipo_error == "COMMAND_NOT_FOUND":
        return f"Azure CLI command syntax: {prompt}"
    elif tipo_error == "SyntaxError":
        return f"fix Azure CLI syntax error: {prompt}"
    else:
        return f"resolve Azure error {tipo_error}: {prompt}"

def aplicar_fallback_a_respuesta(respuesta_original: Dict, fallback_result: Dict) -> Dict:
    """
    Aplica resultado de fallback a respuesta original
    Mejora la respuesta en lugar de reemplazarla completamente
    """
    
    if not fallback_result.get("exito"):
        # Si fallback falló, mantener respuesta original pero agregar contexto
        respuesta_original["fallback_intentado"] = True
        respuesta_original["fallback_error"] = fallback_result.get("error", "")
        return respuesta_original
    
    # Si fallback tuvo éxito, enriquecer respuesta
    resultado_bing = fallback_result.get("resultado", {})
    
    # Agregar información de Bing a respuesta original
    respuesta_mejorada = respuesta_original.copy()
    respuesta_mejorada.update({
        "fallback_aplicado": True,
        "conocimiento_externo": {
            "resumen": resultado_bing.get("resumen", ""),
            "fuentes": resultado_bing.get("fuentes", []),
            "comando_sugerido": resultado_bing.get("comando_sugerido", "")
        },
        "accion_sugerida": fallback_result.get("accion_sugerida", ""),
        "metadata_fallback": fallback_result.get("metadata", {})
    })
    
    # Si había error, intentar resolverlo
    if not respuesta_original.get("exito", True):
        comando_sugerido = resultado_bing.get("comando_sugerido")
        if comando_sugerido:
            respuesta_mejorada["comando_alternativo"] = comando_sugerido
            respuesta_mejorada["exito"] = True  # Marcar como potencialmente resuelto
    
    return respuesta_mejorada