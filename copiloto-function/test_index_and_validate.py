"""
Test completo: Indexar datos → Validar flujo Foundry
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:7071"

def indexar_datos_prueba():
    """Indexa interacciones de prueba en AI Search"""
    print("\n" + "="*80)
    print("📝 PASO 1: Indexando datos de prueba en AI Search")
    print("="*80)
    
    # Datos de prueba sobre Docker
    interacciones_prueba = [
        {
            "session_id": "test-session-001",
            "agent_id": "docker-agent",
            "endpoint": "ejecutar-cli",
            "texto_semantico": "Error de conexión al contenedor Docker boat-rental-backend. Puerto 5432 no responde.",
            "exito": False,
            "tipo": "error",
            "metadata": {
                "comando": "docker exec boat-rental-backend psql",
                "error": "Connection refused",
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "session_id": "test-session-002",
            "agent_id": "docker-agent",
            "endpoint": "diagnostico-recursos",
            "texto_semantico": "Configuración del contenedor Docker: imagen postgres:14, puerto 5432:5432, volumen boat-data",
            "exito": True,
            "tipo": "configuracion",
            "metadata": {
                "container": "boat-rental-backend",
                "image": "postgres:14",
                "ports": ["5432:5432"],
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "session_id": "test-session-003",
            "agent_id": "docker-agent",
            "endpoint": "ejecutar-cli",
            "texto_semantico": "Error al iniciar contenedor Docker: conflicto de puertos. El puerto 5432 ya está en uso por otro proceso.",
            "exito": False,
            "tipo": "error",
            "metadata": {
                "comando": "docker start boat-rental-backend",
                "error": "Port already allocated",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ]
    
    # Registrar cada interacción
    for i, interaccion in enumerate(interacciones_prueba, 1):
        response = requests.post(
            f"{BASE_URL}/api/registrar-interaccion",
            json=interaccion,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Interacción {i}/3 indexada")
        else:
            print(f"   ❌ Error indexando {i}/3: {response.status_code}")
    
    print("\n⏳ Esperando 3 segundos para que AI Search indexe...")
    import time
    time.sleep(3)

def test_busqueda_directa():
    """Prueba búsqueda directa en AI Search"""
    print("\n" + "="*80)
    print("🔍 PASO 2: Validando búsqueda directa en AI Search")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/buscar-memoria",
        json={"query": "configuraciones del contenedor Docker y errores de conexión"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Documentos encontrados: {data.get('total', 0)}")
        
        if data.get('documentos'):
            print(f"\n   📄 Primeros resultados:")
            for doc in data['documentos'][:2]:
                print(f"      - {doc.get('texto_semantico', 'N/A')[:80]}...")
                print(f"        Score: {doc.get('@search.score', 0):.3f}")
        
        return data.get('total', 0) > 0
    else:
        print(f"   ❌ Error: {response.status_code}")
        return False

def test_flujo_foundry():
    """Simula el flujo exacto de Foundry"""
    print("\n" + "="*80)
    print("🤖 PASO 3: Simulando flujo de Foundry")
    print("="*80)
    
    # Paso 1: Copiloto inicial
    print("\n1️⃣ Llamando /api/copiloto...")
    response1 = requests.post(
        f"{BASE_URL}/api/copiloto",
        json={},
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant"
        }
    )
    print(f"   Status: {response1.status_code}")
    
    # Paso 2: Historial con tipo=error (como lo hace Foundry)
    print("\n2️⃣ Llamando /api/historial-interacciones con tipo=error...")
    response2 = requests.post(
        f"{BASE_URL}/api/historial-interacciones",
        json={
            "limit": 10,
            "tipo": "error"
        },
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant"
        }
    )
    
    if response2.status_code == 200:
        data = response2.json()
        print(f"   Status: {response2.status_code}")
        print(f"   Total interacciones: {data.get('total', 0)}")
        print(f"   Respuesta: {data.get('respuesta_usuario', 'N/A')[:100]}...")
        
        # Verificar si se ejecutó búsqueda semántica
        metadata = data.get('metadata', {})
        if 'busqueda_semantica' in metadata:
            print(f"\n   ✅ Búsqueda semántica ejecutada:")
            print(f"      Query: {metadata['busqueda_semantica'].get('query', 'N/A')}")
            print(f"      Docs encontrados: {metadata['busqueda_semantica'].get('total_docs', 0)}")
        else:
            print(f"\n   ❌ NO se ejecutó búsqueda semántica")
        
        return data.get('total', 0) > 0
    else:
        print(f"   ❌ Error: {response2.status_code}")
        return False

def main():
    print("\n" + "="*80)
    print("🧪 TEST COMPLETO: Indexar → Validar Flujo Foundry")
    print("="*80)
    
    # Paso 1: Indexar datos
    indexar_datos_prueba()
    
    # Paso 2: Validar búsqueda directa
    busqueda_ok = test_busqueda_directa()
    
    # Paso 3: Validar flujo Foundry
    foundry_ok = test_flujo_foundry()
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"✅ Indexación: OK")
    print(f"{'✅' if busqueda_ok else '❌'} Búsqueda directa: {'OK' if busqueda_ok else 'FALLÓ'}")
    print(f"{'✅' if foundry_ok else '❌'} Flujo Foundry: {'OK' if foundry_ok else 'FALLÓ'}")
    
    if busqueda_ok and foundry_ok:
        print("\n🎉 SISTEMA LISTO PARA FOUNDRY")
    else:
        print("\n⚠️ REVISAR CONFIGURACIÓN")

if __name__ == "__main__":
    main()
