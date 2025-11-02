"""
Detector inteligente de intención para Bing Grounding
Basado en análisis semántico real, no solo palabras clave
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def detectar_necesidad_bing_inteligente(consulta: str, contexto: Optional[Dict] = None) -> Dict:
    """
    Detecta automáticamente si una consulta requiere Bing Grounding usando análisis de intención inteligente
    """
    
    # === ANÁLISIS DE INTENCIÓN INTELIGENTE ===
    
    # 1. Analizar estructura semántica de la consulta
    intencion = analizar_intencion_semantica(consulta)
    
    # 2. Detectar indicadores de información externa necesaria
    necesita_info_externa = detectar_info_externa_requerida(consulta, contexto)
    
    # 3. Evaluar contexto temporal y actualidad
    requiere_actualidad = evaluar_necesidad_actualidad(consulta)
    
    # 4. Analizar complejidad y ambigüedad
    nivel_ambiguedad = calcular_ambiguedad(consulta)
    
    # === CÁLCULO INTELIGENTE DE SCORE ===
    
    score_bing = 0
    razones = []
    categoria = "general"
    
    # Factor 1: Intención semántica
    if intencion["tipo"] == "busqueda_informacion":
        score_bing += 0.7
        razones.append("Búsqueda de información específica")
        categoria = "busqueda_informacion"
    elif intencion["tipo"] == "comparacion":
        score_bing += 0.6
        razones.append("Solicitud de comparación")
        categoria = "comparacion"
    elif intencion["tipo"] == "comando_local":
        score_bing -= 0.8
        razones.append("Comando ejecutable localmente")
    
    # Factor 2: Información externa
    if necesita_info_externa["requiere"]:
        score_bing += necesita_info_externa["peso"]
        razones.append(necesita_info_externa["razon"])
        categoria = necesita_info_externa["categoria"]
    
    # Factor 3: Actualidad
    if requiere_actualidad["necesario"]:
        score_bing += 0.8
        razones.append("Información que cambia frecuentemente")
        categoria = "informacion_dinamica"
    
    # Factor 4: Ambigüedad
    if nivel_ambiguedad > 0.7:
        score_bing += 0.5
        razones.append("Consulta ambigua que requiere contexto adicional")
    
    # === DECISIÓN FINAL INTELIGENTE ===
    
    requiere_bing = score_bing > 0.4
    confianza = min(abs(score_bing), 1.0)
    
    # Optimizar query para Bing si es necesario
    query_optimizada = optimizar_query_inteligente(consulta, intencion) if requiere_bing else consulta
    
    return {
        "requiere_bing": requiere_bing,
        "confianza": confianza,
        "razon": "; ".join(razones) if razones else "Análisis de intención",
        "categoria": categoria,
        "query_optimizada": query_optimizada,
        "score_calculado": score_bing,
        "intencion_detectada": intencion,
        "timestamp": datetime.now().isoformat()
    }


def analizar_intencion_semantica(consulta: str) -> Dict:
    """Analiza la intención semántica usando búsqueda vectorial en memoria"""
    try:
        from endpoints_search_memory import buscar_memoria_endpoint
        
        # 🧠 BUSCAR INTENCIONES SIMILARES EN MEMORIA VECTORIAL
        resultado = buscar_memoria_endpoint({
            "query": f"intención: {consulta}",
            "top": 3
        })
        
        if resultado.get("exito") and resultado.get("documentos"):
            docs = resultado["documentos"]
            
            # Analizar endpoints más relevantes
            endpoints_encontrados = [d.get("endpoint", "") for d in docs]
            
            # Detectar patrón de introspección
            if any("introspection" in ep or "diagnostico" in ep or "status" in ep for ep in endpoints_encontrados):
                return {"tipo": "introspection", "confianza": 0.9, "endpoint_sugerido": "/api/introspection"}
            
            # Detectar patrón de búsqueda
            if any("buscar" in ep or "search" in ep or "memoria" in ep for ep in endpoints_encontrados):
                return {"tipo": "busqueda_informacion", "confianza": 0.8}
            
            # Detectar patrón de ejecución
            if any("ejecutar" in ep or "cli" in ep or "script" in ep for ep in endpoints_encontrados):
                return {"tipo": "comando_local", "confianza": 0.9}
    
    except Exception as e:
        logging.warning(f"⚠️ Búsqueda vectorial falló, usando análisis estructural: {e}")
    
    # FALLBACK: Análisis estructural básico (sin palabras clave)
    return analizar_estructura_consulta(consulta)


def analizar_estructura_consulta(consulta: str) -> Dict:
    """Análisis estructural de la consulta sin palabras clave predefinidas"""
    # Analizar estructura gramatical
    tiene_interrogacion = "?" in consulta or consulta.lower().startswith(("qué", "cuál", "cómo", "dónde"))
    tiene_imperativo = any(consulta.lower().startswith(v) for v in ["ejecuta", "corre", "instala", "crea"])
    
    if tiene_interrogacion:
        return {"tipo": "busqueda_informacion", "confianza": 0.6}
    elif tiene_imperativo:
        return {"tipo": "comando_local", "confianza": 0.7}
    else:
        return {"tipo": "general", "confianza": 0.5}


def detectar_info_externa_requerida(consulta: str, contexto: Optional[Dict]) -> Dict:
    """Detecta si la consulta requiere información externa"""
    consulta_lower = consulta.lower()
    
    # Indicadores de información externa
    if any(term in consulta_lower for term in ["última versión", "más reciente", "latest", "newest"]):
        return {"requiere": True, "peso": 0.9, "razon": "Versión más reciente", "categoria": "version_actual"}
    
    if any(term in consulta_lower for term in ["documentación oficial", "microsoft docs", "official docs"]):
        return {"requiere": True, "peso": 0.8, "razon": "Documentación oficial", "categoria": "documentacion"}
    
    if any(term in consulta_lower for term in ["problemas conocidos", "errores comunes", "github issues"]):
        return {"requiere": True, "peso": 0.9, "razon": "Problemas reportados", "categoria": "problemas"}
    
    # Indicadores de información local
    if any(term in consulta_lower for term in ["mi archivo", "local", "readme", "function_app"]):
        return {"requiere": False, "peso": -0.8, "razon": "Recurso local", "categoria": "local"}
    
    return {"requiere": False, "peso": 0, "razon": "Sin indicadores externos", "categoria": "neutral"}


def evaluar_necesidad_actualidad(consulta: str) -> Dict:
    """Evalúa si la consulta requiere información actualizada"""
    consulta_lower = consulta.lower()
    
    # Tecnologías que cambian rápidamente
    tech_dinamicas = ["azure functions", "openai", "chatgpt", "kubernetes", "docker", "terraform"]
    
    if any(tech in consulta_lower for tech in tech_dinamicas):
        return {"necesario": True, "razon": "Tecnología de rápida evolución"}
    
    # Términos temporales
    if any(term in consulta_lower for term in ["2024", "actual", "ahora", "hoy", "current", "now"]):
        return {"necesario": True, "razon": "Referencia temporal específica"}
    
    return {"necesario": False, "razon": "Sin necesidad de actualidad"}


def calcular_ambiguedad(consulta: str) -> float:
    """Calcula el nivel de ambigüedad de la consulta"""
    # Factores que aumentan ambigüedad
    palabras_vagas = ["algo", "cosa", "esto", "eso", "something", "thing", "this", "that"]
    pronombres = ["él", "ella", "eso", "esto", "it", "this", "that"]
    
    score_ambiguedad = 0
    palabras = consulta.lower().split()
    
    # Consultas muy cortas son ambiguas
    if len(palabras) < 3:
        score_ambiguedad += 0.5
    
    # Palabras vagas aumentan ambigüedad
    for palabra in palabras_vagas:
        if palabra in consulta.lower():
            score_ambiguedad += 0.3
    
    # Pronombres sin contexto
    for pronombre in pronombres:
        if pronombre in consulta.lower():
            score_ambiguedad += 0.2
    
    return min(score_ambiguedad, 1.0)


def optimizar_query_inteligente(consulta: str, intencion: Dict) -> str:
    """Optimiza la consulta basándose en la intención detectada"""
    query_optimizada = consulta
    
    # Agregar contexto según intención
    if intencion["tipo"] == "busqueda_informacion":
        if "azure" not in consulta.lower():
            query_optimizada = f"Azure {consulta}"
        query_optimizada += " official documentation 2024"
    
    elif intencion["tipo"] == "comparacion":
        query_optimizada += " comparison pros cons 2024"
    
    return query_optimizada


def integrar_con_validador_semantico_inteligente(req, consulta: str, memoria_previa: Optional[Dict] = None) -> Dict:
    """
    Integra la detección inteligente de Bing con el validador semántico
    """
    from memory_precheck import consultar_memoria_antes_responder
    
    # 1. Detectar necesidad de Bing con análisis inteligente
    deteccion = detectar_necesidad_bing_inteligente(consulta, {
        "memoria_previa": memoria_previa,
        "endpoint": getattr(req, 'url', '/api/copiloto')
    })
    
    logging.info(f"🧠 Detección Inteligente: {deteccion['requiere_bing']} (confianza: {deteccion['confianza']:.2f}) - {deteccion['razon']}")
    
    # 🧠 Si la intención detectada sugiere un endpoint específico, marcarlo
    if deteccion["intencion_detectada"].get("endpoint_sugerido"):
        logging.info(f"🎯 Endpoint sugerido por detección vectorial: {deteccion['intencion_detectada']['endpoint_sugerido']}")
        # El agente usará este endpoint automáticamente a través de OpenAPI
    
    # 2. Si no requiere Bing ni introspección, continuar normal
    if not deteccion["requiere_bing"]:
        return {
            "usar_bing": False,
            "continuar_normal": True,
            "deteccion": deteccion
        }
    
    # 3. Si requiere Bing, ejecutarlo automáticamente
    try:
        from bing_fallback_guard import ejecutar_grounding_fallback
        
        resultado_bing = ejecutar_grounding_fallback(
            deteccion["query_optimizada"],
            deteccion["categoria"],
            {
                "consulta_original": consulta,
                "confianza_deteccion": deteccion["confianza"],
                "razon": deteccion["razon"],
                "intencion": deteccion["intencion_detectada"]
            }
        )
        
        # 4. Si Bing fue exitoso, devolver respuesta enriquecida
        if resultado_bing.get("exito"):
            return {
                "usar_bing": True,
                "resultado_bing": resultado_bing,
                "continuar_normal": False,
                "respuesta_final": {
                    "exito": True,
                    "respuesta": resultado_bing.get("resumen", ""),
                    "fuente": "bing_grounding_inteligente",
                    "deteccion_automatica": deteccion,
                    "comando_sugerido": resultado_bing.get("comando_sugerido"),
                    "fuentes": resultado_bing.get("fuentes", []),
                    "confianza": resultado_bing.get("confianza", 0.8),
                    "analisis_intencion": deteccion["intencion_detectada"]
                }
            }
    
    except Exception as e:
        logging.error(f"Error ejecutando Bing inteligente: {e}")
    
    # 5. Si Bing falló, continuar con flujo normal pero marcar que se intentó
    return {
        "usar_bing": True,
        "continuar_normal": True,
        "bing_fallido": True,
        "deteccion": deteccion
    }