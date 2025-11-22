"""
Detector inteligente de intencion para Bing Grounding
Basado en analisis semantico real, no solo palabras clave.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from semantic_intent_classifier import (
    classify_user_intent,
    should_use_grounding,
    enhance_with_context,
    preprocess_text,
)
from semantic_intent_parser import parse_natural_language

FILE_TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9_]{1,8}")


def _extraer_tokens_archivo(consulta: str) -> List[str]:
    """Devuelve posibles referencias a archivos detectadas en el texto."""
    if not consulta:
        return []
    return FILE_TOKEN_REGEX.findall(consulta)


def _evaluar_busqueda_y_lectura(consulta: str) -> Dict[str, Any]:
    """
    Calcula una puntuacion (0-1) que indica si el usuario quiere buscar un archivo
    y luego leerlo. Usa senales semanticas suaves + umbral, no coincidencias exactas.
    """
    texto = (consulta or "").lower()
    tokens_archivo = _extraer_tokens_archivo(texto)

    score = 0.0
    detalles = {
        "tokens_archivo": tokens_archivo,
        "signos_busqueda": False,
        "signos_lectura": False,
    }

    if tokens_archivo:
        score += 0.4  # senal fuerte: referencia a archivo concreto

    if re.search(r"\b(busca\w*|encuentra\w*|find|locat\w+|where)\b", texto):
        detalles["signos_busqueda"] = True
        score += 0.3

    if re.search(r"\b(lee\w*|leer|read|muestrame|show)\b", texto) or "que contiene" in texto or "contenido" in texto:
        detalles["signos_lectura"] = True
        score += 0.3

    if "dime" in texto and "contiene" in texto:
        score += 0.1

    return {
        "score": min(score, 1.0),
        "archivo_objetivo": tokens_archivo[0] if tokens_archivo else None,
        "detalles": detalles,
    }


def _construir_contexto_base(contexto: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normaliza el contexto de conversacion para facilitar el ajuste de confianza."""
    contexto = contexto or {}
    return {
        "previous_intent": contexto.get("previous_intent") or contexto.get("ultimo_intent"),
        "previous_endpoint": contexto.get("endpoint"),
        "tema_reciente": contexto.get("tema_reciente") or contexto.get("topic"),
        "memoria_previa": contexto.get("memoria_previa"),
    }


def _map_intent_to_tipo(intent: str) -> Optional[str]:
    intent_map = {
        "listar_storage": "comando_local",
        "listar_cosmos": "comando_local",
        "listar_functions": "comando_local",
        "listar_resources": "comando_local",
        "diagnosticar_sistema": "diagnostico",
        "revisar_logs": "revisar_logs",
        "ayuda_general": "general",
    }
    return intent_map.get(intent)


def analizar_intencion_semantica(consulta: str, contexto: Optional[Dict] = None) -> Dict:
    """Analiza la intencion semantica combinando clasificador, parser y memoria vectorial."""
    analisis_archivo = _evaluar_busqueda_y_lectura(consulta or "")
    if analisis_archivo["score"] >= 0.75:
        logging.info(f"[INTENCION] buscar+leer detectada (score={analisis_archivo['score']:.2f})")
        return {
            "tipo": "leer_archivo",
            "confianza": analisis_archivo["score"],
            "endpoint_sugerido": "/api/leer-archivo",
            "archivo_objetivo": analisis_archivo["archivo_objetivo"],
            "pipeline": "cli_search_then_read",
            "detalles": analisis_archivo["detalles"],
        }

    clasificacion = classify_user_intent(consulta)
    tipo_por_intent = _map_intent_to_tipo(clasificacion.get("intent", ""))
    if tipo_por_intent:
        return {
            "tipo": tipo_por_intent,
            "confianza": clasificacion.get("confidence", 0),
            "endpoint_sugerido": clasificacion.get("command"),
            "clasificacion_semantica": clasificacion,
        }

    try:
        from endpoints_search_memory import buscar_memoria_endpoint

        resultado = buscar_memoria_endpoint(
            {
                "query": consulta,
                "top": 5,
                "session_id": "UNIVERSAL",
            }
        )

        if resultado.get("exito") and resultado.get("documentos"):
            docs = resultado["documentos"]
            endpoint_scores = {}
            for doc in docs:
                ep = doc.get("endpoint", "")
                score = doc.get("score", 0)
                if ep:
                    endpoint_scores[ep] = endpoint_scores.get(ep, 0) + score

            if endpoint_scores:
                mejor_endpoint = max(endpoint_scores.items(), key=lambda x: x[1])[0]
                confianza = min(endpoint_scores[mejor_endpoint] / len(docs), 1.0)
                logging.info(f"Endpoint sugerido por memoria vectorial: {mejor_endpoint} (confianza: {confianza:.2f})")

                if "introspection" in mejor_endpoint or "historial" in mejor_endpoint:
                    return {"tipo": "introspection", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                if "diagnostico" in mejor_endpoint or "recursos" in mejor_endpoint:
                    return {"tipo": "diagnostico", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                if "ejecutar" in mejor_endpoint or "cli" in mejor_endpoint:
                    return {"tipo": "comando_local", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                if "buscar" in mejor_endpoint or "memoria" in mejor_endpoint:
                    return {"tipo": "busqueda_informacion", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}
                return {"tipo": "general", "confianza": confianza, "endpoint_sugerido": mejor_endpoint}

    except Exception as exc:
        logging.warning(f"Busqueda vectorial fallo, usando analisis estructural: {exc}")

    return analizar_estructura_consulta(consulta)


def analizar_estructura_consulta(consulta: str) -> Dict:
    """Analisis estructural de la consulta sin palabras clave predefinidas."""
    consulta_lower = consulta.lower()

    if any(p in consulta_lower for p in ["estabamos", "trabajando", "quedamos", "ultima", "anterior", "historial"]):
        return {"tipo": "introspection", "confianza": 0.8, "endpoint_sugerido": "/api/historial-interacciones"}

    if any(p in consulta_lower for p in ["estado", "recursos", "diagnostico", "status", "health"]):
        return {"tipo": "diagnostico", "confianza": 0.7, "endpoint_sugerido": "/api/diagnostico-recursos"}

    if any(consulta_lower.startswith(v) for v in ["ejecuta", "corre", "instala", "crea", "az ", "python "]):
        return {"tipo": "comando_local", "confianza": 0.9, "endpoint_sugerido": "/api/ejecutar-cli"}

    if any(p in consulta_lower for p in ["busca", "encuentra", "muestra", "lista"]):
        return {"tipo": "busqueda_informacion", "confianza": 0.6, "endpoint_sugerido": "/api/buscar-memoria"}

    return {"tipo": "general", "confianza": 0.5}


def detectar_info_externa_requerida(consulta: str, contexto: Optional[Dict]) -> Dict:
    """Detecta si la consulta requiere informacion externa."""
    consulta_lower = consulta.lower()

    if any(term in consulta_lower for term in ["ultima version", "mas reciente", "latest", "newest"]):
        return {"requiere": True, "peso": 0.9, "razon": "Version mas reciente", "categoria": "version_actual"}

    if any(term in consulta_lower for term in ["documentacion oficial", "microsoft docs", "official docs"]):
        return {"requiere": True, "peso": 0.8, "razon": "Documentacion oficial", "categoria": "documentacion"}

    if any(term in consulta_lower for term in ["problemas conocidos", "errores comunes", "github issues"]):
        return {"requiere": True, "peso": 0.9, "razon": "Problemas reportados", "categoria": "problemas"}

    if any(term in consulta_lower for term in ["mi archivo", "local", "readme", "function_app"]):
        return {"requiere": False, "peso": -0.8, "razon": "Recurso local", "categoria": "local"}

    return {"requiere": False, "peso": 0, "razon": "Sin indicadores externos", "categoria": "neutral"}


def evaluar_necesidad_actualidad(consulta: str) -> Dict:
    """Evalua si la consulta requiere informacion actualizada."""
    consulta_lower = consulta.lower()
    tech_dinamicas = ["azure functions", "openai", "chatgpt", "kubernetes", "docker", "terraform"]

    if any(tech in consulta_lower for tech in tech_dinamicas):
        return {"necesario": True, "razon": "Tecnologia de rapida evolucion"}

    if any(term in consulta_lower for term in ["2024", "actual", "ahora", "hoy", "current", "now"]):
        return {"necesario": True, "razon": "Referencia temporal especifica"}

    return {"necesario": False, "razon": "Sin necesidad de actualidad"}


def calcular_ambiguedad(consulta: str, contexto: Optional[Dict[str, Any]] = None, parsed: Optional[Dict[str, Any]] = None) -> float:
    """Calcula el nivel de ambiguedad de la consulta."""
    contexto = contexto or {}
    palabras_vagas = ["algo", "cosa", "esto", "eso", "something", "thing", "this", "that"]
    pronombres = ["el", "ella", "eso", "esto", "it", "this", "that"]

    score_ambiguedad = 0.0
    palabras = (consulta or "").lower().split()

    if len(palabras) < 3:
        score_ambiguedad += 0.4

    for palabra in palabras_vagas:
        if palabra in consulta.lower():
            score_ambiguedad += 0.25

    for pronombre in pronombres:
        if pronombre in consulta.lower():
            score_ambiguedad += 0.15

    if parsed and parsed.get("requires_grounding"):
        score_ambiguedad += 0.15

    if contexto.get("previous_intent") and any(p in consulta.lower() for p in pronombres):
        score_ambiguedad = max(score_ambiguedad - 0.1, 0)  # el contexto reduce un poco la ambiguedad

    return min(score_ambiguedad, 1.0)


def optimizar_query_inteligente(consulta: str, intencion: Dict, parsed: Optional[Dict[str, Any]] = None, contexto: Optional[Dict[str, Any]] = None) -> str:
    """Optimiza la consulta basada en la intencion detectada y el parser semantico."""
    query_optimizada = consulta
    contexto = contexto or {}
    parsed = parsed or {}

    if intencion.get("tipo") == "busqueda_informacion" or parsed.get("requires_grounding"):
        if "azure" not in consulta.lower():
            query_optimizada = f"Azure {consulta}"
        query_optimizada += " official documentation 2024"

    elif intencion.get("tipo") == "comparacion":
        query_optimizada += " comparison pros cons 2024"

    if contexto.get("tema_reciente"):
        query_optimizada += f" related to {contexto.get('tema_reciente')}"

    return query_optimizada


def detectar_necesidad_bing_inteligente(consulta: str, contexto: Optional[Dict] = None) -> Dict:
    """
    Detecta automaticamente si una consulta requiere Bing Grounding usando analisis de intencion inteligente.
    """
    ctx = _construir_contexto_base(contexto)
    texto_preparado = preprocess_text(consulta or "")

    analisis_archivo = _evaluar_busqueda_y_lectura(consulta or "")
    if analisis_archivo["score"] >= 0.75:
        return {
            "requiere_bing": False,
            "confianza": analisis_archivo["score"],
            "razon": "Lectura de archivo local detectada",
            "categoria": "leer_archivo",
            "query_optimizada": consulta,
            "score_calculado": -0.5,
            "intencion_detectada": {
                "tipo": "leer_archivo",
                "detalles": analisis_archivo,
            },
            "timestamp": datetime.now().isoformat(),
            "texto_preprocesado": texto_preparado,
        }

    clasificacion = classify_user_intent(consulta)
    clasificacion = enhance_with_context(dict(clasificacion), {"previous_intent": ctx["previous_intent"]})
    parsed = parse_natural_language(consulta)

    intencion_principal = analizar_intencion_semantica(consulta, contexto)
    info_externa = detectar_info_externa_requerida(consulta, contexto)
    actualidad = evaluar_necesidad_actualidad(consulta)
    nivel_ambiguedad = calcular_ambiguedad(consulta, contexto, parsed)

    score_bing = 0.0
    razones: List[str] = []
    categoria = "general"

    if should_use_grounding(clasificacion):
        score_bing += 0.35
        razones.append("Clasificacion semantica sugiere grounding")
    else:
        razones.append("Confianza suficiente en clasificador semantico")

    if parsed.get("requires_grounding"):
        score_bing += 0.35
        razones.append("Parser semantico requiere grounding")
    elif parsed.get("command"):
        score_bing -= 0.3
        razones.append("Parser genero comando local")
        categoria = "comando_local"

    if info_externa["requiere"]:
        score_bing += min(0.5, info_externa["peso"])
        razones.append(info_externa["razon"])
        categoria = info_externa["categoria"]

    if actualidad["necesario"]:
        score_bing += 0.3
        razones.append(actualidad["razon"])
        categoria = "informacion_dinamica"

    if nivel_ambiguedad > 0.65:
        score_bing += 0.25
        razones.append("Consulta ambigua, conviene grounding")

    if intencion_principal.get("tipo") == "revisar_logs":
        score_bing -= 0.6
        razones.append("Consulta de logs se resuelve en Log Analytics interno")
        categoria = "logs"
    elif intencion_principal.get("tipo") in {"comando_local", "diagnostico"}:
        score_bing -= 0.4
        razones.append("Accion ejecutable sin informacion externa")
        categoria = intencion_principal.get("tipo")
    elif intencion_principal.get("tipo") == "busqueda_informacion":
        score_bing += 0.4
        categoria = "busqueda_informacion"

    score_bing = max(min(score_bing, 1.0), -1.0)
    requiere_bing = score_bing > 0.4
    confianza = min(abs(score_bing), 1.0)

    query_optimizada = optimizar_query_inteligente(
        consulta, intencion_principal, parsed, ctx
    ) if requiere_bing else consulta

    return {
        "requiere_bing": requiere_bing,
        "confianza": confianza,
        "razon": "; ".join(razones) if razones else "Analisis de intencion",
        "categoria": categoria,
        "query_optimizada": query_optimizada,
        "score_calculado": score_bing,
        "intencion_detectada": intencion_principal,
        "clasificacion_semantica": clasificacion,
        "parser_semantico": parsed,
        "texto_preprocesado": texto_preparado,
        "ambiguedad": nivel_ambiguedad,
        "timestamp": datetime.now().isoformat(),
    }


def integrar_con_validador_semantico_inteligente(req, consulta: str, memoria_previa: Optional[Dict] = None) -> Dict:
    """
    Integra la deteccion inteligente de Bing con el validador semantico.
    """
    from memory_precheck import consultar_memoria_antes_responder

    deteccion = detectar_necesidad_bing_inteligente(consulta, {"memoria_previa": memoria_previa, "endpoint": getattr(req, "url", "/api/copiloto")})

    logging.info(f"[INTELIGENTE] Deteccion Bing: {deteccion['requiere_bing']} (confianza: {deteccion['confianza']:.2f}) - {deteccion['razon']}")

    if deteccion["intencion_detectada"].get("endpoint_sugerido"):
        logging.info(f"[INTELIGENTE] Endpoint sugerido: {deteccion['intencion_detectada']['endpoint_sugerido']}")

    if not deteccion["requiere_bing"]:
        return {
            "usar_bing": False,
            "continuar_normal": True,
            "deteccion": deteccion,
        }

    try:
        from bing_fallback_guard import ejecutar_grounding_fallback

        resultado_bing = ejecutar_grounding_fallback(
            deteccion["query_optimizada"],
            deteccion["categoria"],
            {
                "consulta_original": consulta,
                "confianza_deteccion": deteccion["confianza"],
                "razon": deteccion["razon"],
                "intencion": deteccion["intencion_detectada"],
            },
        )

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
                    "analisis_intencion": deteccion["intencion_detectada"],
                },
            }

    except Exception as exc:
        logging.error(f"Error ejecutando Bing inteligente: {exc}")

    return {
        "usar_bing": True,
        "continuar_normal": True,
        "bing_fallido": True,
        "deteccion": deteccion,
    }
