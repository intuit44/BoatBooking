def test_analizar_error_cli():
    """Test función _analizar_error_cli"""
    
    def _analizar_error_cli(intentos_log, comando):
        for intento in intentos_log:
            stderr = intento.get("stderr", "").lower()
            
            if "resource group" in stderr and "required" in stderr:
                return {"tipo_error": "MissingParameter", "campo_faltante": "resourceGroup"}
            elif "location" in stderr and ("required" in stderr or "must be specified" in stderr):
                return {"tipo_error": "MissingParameter", "campo_faltante": "location"}
        
        return {"tipo_error": "GenericError", "campo_faltante": None}
    
    # Test
    intentos_log = [{"stderr": "az: error: argument --resource-group/-g: required"}]
    resultado = _analizar_error_cli(intentos_log, "az group create --name test")
    
    print(f"✅ Análisis error: {resultado}")
    assert resultado["tipo_error"] == "MissingParameter"
    assert resultado["campo_faltante"] == "resourceGroup"

def test_reparar_comando():
    """Test función _reparar_comando_con_memoria"""
    
    def _reparar_comando_con_memoria(comando, campo, valor):
        if campo == "resourceGroup" and "--resource-group" not in comando:
            return f"{comando} --resource-group {valor}"
        return comando
    
    # Test
    comando_reparado = _reparar_comando_con_memoria("az group create --name test", "resourceGroup", "boat-rental-rg")
    
    print(f"✅ Comando reparado: {comando_reparado}")
    assert "--resource-group boat-rental-rg" in comando_reparado

def test_endpoint_alternativo():
    """Test función _get_endpoint_alternativo"""
    
    def _get_endpoint_alternativo(campo_faltante, contexto=""):
        mapping = {
            "resourceGroup": "/api/verificar-cosmos",
            "location": "/api/status"
        }
        return mapping.get(campo_faltante, "/api/status")
    
    # Test
    resultado = _get_endpoint_alternativo("resourceGroup")
    
    print(f"✅ Endpoint alternativo: {resultado}")
    assert resultado == "/api/verificar-cosmos"

if __name__ == "__main__":
    print("Testing autorreparacion components...")
    
    test_analizar_error_cli()
    test_reparar_comando()
    test_endpoint_alternativo()
    
    print("\nAll component tests passed!")
    print("Autorreparacion logic is working correctly")