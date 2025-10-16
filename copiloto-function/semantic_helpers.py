# -*- coding: utf-8 -*-
"""
Funciones auxiliares para memoria semántica
"""

def generar_sugerencias_contextuales(contexto_semantico: dict) -> list:
    """Genera sugerencias basadas en contexto semántico"""
    sugerencias = []
    
    if not contexto_semantico:
        return ["diagnosticar:sistema", "verificar:almacenamiento"]
    
    # Basado en estado del sistema
    estado = contexto_semantico.get("estado_sistema", {})
    if estado.get("monitoreo_activo"):
        sugerencias.append("revisar:metricas_monitoreo")
    if estado.get("errores_recientes"):
        sugerencias.append("analizar:errores_recientes")
    
    # Basado en conocimiento cognitivo
    conocimiento = contexto_semantico.get("conocimiento_cognitivo", {})
    if conocimiento.get("recomendaciones"):
        sugerencias.extend(conocimiento["recomendaciones"][:2])
    
    # Sugerencias por defecto
    if not sugerencias:
        sugerencias = ["dashboard", "diagnosticar:completo", "verificar:almacenamiento"]
    
    return sugerencias[:5]

def interpretar_con_contexto_semantico(mensaje: str, contexto_semantico: dict) -> dict:
    """Interpreta mensaje usando contexto semántico"""
    interpretacion = {
        "interpretacion": f"Basándome en el contexto: {mensaje}",
        "sugerencias": []
    }
    
    # Si hay errores recientes, sugerir diagnóstico
    estado = contexto_semantico.get("estado_sistema", {})
    if estado.get("errores_recientes"):
        interpretacion["sugerencias"].append("diagnosticar:errores")
    
    # Si hay conocimiento cognitivo, usar recomendaciones
    conocimiento = contexto_semantico.get("conocimiento_cognitivo", {})
    if conocimiento.get("recomendaciones"):
        interpretacion["sugerencias"].extend(conocimiento["recomendaciones"][:2])
    
    # Sugerencias por defecto
    if not interpretacion["sugerencias"]:
        interpretacion["sugerencias"] = [
            "buscar:" + mensaje,
            "generar:script para " + mensaje,
            "sugerir"
        ]
    
    return interpretacion