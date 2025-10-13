"""
Detector inteligente de intención para Bing Grounding
Integrado con el validador semántico para detección automática
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def detectar_necesidad_bing_grounding(consulta: str, contexto: Optional[Dict] = None) -> Dict:
    """
    Detecta automáticamente si una consulta requiere Bing Grounding
    
    Returns:
        {
            "requiere_bing": bool,
            "confianza": float,
            "razon": str,
            "categoria": str,
            "query_optimizada": str
        }
    """
    consulta_lower = consulta.lower().strip()
    
    # === PATRONES QUE REQUIEREN BING GROUNDING ===
    
    # 1. Información dinámica/versiones
    patrones_dinamicos = [
        r"versión más reciente|última versión|newest version",
        r"qué hay de nuevo|what's new|novedades",
        r"cambios recientes|recent changes|updates",
        r"roadmap|hoja de ruta|futuro de",
        r"cuando sale|when will|fecha de lanzamiento"
    ]
    
    # 2. Documentación oficial específica
    patrones_documentacion = [
        r"documentación oficial|official docs|microsoft docs",
        r"qué dice la documentación|according to docs",
        r"en la documentación de|docs for",
        r"guía oficial|official guide"
    ]
    
    # 3. Problemas/errores reportados
    patrones_problemas = [
        r"errores comunes|common errors|known issues",
        r"problemas reportados|reported issues|bug reports",
        r"github issues|stackoverflow|community problems",
        r"troubleshooting|solución de problemas"
    ]
    
    # 4. Comparaciones/alternativas
    patrones_comparacion = [
        r"vs\s+|versus|comparado con|compared to",
        r"alternativas a|alternatives to|mejor que",
        r"diferencias entre|differences between"
    ]
    
    # 5. Tecnologías específicas que pueden estar desactualizadas
    tecnologias_dinamicas = [
        "deepspeed", "chatgpt", "openai", "azure openai", "cognitive services",
        "kubernetes", "docker", "terraform", "bicep", "arm templates",
        "github actions", "devops", "azure functions v4", "python 3.12"
    ]
    
    # === PATRONES QUE NO REQUIEREN BING GROUNDING ===
    
    # 1. Comandos básicos conocidos
    patrones_basicos = [
        r"cómo usar sed|how to use sed|sed command",
        r"ejemplo de|example of|dame un ejemplo",
        r"explica|explain|qué es|what is",
        r"script para|script to|crear script"
    ]
    
    # 2. Archivos locales
    patrones_locales = [
        r"mi archivo|my file|archivo local|local file",
        r"readme\.md|function_app\.py|requirements\.txt",
        r"en mi proyecto|in my project|mi código|my code"
    ]
    
    # === LÓGICA DE DETECCIÓN ===
    
    score_bing = 0
    razones = []
    categoria = "general"
    
    # Verificar patrones que requieren Bing
    for patron in patrones_dinamicos:
        if re.search(patron, consulta_lower):
            score_bing += 0.8
            razones.append("Información dinámica/versiones")
            categoria = "informacion_dinamica"
    
    for patron in patrones_documentacion:
        if re.search(patron, consulta_lower):
            score_bing += 0.7
            razones.append("Documentación oficial específica")
            categoria = "documentacion_oficial"
    
    for patron in patrones_problemas:
        if re.search(patron, consulta_lower):
            score_bing += 0.9
            razones.append("Problemas/errores reportados")
            categoria = "problemas_reportados"
    
    for patron in patrones_comparacion:
        if re.search(patron, consulta_lower):
            score_bing += 0.6
            razones.append("Comparaciones/alternativas")
            categoria = "comparacion"
    
    # Verificar tecnologías dinámicas
    for tech in tecnologias_dinamicas:
        if tech in consulta_lower:
            score_bing += 0.5
            razones.append(f"Tecnología dinámica: {tech}")
            categoria = "tecnologia_dinamica"
    
    # Verificar patrones que NO requieren Bing
    for patron in patrones_basicos:
        if re.search(patron, consulta_lower):
            score_bing -= 0.6
            razones.append("Comando básico conocido")
    
    for patron in patrones_locales:
        if re.search(patron, consulta_lower):
            score_bing -= 0.8
            razones.append("Archivo/recurso local")
    
    # === DECISIÓN FINAL ===
    
    requiere_bing = score_bing > 0.3
    confianza = min(abs(score_bing), 1.0)
    
    # Optimizar query para Bing si es necesario
    query_optimizada = optimizar_query_para_bing(consulta) if requiere_bing else consulta
    
    return {
        "requiere_bing": requiere_bing,
        "confianza": confianza,
        "razon": "; ".join(razones) if razones else "Análisis heurístico",
        "categoria": categoria,
        "query_optimizada": query_optimizada,
        "score_calculado": score_bing,
        "timestamp": datetime.now().isoformat()
    }


def optimizar_query_para_bing(consulta: str) -> str:
    """Optimiza la consulta para mejores resultados en Bing"""
    
    # Agregar contexto Azure si no está presente
    if "azure" not in consulta.lower() and any(term in consulta.lower() for term in ["bicep", "arm", "functions", "storage", "cosmos"]):
        consulta = f"Azure {consulta}"
    
    # Agregar "official documentation" para consultas de docs
    if any(term in consulta.lower() for term in ["documentación", "docs", "guía"]):
        consulta += " official documentation Microsoft"
    
    # Agregar año actual para versiones
    if any(term in consulta.lower() for term in ["versión", "version", "latest", "newest"]):
        consulta += " 2024"
    
    return consulta


def integrar_con_validador_semantico(req, consulta: str, memoria_previa: Optional[Dict] = None) -> Dict:
    """
    Integra la detección de Bing con el validador semántico existente
    
    Returns:
        {
            "usar_bing": bool,
            "resultado_bing": dict,  # Si se ejecutó Bing
            "continuar_normal": bool,  # Si debe continuar con flujo normal
            "respuesta_final": dict  # Si ya tiene respuesta completa
        }
    """
    from memory_precheck import consultar_memoria_antes_responder
    
    # 1. Detectar necesidad de Bing
    deteccion = detectar_necesidad_bing_grounding(consulta, {
        "memoria_previa": memoria_previa,
        "endpoint": getattr(req, 'url', '/api/copiloto')
    })
    
    logging.info(f"🧠 Detección Bing: {deteccion['requiere_bing']} (confianza: {deteccion['confianza']:.2f}) - {deteccion['razon']}")
    
    # 2. Si no requiere Bing, continuar normal
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
                "razon": deteccion["razon"]
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
                    "fuente": "bing_grounding_automatico",
                    "deteccion_automatica": deteccion,
                    "comando_sugerido": resultado_bing.get("comando_sugerido"),
                    "fuentes": resultado_bing.get("fuentes", []),
                    "confianza": resultado_bing.get("confianza", 0.8)
                }
            }
    
    except Exception as e:
        logging.error(f"Error ejecutando Bing automático: {e}")
    
    # 5. Si Bing falló, continuar con flujo normal pero marcar que se intentó
    return {
        "usar_bing": True,
        "continuar_normal": True,
        "bing_fallido": True,
        "deteccion": deteccion
    }


# === FUNCIONES DE UTILIDAD ===

def generar_sugerencias_por_categoria(categoria: str) -> List[str]:
    """Genera sugerencias específicas por categoría"""
    
    sugerencias_map = {
        "informacion_dinamica": [
            "Consulta la documentación oficial de Microsoft",
            "Revisa el changelog o release notes",
            "Verifica en GitHub releases"
        ],
        "documentacion_oficial": [
            "Visita docs.microsoft.com",
            "Usa el comando --help para información local",
            "Consulta Azure CLI reference"
        ],
        "problemas_reportados": [
            "Revisa GitHub Issues del proyecto",
            "Consulta Stack Overflow",
            "Verifica Azure Status page"
        ],
        "tecnologia_dinamica": [
            "Consulta la documentación más reciente",
            "Verifica compatibilidad de versiones",
            "Revisa breaking changes"
        ]
    }
    
    return sugerencias_map.get(categoria, [
        "Sé más específico en tu consulta",
        "Incluye versiones o contexto adicional",
        "Consulta fuentes oficiales"
    ])