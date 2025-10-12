# -*- coding: utf-8 -*-
"""
Nueva implementación robusta de gestionar_despliegue_http
"""

import json
import logging
import traceback
import os
from datetime import datetime
import azure.functions as func

# Importar funciones de soporte
from gestionar_despliegue_robusto import (
    extraer_payload_dinamico,
    resolver_comando_despliegue,
    validar_payload_completo,
    verificar_autenticacion_azure,
    ejecutar_accion_despliegue,
    generar_respuesta_error,
    generar_respuesta_exitosa
)

def nueva_gestionar_despliegue_http(req: func.HttpRequest) -> func.HttpResponse:
    """🚀 ENDPOINT ROBUSTO Y SEMÁNTICO PARA GESTIÓN DE DESPLIEGUES
    
    Sistema completamente adaptativo que acepta cualquier formato de payload y se adapta
    dinámicamente sin rechazar requests por condiciones predefinidas.
    
    Características:
    - ✅ Validador dinámico que acepta múltiples formatos
    - ✅ Detección automática de acción, entorno, target
    - ✅ Respuestas estructuradas con sugerencias adaptativas
    - ✅ Compatible con Foundry, CodeGPT, CLI sin conflictos
    - ✅ Tolerante al desorden de parámetros
    - ✅ Manejo de errores que guía a agentes para autocorrección
    """
    
    endpoint = "/api/gestionar-despliegue"
    method = "POST"
    
    # Generar run_id simple si no existe la función
    try:
        from function_app import get_run_id
        run_id = get_run_id(req)
    except:
        import uuid
        run_id = uuid.uuid4().hex[:8]
    
    try:
        # === PASO 1: EXTRACCIÓN ULTRA-FLEXIBLE DEL PAYLOAD ===
        payload_info = extraer_payload_dinamico(req)
        
        if not payload_info["exito"]:
            return generar_respuesta_error(
                codigo="PAYLOAD_EXTRACTION_ERROR",
                mensaje=payload_info["error"],
                sugerencias=payload_info.get("sugerencias", []),
                run_id=run_id,
                endpoint=endpoint
            )
        
        body = payload_info["datos"]
        formato_detectado = payload_info["formato"]
        
        logging.info(f"[{run_id}] Payload extraído: formato={formato_detectado}, keys={list(body.keys())}")
        
        # === PASO 2: RESOLUCIÓN SEMÁNTICA DE COMANDO ===
        comando_info = resolver_comando_despliegue(body, run_id)
        
        accion = comando_info["accion"]
        parametros = comando_info["parametros"]
        contexto = comando_info["contexto"]
        alias_usado = comando_info.get("alias_usado")
        
        logging.info(f"[{run_id}] Comando resuelto: accion={accion}, alias={alias_usado}")
        
        # === PASO 3: VALIDACIÓN ADAPTATIVA ===
        validacion = validar_payload_completo(accion, parametros, contexto, run_id)
        
        if not validacion["valido"]:
            return generar_respuesta_error(
                codigo="VALIDATION_ERROR",
                mensaje=validacion["error"],
                sugerencias=validacion["sugerencias"],
                detalles=validacion.get("detalles", {}),
                run_id=run_id,
                endpoint=endpoint
            )
        
        # === PASO 4: VERIFICACIÓN DE AUTENTICACIÓN ADAPTATIVA ===
        auth_result = verificar_autenticacion_azure(accion, run_id)
        
        if not auth_result["autenticado"]:
            return generar_respuesta_error(
                codigo="AUTHENTICATION_ERROR",
                mensaje=auth_result["error"],
                sugerencias=auth_result["sugerencias"],
                detalles=auth_result.get("detalles", {}),
                run_id=run_id,
                endpoint=endpoint,
                status_code=401
            )
        
        # === PASO 5: EJECUCIÓN DEL COMANDO ===
        resultado = ejecutar_accion_despliegue(accion, parametros, contexto, run_id)
        
        # === PASO 6: RESPUESTA ESTRUCTURADA ===
        return generar_respuesta_exitosa(
            accion=accion,
            resultado=resultado,
            alias_usado=alias_usado,
            formato_original=formato_detectado,
            run_id=run_id,
            endpoint=endpoint
        )
        
    except Exception as e:
        logging.error(f"[{run_id}] Error crítico en gestionar_despliegue: {str(e)}")
        logging.error(f"[{run_id}] Traceback: {traceback.format_exc()}")
        
        return generar_respuesta_error(
            codigo="CRITICAL_SYSTEM_ERROR",
            mensaje=f"Error crítico del sistema: {str(e)}",
            sugerencias=[
                "Verificar logs del sistema",
                "Reintentar con payload simplificado",
                "Contactar soporte si el error persiste"
            ],
            detalles={
                "tipo_error": type(e).__name__,
                "mensaje_original": str(e)
            },
            run_id=run_id,
            endpoint=endpoint,
            status_code=500
        )