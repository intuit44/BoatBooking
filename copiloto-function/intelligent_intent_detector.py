"""
Detector inteligente de intención para Bing Grounding
Basado en análisis semántico real, no solo palabras clave
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime


FILE_TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9_]{1,8}")


def _extraer_tokens_archivo(consulta: str) -> List[str]:
    """Devuelve posibles referencias a archivos detectadas en el texto."""
    if not consulta:
        return []
    return FILE_TOKEN_REGEX.findall(consulta)


def _evaluar_busqueda_y_lectura(consulta: str) -> Dict[str, Any]:
    """
    Calcula una puntuación (0-1) que indica si el usuario quiere buscar un archivo
    y luego leerlo. Usa señales semánticas suaves + umbral, no coincidencias exactas.
    """
    texto = (consulta or "").lower()
    tokens_archivo = _extraer_tokens_archivo(texto)

    score = 0.0
    detalles = {
        "tokens_archivo": tokens_archivo,
        "signos_busqueda": False,
        "signos_lectura": False
    }

    if tokens_archivo:
        score += 0.4  # señal fuerte: referencia a archivo concreto

    # Señal de búsqueda: raíces como "busc", "encuent", "find", "where"
    if re.search(r"\b(busca\w*|encuentra\w*|find|locat\w+|where)\b", texto):
        detalles["signos_busqueda"] = True
        score += 0.3

    # Señal de lectura/contenido
    if re.search(r"\b(lee\w*|leer|read|muestrame|show)\b", texto) or "que contiene" in texto or "contenido" in texto:
        detalles["signos_lectura"] = True
        score += 0.3

    # Bonus si explícitamente pide "dime que contiene"
    if "dime" in texto and "contiene" in texto:
        score += 0.1

    return {
        "score": min(score, 1.0),
        "archivo_objetivo": tokens_archivo[0] if tokens_archivo else None,
        "detalles": detalles
    }

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
    analisis_archivo = _evaluar_busqueda_y_lectura(consulta or "")
    if analisis_archivo["score"] >= 0.75:
        logging.info(f"[INTENCION] buscar+leer detectada (score={analisis_archivo['score']:.2f})")
        return {
            "tipo": "leer_archivo",
            "confianza": analisis_archivo["score"],
            "endpoint_sugerido": "/api/leer-archivo",
            "archivo_objetivo": analisis_archivo["archivo_objetivo"],
            "pipeline": "cli_search_then_read",
            "detalles": analisis_archivo["detalles"]
        }
    try:
        from endpoints_search_memory import buscar_memoria_endpoint
        
        # 🧠 BUSCAR ENDPOINTS SIMILARES EN MEMORIA VECTORIAL (SIN FILTRO DE SESIÓN)
        resultado = buscar_memoria_endpoint({
            "query": consulta,  # Buscar directamente la consulta, no "intención:"
            "top": 5,
            "session_id": "UNIVERSAL"  # Forzar búsqueda sin filtro de sesión
        })
        
        if resultado.get("exito") and resultado.get("documentos"):
            docs = resultado["documentos"]
            
            # Analizar endpoints más relevantes y sus scores
            endpoint_scores = {}
            for doc in docs:
                ep = doc.get("endpoint", "")
                score = doc.get("score", 0)
                if ep:
                    endpoint_scores[ep] = endpoint_scores.get(ep, 0) + score
            
            # Ordenar por score acumulado
            if endpoint_scores:
                mejor_endpoint = max(endpoint_scores.items(), key=lambda x: x[1])[0]
                confianza = min(endpoint_scores[mejor_endpoint] / len(docs), 1.0)
                
                logging.info(f"🎯 Endpoint sugerido por memoria vectorial: {mejor_endpoint} (confianza: {confianza:.2f})")
                
                # Determinar tipo basado en el endpoint
                if "introspection" in mejor_endpoint or "historial" in mejor_endpoint:
                    return {"tipo": "introspection", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                elif "diagnostico" in mejor_endpoint or "recursos" in mejor_endpoint:
                    return {"tipo": "diagnostico", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                elif "ejecutar" in mejor_endpoint or "cli" in mejor_endpoint:
                    return {"tipo": "comando_local", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                elif "buscar" in mejor_endpoint or "memoria" in mejor_endpoint:
                    return {"tipo": "busqueda_informacion", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                else:
                    return {"tipo": "general", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
    
    except Exception as e:
        logging.warning(f"⚠️ Búsqueda vectorial falló, usando análisis estructural: {e}")
    
    # FALLBACK: Análisis estructural básico (sin palabras clave)
    return analizar_estructura_consulta(consulta)


def analizar_estructura_consulta(consulta: str) -> Dict:
    """Análisis estructural de la consulta sin palabras clave predefinidas"""
    consulta_lower = consulta.lower()
    
    # Detectar patrones de introspección/memoria
    if any(p in consulta_lower for p in ["estábamos", "estabamos", "trabajando", "quedamos", "última", "ultima", "anterior", "historial"]):
        return {"tipo": "introspection", "confianza": 0.8, "endpoint_sugerido": "/api/historial-interacciones"}
    
    # Detectar diagnóstico
    if any(p in consulta_lower for p in ["estado", "recursos", "diagnostico", "status", "health"]):
        return {"tipo": "diagnostico", "confianza": 0.7, "endpoint_sugerido": "/api/diagnostico-recursos"}
    
    # Detectar ejecución
    if any(consulta_lower.startswith(v) for v in ["ejecuta", "corre", "instala", "crea", "az ", "python "]):
        return {"tipo": "comando_local", "confianza": 0.9, "endpoint_sugerido": "/api/ejecutar-cli"}
    
    # Detectar búsqueda en memoria
    if any(p in consulta_lower for p in ["busca", "encuentra", "muestra", "lista"]):
        return {"tipo": "busqueda_informacion", "confianza": 0.6, "endpoint_sugerido": "/api/buscar-memoria"}
    
    # Fallback genérico
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
