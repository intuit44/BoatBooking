"""
Test que simula el flujo exacto de Foundry:
1. Llamar /api/copiloto con Session-ID=assistant
2. Llamar /api/historial-interacciones con tipo=error
3. Verificar que encuentra los documentos de prueba en AI Search
"""

import requests
import json

BASE_URL = "http://localhost:7071"

def test_foundry_flow():
    print("=" * 80)
    print("🧪 TEST: Simulando flujo de Foundry")
    print("=" * 80)
    
    # 1️⃣ PASO 1: Llamar /api/copiloto (como lo hace Foundry)
    print("\n1️⃣ Llamando /api/copiloto con Session-ID=assistant...")
    
    response1 = requests.get(
        f"{BASE_URL}/api/copiloto",
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant"
        }
    )
    
    print(f"   Status: {response1.status_code}")
    result1 = response1.json()
    print(f"   Tipo respuesta: {result1.get('tipo', 'N/A')}")
    print(f"   Memoria disponible: {result1.get('metadata', {}).get('memoria_disponible', 'N/A')}")
    
    # 2️⃣ PASO 2: Llamar /api/historial-interacciones con tipo=error
    print("\n2️⃣ Llamando /api/historial-interacciones con tipo=error...")
    
    response2 = requests.post(
        f"{BASE_URL}/api/historial-interacciones",
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant"
        },
        json={
            "limit": 10,
            "tipo": "error"
        }
    )
    
    print(f"   Status: {response2.status_code}")
    result2 = response2.json()
    print(f"   Éxito: {result2.get('exito')}")
    print(f"   Total interacciones: {result2.get('total', 0)}")
    print(f"   Respuesta usuario: {result2.get('respuesta_usuario', '')[:200]}...")
    
    # 3️⃣ VERIFICAR: ¿Encontró documentos en AI Search?
    print("\n3️⃣ Verificación de búsqueda en AI Search...")
    
    metadata = result2.get('metadata', {})
    print(f"   Query SQL aplicada: {metadata.get('query_sql', 'N/A')[:100]}...")
    print(f"   Wrapper aplicado: {metadata.get('wrapper_aplicado', False)}")
    
    # 4️⃣ PRUEBA DIRECTA: Llamar buscar-memoria con query explícita
    print("\n4️⃣ Prueba directa de /api/buscar-memoria...")
    
    response3 = requests.post(
        f"{BASE_URL}/api/buscar-memoria",
        json={
            "query": "configuraciones del contenedor Docker y errores de conexión",
            "session_id": "assistant",
            "top": 5
        }
    )
    
    print(f"   Status: {response3.status_code}")
    result3 = response3.json()
    print(f"   Éxito: {result3.get('exito')}")
    print(f"   Total documentos: {result3.get('total', 0)}")
    
    if result3.get('documentos'):
        print(f"\n   ✅ DOCUMENTOS ENCONTRADOS:")
        for i, doc in enumerate(result3['documentos'][:3]):
            print(f"      {i+1}. {doc.get('texto_semantico', '')[:100]}...")
    else:
        print(f"   ❌ NO se encontraron documentos")
    
    # 5️⃣ RESUMEN
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL TEST")
    print("=" * 80)
    print(f"✅ /api/copiloto: {'OK' if response1.status_code == 200 else 'FAIL'}")
    print(f"✅ /api/historial-interacciones: {'OK' if response2.status_code == 200 else 'FAIL'}")
    print(f"✅ /api/buscar-memoria: {'OK' if response3.status_code == 200 else 'FAIL'}")
    print(f"\n🎯 Documentos encontrados en búsqueda directa: {result3.get('total', 0)}")
    print(f"🎯 Interacciones en historial: {result2.get('total', 0)}")
    
    if result3.get('total', 0) > 0 and result2.get('total', 0) == 0:
        print("\n⚠️ PROBLEMA DETECTADO:")
        print("   - buscar-memoria SÍ encuentra documentos")
        print("   - historial-interacciones NO los encuentra")
        print("   - Causa: La búsqueda automática no se está ejecutando correctamente")
    elif result3.get('total', 0) > 0 and result2.get('total', 0) > 0:
        print("\n✅ TODO FUNCIONA CORRECTAMENTE")
    else:
        print("\n❌ NO HAY DOCUMENTOS INDEXADOS EN AI SEARCH")
        print("   Ejecuta primero: python test_cosmos_memory.py")

if __name__ == "__main__":
    test_foundry_flow()
