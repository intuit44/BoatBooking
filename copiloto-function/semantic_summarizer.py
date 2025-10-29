"""
Generador de resúmenes semánticos inteligentes
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

def generar_resumen_semantico_inteligente(interacciones: List[Dict], contexto_inteligente: Dict, interpretacion_semantica: str) -> str:
    """Genera un resumen natural y dinámico de las interacciones recientes"""
    
    if not interacciones:
        return "No hay actividad previa registrada en esta sesión."
    
    # Extraer interacciones significativas (escanear hasta 100)
    interacciones_relevantes = []
    for inter in interacciones[:100]:
        texto = inter.get("texto_semantico", "")
        consulta = inter.get("data", {}).get("params", {}).get("consulta", "") if isinstance(inter.get("data"), dict) else ""
        endpoint = inter.get("endpoint", "")
        timestamp = inter.get("timestamp", "")
        
        # Filtrar interacciones vacías o de historial
        if consulta and consulta != "sin_comando" and "historial" not in endpoint:
            interacciones_relevantes.append({
                "consulta": consulta,
                "endpoint": endpoint,
                "timestamp": timestamp,
                "texto": texto[:200]
            })
    
    if not interacciones_relevantes:
        # Buscar en texto_semantico con patrones más amplios (escanear TODO el historial)
        for inter in interacciones:
            texto = inter.get("texto_semantico", "")
            if not texto or len(texto) < 20:
                continue
            
            # Patrones de actividad significativa
            patrones = [
                ("Verificación", "verificando"),
                ("Diagnóstico", "diagnosticando"),
                ("Ejecutando", "ejecutando"),
                ("Creando", "creando"),
                ("Configurando", "configurando"),
                ("Analizando", "analizando"),
                ("DIAGNOSTICO DE RECURSO", "diagnosticando recurso"),
                ("verifica estado", "verificando estado")
            ]
            
            for patron, verbo in patrones:
                if patron in texto or patron.lower() in texto.lower():
                    # Extraer contexto
                    if "Cosmos" in texto or "cosmos" in texto:
                        return f"🧠 Estábamos {verbo} Cosmos DB."
                    elif "recurso" in texto.lower():
                        # Buscar nombre del recurso
                        import re
                        match = re.search(r"recurso ['\"]([^'\"]+)['\"]", texto, re.IGNORECASE)
                        if match:
                            return f"🧠 Estábamos {verbo} el recurso '{match.group(1)}'."
                    
                    lineas = texto.split('\n')
                    primera_linea = lineas[0] if lineas else texto[:150]
                    contexto = primera_linea.replace(patron + " de", "").replace(patron, "").strip()
                    if len(contexto) > 10:
                        return f"🧠 Estábamos {verbo}: {contexto[:80]}."
        
        return f"Las últimas {len(interacciones)} interacciones fueron consultas de historial."
    
    # Construir respuesta natural y dinámica
    ultima = interacciones_relevantes[0]
    
    # Generar respuesta conversacional
    if "verifica" in ultima['consulta'].lower() or "estado" in ultima['consulta'].lower():
        respuesta = f"🧠 Estábamos verificando: {ultima['consulta'].replace('verifica', '').replace('estado de', '').strip()}."
    elif "diagnostica" in ultima['consulta'].lower():
        respuesta = f"🧠 Estábamos diagnosticando: {ultima['consulta'].replace('diagnostica', '').strip()}."
    else:
        respuesta = f"🧠 Última actividad: {ultima['consulta']}."
    
    # Agregar contexto temporal si hay más interacciones
    if len(interacciones_relevantes) > 1:
        respuesta += f" Antes trabajamos en: {interacciones_relevantes[1]['consulta']}."
    
    return respuesta
