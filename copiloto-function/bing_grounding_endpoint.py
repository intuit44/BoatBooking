import os
import json
import logging
import requests
from datetime import datetime
import azure.functions as func


app = func.FunctionApp()

@app.function_name(name="bing_grounding_http")
@app.route(route="bing-grounding", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def bing_grounding_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint de búsqueda inteligente que actúa como fuente de conocimiento externo
    Se activa automáticamente cuando el sistema interno no puede resolver algo
    """
    try:
        body = req.get_json()
        if not body:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Request body requerido"}),
                mimetype="application/json", status_code=400
            )
        
        query = body.get("query", "").strip()
        contexto = body.get("contexto", "")
        intencion_original = body.get("intencion_original", "")
        prioridad = body.get("prioridad", "normal")
        
        if not query:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'query' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        # Realizar búsqueda en Bing
        resultado_bing = _buscar_en_bing(query, contexto)
        
        if resultado_bing.get("exito"):
            # Procesar y estructurar respuesta
            respuesta = {
                "exito": True,
                "resultado": {
                    "resumen": resultado_bing.get("resumen", ""),
                    "fuentes": resultado_bing.get("fuentes", []),
                    "tipo": "snippet",
                    "comando_sugerido": _extraer_comando_de_respuesta(resultado_bing.get("resumen", ""))
                },
                "accion_sugerida": "Reintentar con comando sugerido",
                "reutilizable": True,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "contexto": contexto,
                    "intencion_original": intencion_original,
                    "prioridad": prioridad,
                    "trigger": "sistema_interno_insuficiente"
                }
            }
            
            # Registrar aprendizaje
            _registrar_aprendizaje_externo(query, resultado_bing, contexto)
            
            return func.HttpResponse(
                json.dumps(respuesta, ensure_ascii=False),
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "No se pudo obtener información de Bing",
                    "detalles": resultado_bing.get("error", "")
                }),
                mimetype="application/json", status_code=500
            )
            
    except Exception as e:
        logging.error(f"Error en bing-grounding: {str(e)}")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )

def _buscar_en_bing(query: str, contexto: str) -> dict:
    """Realiza búsqueda en Bing Search API"""
    try:
        bing_key = os.environ.get("BING_SEARCH_KEY")
        if not bing_key:
            return {"exito": False, "error": "BING_SEARCH_KEY no configurado"}
        
        # Mejorar query según contexto
        query_mejorada = _mejorar_query_segun_contexto(query, contexto)
        
        headers = {"Ocp-Apim-Subscription-Key": bing_key}
        params = {
            "q": query_mejorada,
            "count": 5,
            "offset": 0,
            "mkt": "es-ES",
            "safesearch": "Moderate"
        }
        
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            web_pages = data.get("webPages", {}).get("value", [])
            
            # Extraer información relevante
            resumen = _generar_resumen_de_resultados(web_pages, contexto)
            fuentes = [{"titulo": p.get("name", ""), "url": p.get("url", "")} for p in web_pages[:3]]
            
            return {
                "exito": True,
                "resumen": resumen,
                "fuentes": fuentes,
                "resultados_raw": web_pages
            }
        else:
            return {"exito": False, "error": f"Bing API error: {response.status_code}"}
            
    except Exception as e:
        return {"exito": False, "error": str(e)}

def _mejorar_query_segun_contexto(query: str, contexto: str) -> str:
    """Mejora la query según el contexto del error"""
    mejoras = {
        "comando fallido en ejecutar-cli": f"Azure CLI {query} example command",
        "herramienta desconocida": f"how to use {query} Azure",
        "parametro ambiguo": f"{query} Azure CLI parameters examples",
        "api error": f"fix {query} Azure API error",
        "script optimization": f"optimize {query} Azure script best practices"
    }
    
    return mejoras.get(contexto, f"Azure {query} documentation example")

def _generar_resumen_de_resultados(resultados: list, contexto: str) -> str:
    """Genera resumen inteligente de los resultados de Bing"""
    if not resultados:
        return "No se encontraron resultados relevantes"
    
    # Extraer snippets más relevantes
    snippets = []
    for resultado in resultados[:3]:
        snippet = resultado.get("snippet", "")
        if snippet and len(snippet) > 20:
            snippets.append(snippet)
    
    # Generar resumen contextual
    if "comando" in contexto.lower():
        return f"Para resolver el comando: {' '.join(snippets[:2])}"
    elif "error" in contexto.lower():
        return f"Solución al error: {snippets[0] if snippets else 'Verificar documentación oficial'}"
    else:
        return snippets[0] if snippets else "Consultar documentación de Azure"

def _extraer_comando_de_respuesta(resumen: str) -> str:
    """Extrae comando sugerido del resumen"""
    import re
    
    # Buscar patrones de comandos Azure CLI
    patrones = [
        r'`(az [^`]+)`',
        r'az [a-z-]+ [a-z-]+ [^\n\r.]+',
        r'--[a-z-]+ [^\s]+'
    ]
    
    for patron in patrones:
        match = re.search(patron, resumen)
        if match:
            return match.group(1) if '`' in patron else match.group(0)
    
    return ""

def _registrar_aprendizaje_externo(query: str, resultado: dict, contexto: str):
    """Registra el aprendizaje externo en memoria semántica"""
    try:
        evento = {
            "tipo": "aprendizaje_externo",
            "fuente": "bing",
            "query": query,
            "contexto": contexto,
            "resultado_exitoso": resultado.get("exito", False),
            "resumen": resultado.get("resumen", ""),
            "timestamp": datetime.now().isoformat(),
            "trigger": "sistema_interno_insuficiente"
        }
        
        # Intentar guardar en Cosmos si está disponible
        try:
            from services.cosmos_store import CosmosMemoryStore
            cosmos = CosmosMemoryStore()
            if cosmos.enabled:
                cosmos.upsert({
                    "id": f"bing_learning_{int(datetime.now().timestamp())}",
                    "session_id": "bing_grounding",
                    "event_data": evento,
                    "timestamp": evento["timestamp"]
                })
        except Exception:
            pass  # Fallar silenciosamente si Cosmos no está disponible
            
        logging.info(f"Aprendizaje registrado: {query} -> {resultado.get('exito', False)}")
        
    except Exception as e:
        logging.warning(f"Error registrando aprendizaje: {e}")