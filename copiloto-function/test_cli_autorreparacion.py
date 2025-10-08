import json
import requests
import time

def test_cli_missing_parameter():
    """Test que el endpoint devuelve 422 con metadata cuando falta parámetro"""
    url = "http://localhost:7071/api/ejecutar-cli"
    
    # Comando que falla por falta de resource group
    payload = {
        "comando": "az group create --name test-group"
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 422:
        data = response.json()
        assert data["tipo_error"] == "MissingParameter"
        assert "campo_faltante" in data
        assert "endpoint_alternativo" in data
        assert "memoria_detectada" in data
        print("✅ Test 422 response passed")
    else:
        print("❌ Expected 422, got", response.status_code)

def test_memory_consultation():
    """Test endpoint consultar-memoria"""
    url = "http://localhost:7071/api/consultar-memoria"
    
    payload = {
        "claves": ["resourceGroup", "location", "subscriptionId"]
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Memory Status: {response.status_code}")
    print(f"Memory Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        assert "memoria" in data
        assert "claves_encontradas" in data
        print("✅ Memory consultation passed")

def test_agent_422_simulation():
    """Simula comportamiento del agente ante 422"""
    
    # 1. Comando inicial que falla
    cli_response = requests.post("http://localhost:7071/api/ejecutar-cli", 
                                json={"comando": "az group create --name test"})
    
    if cli_response.status_code == 422:
        data = cli_response.json()
        endpoint_alt = data.get("endpoint_alternativo")
        campo_faltante = data.get("campo_faltante")
        
        print(f"🔧 Agente detecta falta: {campo_faltante}")
        print(f"🔄 Ejecutando: {endpoint_alt}")
        
        # 2. Agente ejecuta endpoint alternativo
        if endpoint_alt:
            alt_response = requests.get(f"http://localhost:7071{endpoint_alt}")
            print(f"Alt Status: {alt_response.status_code}")
            
            if alt_response.status_code == 200:
                print("✅ Agente simulation passed")
            else:
                print("❌ Alternative endpoint failed")

if __name__ == "__main__":
    print("🧪 Testing CLI autorreparación...")
    
    try:
        test_cli_missing_parameter()
        time.sleep(1)
        test_memory_consultation()
        time.sleep(1)
        test_agent_422_simulation()
        
        print("\n✅ All tests completed")
        
    except requests.exceptions.ConnectionError:
        print("❌ Function App not running. Start with: func start")
    except Exception as e:
        print(f"❌ Test failed: {e}")