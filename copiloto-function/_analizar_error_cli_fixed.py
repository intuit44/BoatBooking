def _analizar_error_cli(intentos_log: list, comando: str) -> dict:
    """Analiza errores de CLI para detectar parámetros faltantes"""
    for intento in intentos_log:
        stderr = intento.get("stderr", "").lower()
        
        # Patrones comunes de Azure CLI
        if "resource group" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "resourceGroup"}
        elif "location" in stderr and ("required" in stderr or "must be specified" in stderr):
            return {"tipo_error": "MissingParameter", "campo_faltante": "location"}
        elif "subscription" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "subscriptionId"}
        elif "template" in stderr and ("not found" in stderr or "required" in stderr):
            return {"tipo_error": "MissingParameter", "campo_faltante": "template"}
        elif "storage account" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "storageAccount"}
    
    return {"tipo_error": "GenericError", "campo_faltante": None}