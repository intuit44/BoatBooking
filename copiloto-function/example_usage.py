#!/usr/bin/env python3
"""
Ejemplo de cómo usar el memory service en los endpoints
"""

# Ejemplo de uso en autocorregir_http o cualquier endpoint:

def autocorregir_http(req):
    """Ejemplo de endpoint usando memory service"""
    try:
        # Tu lógica existente aquí...
        data = req.get_json()
        run_id = f"run_{int(time.time())}"
        
        # En lugar de _log_semantic_event, usar memory service
        if memory_service:
            memory_service.log_event("alerta", {
                "tipo": "alerta",
                "alerta": data.get("alertRule"),
                "timestamp": datetime.utcnow().isoformat(),
                "run_id": run_id
            }, session_id=run_id)
            
            # También guardar en Cosmos DB si está disponible
            if memory_service.cosmos_store.enabled:
                memory_service.cosmos_store.upsert({
                    "session_id": run_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "alerta": data.get("alertRule"),
                    "severity": data.get("severity"),
                    "estado": data.get("monitorCondition"),
                    "contenido": json.dumps(data)
                })
        
        # Tu respuesta normal
        return func.HttpResponse(json.dumps({"ok": True}))
        
    except Exception as e:
        # Log del error también
        if memory_service:
            memory_service.log_event("error", {
                "error": str(e),
                "endpoint": "autocorregir_http",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)

# Ejemplo de uso en cualquier función que necesite logging:

def ejemplo_funcion_con_logging():
    """Ejemplo de función que usa memory service para logging"""
    
    # Log de inicio de operación
    if memory_service:
        memory_service.log_event("operacion_inicio", {
            "funcion": "ejemplo_funcion_con_logging",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    try:
        # Tu lógica aquí...
        resultado = {"exito": True, "datos": "algunos datos"}
        
        # Log de éxito
        if memory_service:
            memory_service.log_event("operacion_exitosa", {
                "funcion": "ejemplo_funcion_con_logging",
                "resultado": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return resultado
        
    except Exception as e:
        # Log de error
        if memory_service:
            memory_service.log_event("operacion_error", {
                "funcion": "ejemplo_funcion_con_logging",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        raise

# Ejemplo de uso para guardar fixes pendientes:

def guardar_fix_pendiente(issue_data):
    """Ejemplo de cómo guardar un fix pendiente"""
    if memory_service:
        return memory_service.save_pending_fix({
            "issue": issue_data.get("issue"),
            "solution": issue_data.get("solution"),
            "priority": issue_data.get("priority", "medium"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        })
    return False

# Ejemplo de consulta de historial:

def obtener_historial_sesion(session_id):
    """Ejemplo de cómo obtener historial de una sesión"""
    if memory_service and memory_service.cosmos_store.enabled:
        return memory_service.get_session_history(session_id, limit=50)
    return []