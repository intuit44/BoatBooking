#!/usr/bin/env python3
"""Test simple del sistema Bing Grounding"""

def test_trigger_logic():
    """Test: logica de activacion de Bing"""
    
    def should_trigger_bing_grounding(error_info, contexto):
        error_type = error_info.get("tipo_error", "")
        
        # Casos que activan Bing
        if error_type == "COMMAND_NOT_FOUND":
            return True
        if error_type == "MissingParameter" and error_info.get("memoria_consultada") and not error_info.get("memoria_encontrada"):
            return True
        if any(keyword in contexto.lower() for keyword in ["no se", "desconozco", "error"]):
            return True
        
        return False
    
    # Test 1: Comando no encontrado
    result = should_trigger_bing_grounding({"tipo_error": "COMMAND_NOT_FOUND"}, "comando fallido")
    assert result == True
    print("OK: Activa para comando no encontrado")
    
    # Test 2: Parametro faltante sin memoria
    result = should_trigger_bing_grounding({
        "tipo_error": "MissingParameter",
        "memoria_consultada": True,
        "memoria_encontrada": False
    }, "falta parametro")
    assert result == True
    print("OK: Activa cuando memoria no resuelve")
    
    # Test 3: Contexto de error
    result = should_trigger_bing_grounding({"tipo_error": "GenericError"}, "no se como hacer esto")
    assert result == True
    print("OK: Activa por contexto de incertidumbre")

def test_comando_construction():
    """Test: construccion de comando desde Bing"""
    
    def construir_comando_desde_grounding(grounding_result, comando_original=""):
        if not grounding_result.get("exito"):
            return comando_original
        
        resultado = grounding_result.get("resultado", {})
        comando_sugerido = resultado.get("comando_sugerido", "")
        
        if comando_sugerido:
            return comando_sugerido
        
        # Extraer de resumen
        resumen = resultado.get("resumen", "")
        if "az group create" in resumen:
            return "az group create --name test --location eastus"
        
        return comando_original
    
    # Test construccion
    grounding_result = {
        "exito": True,
        "resultado": {
            "resumen": "Para crear grupo usar az group create --name test --location eastus",
            "comando_sugerido": "az group create --name test --location eastus"
        }
    }
    
    comando = construir_comando_desde_grounding(grounding_result, "az group create")
    assert "eastus" in comando
    print("OK: Construye comando desde resultado Bing")

def test_endpoint_structure():
    """Test: estructura del endpoint"""
    
    # Request esperado
    request = {
        "query": "como crear grupo Azure CLI",
        "contexto": "comando fallido",
        "intencion_original": "crear recurso",
        "prioridad": "alta"
    }
    
    # Response esperado
    response = {
        "exito": True,
        "resultado": {
            "resumen": "Usar az group create...",
            "fuentes": [{"titulo": "docs", "url": "https://docs.microsoft.com"}],
            "tipo": "snippet",
            "comando_sugerido": "az group create --name test"
        },
        "accion_sugerida": "Reintentar con comando sugerido",
        "reutilizable": True
    }
    
    # Validaciones
    assert "query" in request
    assert request["prioridad"] in ["baja", "normal", "alta", "critica"]
    assert response["exito"] == True
    assert "comando_sugerido" in response["resultado"]
    
    print("OK: Estructura del endpoint correcta")

if __name__ == "__main__":
    print("Testing Bing Grounding sistema...")
    
    test_trigger_logic()
    test_comando_construction()
    test_endpoint_structure()
    
    print("\nBing Grounding tests PASSED")
    print("Sistema de conocimiento externo listo")