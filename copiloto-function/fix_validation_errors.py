#!/usr/bin/env python3
"""
Correcciones mínimas para errores de validación detectados en el reporte de pruebas
"""

# Función para validar JSON de entrada
def validate_json_input(req):
    """Valida entrada JSON y devuelve error 400 si es inválida"""
    try:
        body = req.get_json()
        if body is None:
            return None, {"error": "Request body must be valid JSON", "status": 400}
        return body, None
    except ValueError as e:
        return None, {"error": "Invalid JSON format", "details": str(e), "status": 400}

# Función para validar parámetros requeridos
def validate_required_params(body, required_fields):
    """Valida que los campos requeridos estén presentes"""
    missing = []
    for field in required_fields:
        if not body.get(field):
            missing.append(field)
    
    if missing:
        return {"error": f"Missing required parameters: {', '.join(missing)}", 
                "missing_fields": missing, "status": 400}
    return None

# Corrección para crear-contenedor
def fix_crear_contenedor_validation():
    """Corrección para el endpoint crear-contenedor"""
    return """
@app.function_name(name="crear_contenedor_http")
@app.route(route="crear-contenedor", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_contenedor_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Validar JSON
        body, error = validate_json_input(req)
        if error:
            return func.HttpResponse(json.dumps(error), mimetype="application/json", status_code=error["status"])
        
        # Validar parámetros requeridos
        error = validate_required_params(body, ["nombre"])
        if error:
            return func.HttpResponse(json.dumps(error), mimetype="application/json", status_code=error["status"])
        
        # Procesar...
        nombre = body.get("nombre", "").strip()
        if not nombre:
            return func.HttpResponse(
                json.dumps({"error": "Parameter 'nombre' cannot be empty", "status": 400}),
                mimetype="application/json", status_code=400
            )
        
        # Resto de la lógica...
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            mimetype="application/json", status_code=500
        )
"""

# Corrección para bridge-cli
def fix_bridge_cli_validation():
    """Corrección para el endpoint bridge-cli"""
    return """
@app.function_name(name="bridge_cli")
@app.route(route="bridge-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def bridge_cli(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Validar que hay contenido
        raw_body = req.get_body().decode('utf-8') if req.get_body() else ""
        
        if not raw_body or raw_body.strip() in ["{}", ""]:
            return func.HttpResponse(
                json.dumps({"error": "Request body cannot be empty", "status": 400}),
                mimetype="application/json", status_code=400
            )
        
        # Resto de la lógica...
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            mimetype="application/json", status_code=500
        )
"""

# Corrección para ejecutar-cli
def fix_ejecutar_cli_validation():
    """Corrección para el endpoint ejecutar-cli"""
    return """
@app.function_name(name="ejecutar_cli_http")
@app.route(route="ejecutar-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_cli_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Validar JSON
        body, error = validate_json_input(req)
        if error:
            return func.HttpResponse(json.dumps(error), mimetype="application/json", status_code=error["status"])
        
        # Validar comando
        comando = body.get("comando", "").strip()
        if not comando:
            return func.HttpResponse(
                json.dumps({"error": "Parameter 'comando' is required", "status": 400}),
                mimetype="application/json", status_code=400
            )
        
        # Resto de la lógica...
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            mimetype="application/json", status_code=500
        )
"""

# Corrección para leer-archivo (timeout)
def fix_leer_archivo_timeout():
    """Corrección para el endpoint leer-archivo que tiene timeouts"""
    return """
@app.function_name(name="leer_archivo_http")
@app.route(route="leer-archivo", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def leer_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Validar parámetro requerido
        ruta = req.params.get("ruta", "").strip()
        if not ruta:
            return func.HttpResponse(
                json.dumps({"error": "Parameter 'ruta' is required", "status": 400}),
                mimetype="application/json", status_code=400
            )
        
        # Timeout rápido para evitar cuelgues
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 segundos máximo
        
        try:
            # Resto de la lógica...
            pass
        finally:
            signal.alarm(0)  # Cancelar timeout
        
    except TimeoutError:
        return func.HttpResponse(
            json.dumps({"error": "Request timed out", "status": 408}),
            mimetype="application/json", status_code=408
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            mimetype="application/json", status_code=500
        )
"""

if __name__ == "__main__":
    print("🔧 Correcciones de validación generadas")
    print("📋 Problemas principales identificados:")
    print("  - Falta validación de JSON de entrada")
    print("  - Parámetros requeridos no validados")
    print("  - Errores 500 en lugar de 400 para entradas inválidas")
    print("  - Timeouts en algunos endpoints")
    print("\n✅ Aplicar estas correcciones al function_app.py")