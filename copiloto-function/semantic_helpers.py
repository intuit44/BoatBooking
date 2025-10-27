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

def generar_resumen_conversacion(interacciones: list) -> str:
    """Genera resumen dinámico usando el ecosistema semántico existente"""
    if not interacciones:
        return "Nueva sesión iniciada sin contexto previo"
    
    # Usar clasificador semántico existente para análisis dinámico
    try:
        from semantic_classifier import get_intelligent_context
        contexto = get_intelligent_context(interacciones)
        
        # Usar intent classifier para detectar patrones
        from semantic_intent_classifier import classify_user_intent
        
        # Analizar última interacción para contexto
        ultima_interaccion = interacciones[0] if interacciones else {}
        texto_ultima = ultima_interaccion.get('texto_semantico', '')
        
        if texto_ultima:
            intent_analysis = classify_user_intent(texto_ultima)
            patron_detectado = intent_analysis.get('intent', 'general')
            confianza = intent_analysis.get('confidence', 0.5)
        else:
            patron_detectado = 'general'
            confianza = 0.5
        
        # Generar resumen dinámico basado en análisis real
        total = len(interacciones)
        modo = contexto.get('mode', 'continuation')
        resumen_inteligente = contexto.get('summary', f'Análisis de {total} interacciones')
        
        # Determinar estado del sistema dinámicamente
        exitosas = sum(1 for i in interacciones if i.get('exito', True))
        tasa_exito = exitosas / total if total > 0 else 0
        
        if tasa_exito > 0.9:
            estado_sistema = "Sistema funcionando óptimamente"
        elif tasa_exito > 0.7:
            estado_sistema = "Sistema estable con algunas incidencias"
        else:
            estado_sistema = "Sistema requiere atención"
        
        # Construir resumen semántico dinámico
        resumen = f"**Análisis Semántico Dinámico:**\n\n"
        resumen += f"• **Contexto**: {resumen_inteligente}\n"
        resumen += f"• **Modo de Operación**: {modo}\n"
        resumen += f"• **Patrón Detectado**: {patron_detectado} (confianza: {int(confianza*100)}%)\n"
        resumen += f"• **Estado del Sistema**: {estado_sistema}\n"
        resumen += f"• **Memoria Activa**: {total} interacciones analizadas\n\n"
        
        # Añadir insights específicos basados en el modo
        if modo == 'error_correction':
            resumen += "🔧 **Contexto de Corrección**: El sistema está en modo de resolución de problemas.\n"
        elif modo == 'execution':
            resumen += "⚡ **Contexto de Ejecución**: Sesión enfocada en comandos y operaciones.\n"
        elif modo == 'information_retrieval':
            resumen += "🔍 **Contexto de Consulta**: Sesión orientada a búsqueda de información.\n"
        
        return resumen
        
    except ImportError:
        # Fallback simple si no están disponibles los módulos
        total = len(interacciones)
        exitosas = sum(1 for i in interacciones if i.get('exito', True))
        tasa = int((exitosas / total * 100)) if total > 0 else 0
        
        return f"Sesión activa: {total} interacciones, {tasa}% éxito. Sistema {'estable' if tasa > 80 else 'requiere atención'}."