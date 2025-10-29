"""
Test de simulación REAL de cómo Foundry invoca el endpoint historial-interacciones
Simula el formato exacto de arguments que envía Foundry
"""
import requests
import json

# URL del endpoint
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/historial-interacciones"

def test_foundry_basic_call():
    """Test 1: Llamada básica como la hace Foundry (headers en arguments)"""
    print("\n" + "="*80)
    print("TEST 1: Llamada básica (simulando Foundry)")
    print("="*80)
    
    # Foundry envía los headers como parte del body en 'arguments'
    # NO como headers HTTP reales
    payload = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    # Pero también los enviamos como headers HTTP para compatibilidad
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        params=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response preview: {response.text[:500]}...")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Total interacciones: {data.get('total', 0)}")
        print(f"✅ Interacciones devueltas: {len(data.get('interacciones', []))}")
        if data.get('interacciones'):
            print(f"\n📝 Primera interacción:")
            primera = data['interacciones'][0]
            print(f"   - Endpoint: {primera.get('endpoint')}")
            print(f"   - Timestamp: {primera.get('timestamp')}")
            print(f"   - Texto semántico: {primera.get('texto_semantico', '')[:100]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_foundry_with_filters():
    """Test 2: Con filtros dinámicos (tipo, contiene, etc)"""
    print("\n" + "="*80)
    print("TEST 2: Con filtros dinámicos")
    print("="*80)
    
    payload = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "tipo": "interaccion_usuario",
        "contiene": "copiloto",
        "limite": 5
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        params=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Query dinámica aplicada: {data.get('query_dinamica_aplicada', False)}")
        print(f"✅ Total encontrado: {data.get('total', 0)}")
        print(f"✅ Filtros aplicados: {data.get('filtros_aplicados', {})}")
        
        if data.get('interacciones'):
            print(f"\n📝 Interacciones filtradas:")
            for inter in data['interacciones'][:3]:
                print(f"   - {inter.get('endpoint')}: {inter.get('texto_semantico', '')[:80]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_foundry_temporal_filter():
    """Test 3: Filtro temporal (últimas 24h)"""
    print("\n" + "="*80)
    print("TEST 3: Filtro temporal (últimas 24h)")
    print("="*80)
    
    payload = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "fecha_inicio": "últimas 24h",
        "limite": 10
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        params=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Query dinámica: {data.get('query_dinamica_aplicada', False)}")
        print(f"✅ Total: {data.get('total', 0)}")
        print(f"✅ SQL generado: {data.get('metadata', {}).get('query_sql', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")

def test_foundry_endpoint_filter():
    """Test 4: Filtrar por endpoint específico"""
    print("\n" + "="*80)
    print("TEST 4: Filtrar por endpoint específico")
    print("="*80)
    
    payload = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "endpoint": "/api/copiloto",
        "limite": 5
    }
    
    headers = {
        "Session-ID": "assistant",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        params=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Query dinámica: {data.get('query_dinamica_aplicada', False)}")
        print(f"✅ Total: {data.get('total', 0)}")
        
        if data.get('interacciones'):
            print(f"\n📝 Interacciones del endpoint /api/copiloto:")
            for inter in data['interacciones']:
                print(f"   - {inter.get('endpoint')}: {inter.get('timestamp')}")
    else:
        print(f"❌ Error: {response.text}")

def test_foundry_post_method():
    """Test 5: Usando POST (como a veces hace Foundry)"""
    print("\n" + "="*80)
    print("TEST 5: POST con body (alternativa de Foundry)")
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
    
    response = requests.post(
        f"{BASE_URL}{ENDPOINT}",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Total: {data.get('total', 0)}")
        print(f"✅ Query dinámica: {data.get('query_dinamica_aplicada', False)}")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    print("\nSIMULACION DE INVOCACIONES DESDE FOUNDRY")
    print("=" * 80)
    print("Estos tests simulan exactamente como Foundry invoca el endpoint")
    print("=" * 80)
    
    try:
        test_foundry_basic_call()
        test_foundry_with_filters()
        test_foundry_temporal_filter()
        test_foundry_endpoint_filter()
        test_foundry_post_method()
        
        print("\n" + "="*80)
        print("✅ TESTS COMPLETADOS")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("Asegúrate de que el servidor esté corriendo:")
        print("  cd copiloto-function")
        print("  func start")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
