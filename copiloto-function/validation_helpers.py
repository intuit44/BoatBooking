def validate_json_input(req):
    """Valida entrada JSON y devuelve error 400 si es inválida"""
    try:
        body = req.get_json()
        if body is None:
            return None, {"error": "Request body must be valid JSON", "status": 400}
        return body, None
    except ValueError as e:
        return None, {"error": "Invalid JSON format", "details": str(e), "status": 400}

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