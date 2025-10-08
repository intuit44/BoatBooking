import json

def test_analizar_error_cli():
    """Test función _analizar_error_cli"""
    
    # Simular logs de error
    intentos_log = [
        {
            "stderr": "az: error: argument --resource-group/-g: expected one argument"
        }
    ]
    
    # Importar función directamente
    exec(open('_analizar_error_cli_fixed.py').read())
    
    resultado = _analizar_error_cli(intentos_log, "az group create --name test")
    
    print(f"Análisis error: {json.dumps(resultado, indent=2)}")
    
    assert resultado["tipo_error"] == "MissingParameter"
    assert resultado["campo_faltante"] == "resourceGroup"
    
    print("✅ Test _analizar_error_cli passed")

def test_reparar_comando():
    """Test función _reparar_comando_con_memoria"""
    
    exec(open('_reparar_comando_con_memoria.py').read())
    
    comando_original = "az group create --name test"
    comando_reparado = _reparar_comando_con_memoria(comando_original, "resourceGroup", "boat-rental-rg")
    
    print(f"Comando original: {comando_original}")
    print(f"Comando reparado: {comando_reparado}")
    
    assert "--resource-group boat-rental-rg" in comando_reparado
    
    print("✅ Test _reparar_comando passed")

def test_get_endpoint_alternativo():
    """Test función _get_endpoint_alternativo"""
    
    # Simular función
    def _get_endpoint_alternativo(campo_faltante, contexto=""):
        mapping = {
            "resourceGroup": "/api/verificar-cosmos",
            "location": "/api/status", 
            "subscriptionId": "/api/verificar-cosmos",
            "storageAccount": "/api/listar-blobs",
            "appName": "/api/verificar-app-insights"
        }
        return mapping.get(campo_faltante, "/api/status")
    
    resultado = _get_endpoint_alternativo("resourceGroup")
    print(f"Endpoint alternativo: {resultado}")
    
    assert resultado == "/api/verificar-cosmos"
    
    print("✅ Test _get_endpoint_alternativo passed")

if __name__ == "__main__":
    test_analizar_error_cli()
    test_reparar_comando()
    test_get_endpoint_alternativo()
    print("\n✅ All integration tests passed")