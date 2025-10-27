# -*- coding: utf-8 -*-
"""
Analizador semántico dinámico - Sin predefiniciones
"""

def analizar_semanticamente(interacciones: list) -> str:
    """Genera análisis semántico dinámico basado en patrones reales"""
    if not interacciones:
        return "Nueva sesión sin contexto previo"
    
    # Análisis dinámico de patrones
    endpoints = [i.get('endpoint', '') for i in interacciones if i.get('endpoint')]
    tipos_operacion = {}
    tendencias = {}
    
    for interaccion in interacciones:
        endpoint = interaccion.get('endpoint', 'unknown')
        exito = interaccion.get('exito', True)
        
        # Clasificar dinámicamente por tipo de operación
        if 'cli' in endpoint or 'ejecutar' in endpoint:
            tipos_operacion['ejecucion'] = tipos_operacion.get('ejecucion', 0) + 1
        elif 'memoria' in endpoint or 'historial' in endpoint:
            tipos_operacion['memoria'] = tipos_operacion.get('memoria', 0) + 1
        elif 'diagnostico' in endpoint or 'verificar' in endpoint:
            tipos_operacion['diagnostico'] = tipos_operacion.get('diagnostico', 0) + 1
        else:
            tipos_operacion['otros'] = tipos_operacion.get('otros', 0) + 1
        
        # Analizar tendencias de éxito
        tendencias[endpoint] = tendencias.get(endpoint, {'total': 0, 'exitosos': 0})
        tendencias[endpoint]['total'] += 1
        if exito:
            tendencias[endpoint]['exitosos'] += 1
    
    # Generar análisis dinámico
    total = len(interacciones)
    tipo_dominante = max(tipos_operacion.items(), key=lambda x: x[1]) if tipos_operacion else ('unknown', 0)
    
    # Calcular métricas dinámicas
    tasa_exito_global = sum(1 for i in interacciones if i.get('exito', True)) / total
    
    # Generar texto semántico adaptativo
    if tipo_dominante[0] == 'ejecucion':
        contexto = f"Sesión enfocada en ejecución de comandos ({tipo_dominante[1]} operaciones)"
    elif tipo_dominante[0] == 'memoria':
        contexto = f"Sesión con alta actividad de memoria ({tipo_dominante[1]} consultas)"
    elif tipo_dominante[0] == 'diagnostico':
        contexto = f"Sesión de diagnóstico del sistema ({tipo_dominante[1]} verificaciones)"
    else:
        contexto = f"Sesión mixta con {total} interacciones variadas"
    
    # Estado dinámico basado en métricas reales
    if tasa_exito_global > 0.9:
        estado = "Sistema funcionando óptimamente"
    elif tasa_exito_global > 0.7:
        estado = "Sistema estable con algunas incidencias"
    else:
        estado = "Sistema requiere atención"
    
    return f"{contexto}. {estado}. Memoria activa con {total} interacciones."

def generar_contexto_inteligente(interacciones: list) -> dict:
    """Genera contexto inteligente sin predefiniciones"""
    if not interacciones:
        return {"modo": "nueva_sesion", "analisis": "Sin datos previos"}
    
    # Análisis temporal dinámico
    from datetime import datetime, timedelta
    ahora = datetime.now()
    recientes = []
    
    for i in interacciones:
        try:
            timestamp = datetime.fromisoformat(i.get('timestamp', '').replace('Z', '+00:00'))
            if (ahora - timestamp) < timedelta(minutes=30):
                recientes.append(i)
        except:
            continue
    
    # Determinar modo dinámicamente
    if len(recientes) > 5:
        modo = "sesion_activa"
    elif len(interacciones) > 20:
        modo = "sesion_extendida"
    else:
        modo = "sesion_normal"
    
    # Análisis de patrones sin predefinir
    patrones = {}
    for i in interacciones:
        endpoint = i.get('endpoint', 'unknown')
        patrones[endpoint] = patrones.get(endpoint, 0) + 1
    
    patron_principal = max(patrones.items(), key=lambda x: x[1])[0] if patrones else 'ninguno'
    
    return {
        "modo": modo,
        "patron_detectado": patron_principal,
        "actividad_reciente": len(recientes),
        "total_analizado": len(interacciones),
        "analisis": f"Patrón {patron_principal} detectado en modo {modo}"
    }