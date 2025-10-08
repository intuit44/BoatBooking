import sys
import os
sys.path.append(os.path.dirname(__file__))

from unittest.mock import patch, Mock
import json

def test_buscar_en_memoria():
    """Test función _buscar_en_memoria con mock"""
    
    # Mock CosmosMemoryStore
    mock_cosmos = Mock()
    mock_cosmos.enabled = True
    mock_cosmos.container = Mock()
    
    # Mock query response
    mock_items = [
        {
            "response_data": {
                "resourceGroup": "boat-rental-rg",
                "location": "eastus"
            }
        }
    ]
    mock_cosmos.container.query_items.return_value = mock_items
    
    with patch('function_app.CosmosMemoryStore', return_value=mock_cosmos):
        with patch('function_app.obtener_estado_sistema', return_value={"exito": True}):
            from function_app import _buscar_en_memoria
            
            # Test buscar resourceGroup
            resultado = _buscar_en_memoria("resourceGroup")
            print(f"Resultado resourceGroup: {resultado}")
            assert resultado == "boat-rental-rg"
            
            # Test buscar location  
            resultado = _buscar_en_memoria("location")
            print(f"Resultado location: {resultado}")
            assert resultado == "eastus"
            
            # Test campo no encontrado
            resultado = _buscar_en_memoria("noexiste")
            print(f"Resultado no existe: {resultado}")
            assert resultado is None
            
            print("✅ Test _buscar_en_memoria passed")

def test_buscar_memoria_disabled():
    """Test cuando Cosmos está deshabilitado"""
    
    mock_cosmos = Mock()
    mock_cosmos.enabled = False
    mock_cosmos.container = None
    
    with patch('function_app.CosmosMemoryStore', return_value=mock_cosmos):
        with patch('function_app.obtener_estado_sistema', return_value={"exito": True}):
            from function_app import _buscar_en_memoria
            
            resultado = _buscar_en_memoria("resourceGroup")
            print(f"Resultado disabled: {resultado}")
            assert resultado is None
            
            print("✅ Test memoria disabled passed")

if __name__ == "__main__":
    test_buscar_en_memoria()
    test_buscar_memoria_disabled()
    print("\n✅ All memory tests passed")