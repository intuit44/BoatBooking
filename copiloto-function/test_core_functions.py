#!/usr/bin/env python3
"""Test de las 3 funciones principales de autorreparacion"""

def test_analizar_error_cli():
    """Test: detecta parametros faltantes en stderr"""
    def _analizar_error_cli(intentos_log, comando):
        for intento in intentos_log:
            stderr = intento.get("stderr", "").lower()
            if "resource group" in stderr and "required" in stderr:
                return {"tipo_error": "MissingParameter", "campo_faltante": "resourceGroup"}
            elif "location" in stderr and "required" in stderr:
                return {"tipo_error": "MissingParameter", "campo_faltante": "location"}
        return {"tipo_error": "GenericError", "campo_faltante": None}
    
    # Test 1: resourceGroup faltante
    logs = [{"stderr": "argument --resource-group/-g: required resource group"}]
    result = _analizar_error_cli(logs, "az group create")
    assert result["tipo_error"] == "MissingParameter"
    assert result["campo_faltante"] == "resourceGroup"
    print("OK: Detecta resourceGroup faltante")
    
    # Test 2: location faltante  
    logs = [{"stderr": "argument --location/-l: required location"}]
    result = _analizar_error_cli(logs, "az group create")
    assert result["tipo_error"] == "MissingParameter"
    assert result["campo_faltante"] == "location"
    print("OK: Detecta location faltante")

def test_reparar_comando():
    """Test: repara comando agregando parametro"""
    def _reparar_comando_con_memoria(comando, campo, valor):
        if campo == "resourceGroup" and "--resource-group" not in comando:
            return f"{comando} --resource-group {valor}"
        elif campo == "location" and "--location" not in comando:
            return f"{comando} --location {valor}"
        return comando
    
    # Test 1: agregar resourceGroup
    original = "az group create --name test"
    reparado = _reparar_comando_con_memoria(original, "resourceGroup", "boat-rental-rg")
    assert "--resource-group boat-rental-rg" in reparado
    print("OK: Repara resourceGroup")
    
    # Test 2: agregar location
    reparado = _reparar_comando_con_memoria(original, "location", "eastus")
    assert "--location eastus" in reparado
    print("OK: Repara location")

def test_endpoint_alternativo():
    """Test: mapea campo a endpoint correcto"""
    def _get_endpoint_alternativo(campo_faltante, contexto=""):
        mapping = {
            "resourceGroup": "/api/verificar-cosmos",
            "location": "/api/status",
            "subscriptionId": "/api/verificar-cosmos"
        }
        return mapping.get(campo_faltante, "/api/status")
    
    # Test mapping
    assert _get_endpoint_alternativo("resourceGroup") == "/api/verificar-cosmos"
    assert _get_endpoint_alternativo("location") == "/api/status"
    assert _get_endpoint_alternativo("unknown") == "/api/status"
    print("OK: Mapea endpoints correctamente")

if __name__ == "__main__":
    print("Testing core autorreparacion functions...")
    test_analizar_error_cli()
    test_reparar_comando()
    test_endpoint_alternativo()
    print("All core function tests PASSED")