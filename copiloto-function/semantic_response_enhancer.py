"""
🧠 Mejorador de Respuestas Semánticas
Transforma respuestas básicas en respuestas contextuales enriquecidas
"""

import logging
from typing import Dict, Any, Optional

def enhance_response_with_semantic_context(
    original_response: str, 
    memoria_contexto: Dict[str, Any], 
    user_query: str = ""
) -> str:
    """
    Mejora una respuesta básica con contexto semántico rico
    """
    
    if not memoria_contexto or not memoria_contexto.get("tiene_historial"):
        return original_response
    
    try:
        # Extraer información semántica
        interpretacion = memoria_contexto.get("interpretacion_semantica", "")
        contexto_inteligente = memoria_contexto.get("contexto_inteligente", {})
        interacciones = memoria_contexto.get("interacciones_recientes", [])
        
        # Detectar tipo de consulta del usuario
        query_type = detect_query_intent(user_query)
        
        # Generar respuesta enriquecida según el tipo
        if query_type == "historical_inquiry":
            return generate_historical_response(interacciones, interpretacion, contexto_inteligente)
        elif query_type == "context_request":
            return generate_contextual_response(interacciones, interpretacion, contexto_inteligente)
        elif query_type == "continuation":
            return generate_continuation_response(interacciones, interpretacion, contexto_inteligente)
        else:
            return enhance_general_response(original_response, interacciones, interpretacion)
            
    except Exception as e:
        logging.error(f"Error mejorando respuesta semántica: {e}")
        return original_response

def detect_query_intent(user_query: str) -> str:
    """Detecta la intención de la consulta del usuario"""
    
    query_lower = user_query.lower()
    
    # Consultas históricas (AMPLIADO)
    historical_keywords = [
        "antes", "habíamos", "hablando", "hablamos", "conversando", 
        "detectado", "anterior", "previo", "hicimos", "quedamos",
        "estuvimos", "estabamos", "discutimos", "vimos", "tratamos"
    ]
    if any(word in query_lower for word in historical_keywords):
        return "historical_inquiry"
    
    # Solicitudes de contexto
    if any(word in query_lower for word in ["contexto", "semántico", "enriquecido", "validar", "resumen"]):
        return "context_request"
    
    # Continuación de conversación
    if any(word in query_lower for word in ["continuar", "siguiente", "ahora", "después", "sigue"]):
        return "continuation"
    
    return "general"

def generate_historical_response(
    interacciones: list, 
    interpretacion: str, 
    contexto_inteligente: dict
) -> str:
    """Genera respuesta rica para consultas históricas"""
    
    if not interacciones:
        return "No hay historial previo disponible para analizar."
    
    # Analizar patrones en las interacciones
    endpoints_recientes = [i.get("endpoint", "unknown") for i in interacciones[:5]]
    acciones_exitosas = sum(1 for i in interacciones if i.get("exito", True))
    total_acciones = len(interacciones)
    
    # Detectar patrones de actividad
    patron_detectado = analyze_activity_pattern(endpoints_recientes)
    
    response = f"""ANALISIS CONTEXTUAL COMPLETO

Patron de Actividad Detectado: {patron_detectado}

Metricas de Sesion:
- Total de interacciones analizadas: {total_acciones}
- Tasa de exito: {(acciones_exitosas/total_acciones)*100:.1f}%
- Modo de operacion: {contexto_inteligente.get('modo_operacion', 'general')}

Interpretacion Semantica: {interpretacion}

Ultimas Actividades Significativas:"""

    # Agregar detalles de las últimas interacciones
    for i, interaccion in enumerate(interacciones[:3], 1):
        endpoint = interaccion.get("endpoint", "unknown")
        timestamp = interaccion.get("timestamp", "")
        exito = "OK" if interaccion.get("exito", True) else "ERROR"
        
        # Formatear timestamp
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            tiempo = dt.strftime("%H:%M")
        except:
            tiempo = "??:??"
        
        response += f"\n{i}. [{tiempo}] {endpoint.replace('_', ' ').title()} {exito}"
    
    response += f"\n\nRecomendacion: Basandome en este patron, sugiero {generate_smart_recommendation(patron_detectado, endpoints_recientes)}"
    
    return response

def generate_contextual_response(
    interacciones: list, 
    interpretacion: str, 
    contexto_inteligente: dict
) -> str:
    """Genera respuesta para solicitudes de contexto enriquecido"""
    
    modo_operacion = contexto_inteligente.get('modo_operacion', 'general')
    contexto_seleccionado = contexto_inteligente.get('contexto_seleccionado', 0)
    total_analizado = contexto_inteligente.get('total_analizado', 0)
    
    response = f"""CONTEXTO SEMANTICO ENRIQUECIDO

Estado Actual del Sistema:
- Modo de operacion: {modo_operacion.replace('_', ' ').title()}
- Contexto procesado: {contexto_seleccionado}/{total_analizado} interacciones
- Interpretacion: {interpretacion}

Flujo de Procesamiento Aplicado:
1. Recuperacion de memoria universal (50 interacciones)
2. Clasificacion semantica multi-patron
3. Validacion y optimizacion de contexto
4. Generacion de respuesta enriquecida

Analisis de Calidad:"""

    if interacciones:
        # Analizar calidad de las interacciones
        endpoints_unicos = len(set(i.get("endpoint", "") for i in interacciones))
        response += f"""
- Diversidad de consultas: {endpoints_unicos} tipos diferentes
- Cobertura temporal: {len(interacciones)} interacciones recientes
- Consistencia: {"Alta" if all(i.get("exito", True) for i in interacciones[:3]) else "Media"}"""
    
    response += f"\n\n🎯 **Capacidades Activas**: Memoria semántica, clasificación inteligente, optimización de tokens, validación de contexto"
    
    return response

def generate_continuation_response(
    interacciones: list, 
    interpretacion: str, 
    contexto_inteligente: dict
) -> str:
    """Genera respuesta para continuación de conversación"""
    
    if not interacciones:
        return "Iniciando nueva sesión. ¿En qué puedo ayudarte?"
    
    ultimo_endpoint = interacciones[0].get("endpoint", "unknown") if interacciones else "unknown"
    ultimo_exito = interacciones[0].get("exito", True) if interacciones else True
    
    response = f"""CONTINUANDO DESDE CONTEXTO PREVIO

Punto de Continuacion: 
- Ultima accion: {ultimo_endpoint.replace('_', ' ').title()}
- Estado: {"Completada exitosamente" if ultimo_exito else "Requiere atencion"}

{interpretacion}

Opciones de Continuacion:"""

    # Sugerir acciones basadas en el contexto
    suggestions = generate_continuation_suggestions(ultimo_endpoint, interacciones)
    for i, suggestion in enumerate(suggestions, 1):
        response += f"\n{i}. {suggestion}"
    
    return response

def enhance_general_response(
    original_response: str, 
    interacciones: list, 
    interpretacion: str
) -> str:
    """Mejora respuesta general con contexto semántico"""
    
    if not interacciones:
        return original_response
    
    # Agregar contexto semántico al final
    context_note = f"\n\n---\nContexto: {interpretacion}"
    
    return original_response + context_note

def analyze_activity_pattern(endpoints: list) -> str:
    """Analiza patrón de actividad en los endpoints"""
    
    if not endpoints:
        return "Sin actividad detectada"
    
    # Contar frecuencias
    from collections import Counter
    endpoint_counts = Counter(endpoints)
    most_common = endpoint_counts.most_common(1)[0] if endpoint_counts else ("unknown", 0)
    
    # Detectar patrones específicos
    if "verificar" in str(endpoints):
        return "Flujo de diagnóstico y verificación"
    elif "hybrid" in str(endpoints):
        return "Procesamiento híbrido multi-fuente"
    elif "ejecutar" in str(endpoints):
        return "Ejecución de comandos y scripts"
    elif most_common[1] > 1:
        return f"Patrón repetitivo en {most_common[0]}"
    else:
        return "Actividad diversificada"

def generate_smart_recommendation(patron: str, endpoints: list) -> str:
    """Genera recomendación inteligente basada en el patrón"""
    
    if "diagnóstico" in patron:
        return "continuar con la verificación de componentes restantes o proceder con la corrección de issues detectados."
    elif "híbrido" in patron:
        return "aprovechar la integración multi-fuente para consultas complejas o análisis cruzados."
    elif "ejecución" in patron:
        return "revisar los resultados de los comandos ejecutados y planificar los siguientes pasos."
    elif "repetitivo" in patron:
        return "considerar automatizar esta secuencia o explorar alternativas más eficientes."
    else:
        return "mantener la diversidad de acciones para una cobertura completa del sistema."

def generate_continuation_suggestions(ultimo_endpoint: str, interacciones: list) -> list:
    """Genera sugerencias de continuación basadas en el contexto"""
    
    suggestions = []
    
    if "verificar" in ultimo_endpoint:
        suggestions.append("Revisar resultados de la verificación y corregir issues detectados")
        suggestions.append("Ejecutar diagnóstico completo del sistema")
    elif "ejecutar" in ultimo_endpoint:
        suggestions.append("Analizar output del comando ejecutado")
        suggestions.append("Continuar con el siguiente paso del flujo")
    elif "hybrid" in ultimo_endpoint:
        suggestions.append("Aprovechar procesamiento híbrido para consultas complejas")
        suggestions.append("Validar resultados de múltiples fuentes")
    else:
        suggestions.append("Continuar con la siguiente acción planificada")
        suggestions.append("Solicitar más contexto si es necesario")

    return suggestions
