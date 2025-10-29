"""
Filtro Inteligente de Interacciones
Elimina redundancia y extrae solo información útil
"""

def filtrar_interacciones_inteligente(interacciones: list) -> dict:
    """
    Filtra interacciones redundantes y extrae resumen útil
    
    Returns:
        dict con interacciones_filtradas y resumen_semantico
    """
    if not interacciones:
        return {"interacciones_filtradas": [], "resumen_semantico": "Sin actividad previa"}
    
    # Filtrar interacciones de historial recursivas
    interacciones_utiles = []
    endpoints_vistos = {}
    
    for inter in interacciones:
        endpoint = inter.get("endpoint", "")
        texto = inter.get("texto_semantico", "")
        
        # Saltar consultas de historial recursivas
        if "historial" in endpoint.lower() and "CONSULTA DE HISTORIAL" in texto:
            continue
        
        # Saltar duplicados del mismo endpoint en corto tiempo
        key = f"{endpoint}_{inter.get('timestamp', '')[:16]}"  # Agrupar por minuto
        if key in endpoints_vistos:
            continue
        
        endpoints_vistos[key] = True
        interacciones_utiles.append(inter)
    
    # Generar resumen semántico
    if not interacciones_utiles:
        return {
            "interacciones_filtradas": [],
            "resumen_semantico": "Solo consultas de historial sin actividad real"
        }
    
    # Extraer acciones reales
    acciones = []
    for inter in interacciones_utiles[-10:]:  # Últimas 10 útiles
        endpoint = inter.get("endpoint", "unknown")
        if endpoint not in ["historial-interacciones", "health", "status"]:
            acciones.append(endpoint.replace("/api/", "").replace("-", " "))
    
    if acciones:
        resumen = f"Actividad reciente: {', '.join(set(acciones[:5]))}"
    else:
        resumen = "Interacciones de sistema sin acciones de usuario"
    
    return {
        "interacciones_filtradas": interacciones_utiles[-20:],  # Últimas 20 útiles
        "resumen_semantico": resumen,
        "total_original": len(interacciones),
        "total_filtrado": len(interacciones_utiles),
        "redundancia_eliminada": len(interacciones) - len(interacciones_utiles)
    }
