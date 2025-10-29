"""
Test REAL simulando exactamente como Foundry invoca el endpoint
Basado en el ejemplo real proporcionado
"""
import requests
import json
import sys

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:7071"

def test_foundry_basic():
    """
    Simula la llamada REAL de Foundry:
    {
      "id": "call_9hDytijnmFMCI0zgY2fUjKxV",
      "type": "openapi",
      "function": {
        "name": "CopilotoFunctionApp_historialInteracciones",
        "arguments": "{\"Session-ID\":\"assistant\",\"Agent-ID\":\"assistant\"}"
      }
    }
    """
    print("\n" + "="*80)
    print("TEST 1: Llamada basica (como Foundry)")
    print("="*80)
    
    # Foundry envia Session-ID y Agent-ID como parametros
    params = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    # Tambien como headers
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/historial-interacciones",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validar estructura de respuesta
            assert 'exito' in data, "Falta campo 'exito'"
            assert 'interacciones' in data, "Falta campo 'interacciones'"
            assert 'total' in data, "Falta campo 'total'"
            assert 'respuesta_usuario' in data, "Falta campo 'respuesta_usuario'"
            
            print(f"\nRESULTADOS:")
            print(f"  - Exito: {data['exito']}")
            print(f"  - Total interacciones: {data['total']}")
            print(f"  - Interacciones devueltas: {len(data['interacciones'])}")
            print(f"  - Session ID: {data.get('session_id')}")
            print(f"  - Query dinamica: {data.get('query_dinamica_aplicada', False)}")
            
            if data['interacciones']:
                print(f"\nPRIMERA INTERACCION:")
                primera = data['interacciones'][0]
                print(f"  - Numero: {primera.get('numero')}")
                print(f"  - Timestamp: {primera.get('timestamp')}")
                print(f"  - Endpoint: {primera.get('endpoint')}")
                print(f"  - Exito: {primera.get('exito')}")
                print(f"  - Tipo: {primera.get('tipo')}")
                texto = primera.get('texto_semantico', '')
                print(f"  - Texto semantico (preview): {texto[:100]}...")
            
            print(f"\nRESPUESTA_USUARIO (preview):")
            print(f"  {data['respuesta_usuario'][:200]}...")
            
            return True
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_foundry_with_filters():
    """
    Test con filtros dinamicos (tipo, contiene, endpoint)
    Simula: arguments: '{"Session-ID":"assistant","tipo":"interaccion_usuario","contiene":"cosmos"}'
    """
    print("\n" + "="*80)
    print("TEST 2: Con filtros dinamicos")
    print("="*80)
    
    params = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "tipo": "interaccion_usuario",
        "contiene": "copiloto",
        "limite": 5
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/historial-interacciones",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nRESULTADOS:")
            print(f"  - Query dinamica aplicada: {data.get('query_dinamica_aplicada', False)}")
            print(f"  - Total encontrado: {data.get('total', 0)}")
            print(f"  - Interacciones devueltas: {len(data.get('interacciones', []))}")
            
            if data.get('filtros_aplicados'):
                print(f"\nFILTROS APLICADOS:")
                for key, value in data['filtros_aplicados'].items():
                    print(f"  - {key}: {value}")
            
            if data.get('metadata', {}).get('query_sql'):
                print(f"\nQUERY SQL GENERADA:")
                print(f"  {data['metadata']['query_sql']}")
            
            if data.get('interacciones'):
                print(f"\nINTERACCIONES FILTRADAS:")
                for inter in data['interacciones'][:3]:
                    print(f"  - {inter['endpoint']}: {inter.get('texto_semantico', '')[:60]}...")
            
            return True
        else:
            print(f"ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def test_foundry_temporal():
    """Test con filtro temporal (ultimas 24h)"""
    print("\n" + "="*80)
    print("TEST 3: Filtro temporal (ultimas 24h)")
    print("="*80)
    
    params = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "fecha_inicio": "ultimas 24h",
        "limite": 10
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/historial-interacciones",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nRESULTADOS:")
            print(f"  - Query dinamica: {data.get('query_dinamica_aplicada', False)}")
            print(f"  - Total: {data.get('total', 0)}")
            
            if data.get('metadata', {}).get('query_sql'):
                print(f"\nQUERY SQL:")
                print(f"  {data['metadata']['query_sql']}")
            
            return True
        else:
            print(f"ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def test_foundry_endpoint_filter():
    """Test filtrando por endpoint especifico"""
    print("\n" + "="*80)
    print("TEST 4: Filtro por endpoint")
    print("="*80)
    
    params = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "endpoint": "/api/copiloto",
        "limite": 5
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/historial-interacciones",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nRESULTADOS:")
            print(f"  - Query dinamica: {data.get('query_dinamica_aplicada', False)}")
            print(f"  - Total: {data.get('total', 0)}")
            
            if data.get('interacciones'):
                print(f"\nENDPOINTS ENCONTRADOS:")
                for inter in data['interacciones']:
                    print(f"  - {inter.get('endpoint')} ({inter.get('timestamp')})")
            
            return True
        else:
            print(f"ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def test_foundry_post():
    """Test usando POST (como a veces hace Foundry)"""
    print("\n" + "="*80)
    print("TEST 5: POST con body")
    print("="*80)
    
    payload = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "tipo": "interaccion_usuario",
        "limite": 3
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/historial-interacciones",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nRESULTADOS:")
            print(f"  - Total: {data.get('total', 0)}")
            print(f"  - Query dinamica: {data.get('query_dinamica_aplicada', False)}")
            
            return True
        else:
            print(f"ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SIMULACION REAL DE FOUNDRY - QUERIES DINAMICAS")
    print("="*80)
    print("Estos tests replican exactamente como Foundry invoca el endpoint")
    print("="*80)
    
    results = []
    
    try:
        results.append(("Test 1: Basico", test_foundry_basic()))
        results.append(("Test 2: Filtros", test_foundry_with_filters()))
        results.append(("Test 3: Temporal", test_foundry_temporal()))
        results.append(("Test 4: Endpoint", test_foundry_endpoint_filter()))
        results.append(("Test 5: POST", test_foundry_post()))
        
        print("\n" + "="*80)
        print("RESUMEN DE TESTS")
        print("="*80)
        
        for name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"{name}: {status}")
        
        total = len(results)
        passed = sum(1 for _, r in results if r)
        print(f"\nTotal: {passed}/{total} tests pasaron")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: No se pudo conectar al servidor")
        print("Asegurate de que el servidor este corriendo:")
        print("  cd copiloto-function")
        print("  func start")
    except Exception as e:
        print(f"\nERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
