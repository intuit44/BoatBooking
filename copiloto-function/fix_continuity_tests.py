"""
🔧 Fix para Pruebas de Continuidad
Corrige los problemas detectados en las pruebas 4 y 6
"""

import requests
import json
import time
import logging

BASE_URL = "http://localhost:7071/api"
HEADERS = {"Content-Type": "application/json"}

def test_memory_persistence():
    """Prueba que la memoria persista entre llamadas"""
    
    print("🧪 PROBANDO PERSISTENCIA DE MEMORIA")
    print("=" * 50)
    
    session_id = f"continuity_test_{int(time.time())}"
    agent_id = "test_agent_continuity"
    
    # 1. Hacer una interacción inicial para crear memoria
    print("1️⃣ Creando interacción inicial...")
    response1 = requests.post(
        f"{BASE_URL}/verificar-sistema",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": agent_id},
        json={"test_action": "initial_diagnostic"}
    )
    
    print(f"   Status: {response1.status_code}")
    if response1.status_code == 200:
        print("   ✅ Interacción inicial creada")
    else:
        print("   ❌ Error en interacción inicial")
        return False
    
    time.sleep(1)  # Esperar para que se registre
    
    # 2. Consultar historial para verificar que se guardó
    print("2️⃣ Consultando historial...")
    response2 = requests.post(
        f"{BASE_URL}/historial-interacciones",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": agent_id},
        json={}
    )
    
    print(f"   Status: {response2.status_code}")
    if response2.status_code == 200:
        data = response2.json()
        has_history = data.get("tiene_historial", False)
        total_interactions = data.get("total_interacciones", 0)
        
        print(f"   Tiene historial: {has_history}")
        print(f"   Total interacciones: {total_interactions}")
        
        if has_history and total_interactions > 0:
            print("   ✅ Memoria persistió correctamente")
            return True
        else:
            print("   ❌ Memoria no persistió")
            print(f"   Respuesta completa: {json.dumps(data, indent=2)[:500]}...")
            return False
    else:
        print("   ❌ Error consultando historial")
        return False

def test_cross_agent_visibility():
    """Prueba que los agentes vean interacciones de otros agentes"""
    
    print("\n🧪 PROBANDO VISIBILIDAD CRUZADA ENTRE AGENTES")
    print("=" * 50)
    
    session_id = f"cross_agent_test_{int(time.time())}"
    
    # 1. Interacción con Agent A
    print("1️⃣ Interacción con Agent A...")
    response1 = requests.post(
        f"{BASE_URL}/ejecutar-cli",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": "agent_a"},
        json={"comando": "test command from agent A"}
    )
    
    print(f"   Status: {response1.status_code}")
    time.sleep(1)
    
    # 2. Interacción con Agent B
    print("2️⃣ Interacción con Agent B...")
    response2 = requests.post(
        f"{BASE_URL}/verificar-sistema",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": "agent_b"},
        json={"test_action": "system check from agent B"}
    )
    
    print(f"   Status: {response2.status_code}")
    time.sleep(1)
    
    # 3. Agent A consulta historial (debe ver ambas interacciones si es memoria universal)
    print("3️⃣ Agent A consulta historial...")
    response3 = requests.post(
        f"{BASE_URL}/historial-interacciones",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": "agent_a"},
        json={}
    )
    
    if response3.status_code == 200:
        data = response3.json()
        total_interactions = data.get("total_interacciones", 0)
        
        print(f"   Total interacciones visibles para Agent A: {total_interactions}")
        
        # En memoria universal, debería ver más de sus propias interacciones
        if total_interactions >= 2:
            print("   ✅ Memoria cruzada funciona (memoria universal)")
            return True
        else:
            print("   ❌ Memoria cruzada no funciona")
            print(f"   Respuesta: {json.dumps(data, indent=2)[:500]}...")
            return False
    else:
        print("   ❌ Error consultando historial")
        return False

def test_required_fields():
    """Prueba que todos los campos requeridos estén presentes"""
    
    print("\n🧪 PROBANDO CAMPOS REQUERIDOS")
    print("=" * 50)
    
    session_id = f"fields_test_{int(time.time())}"
    
    response = requests.post(
        f"{BASE_URL}/historial-interacciones",
        headers={**HEADERS, "Session-ID": session_id, "Agent-ID": "fields_test_agent"},
        json={}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        required_fields = [
            "interpretacion_semantica",
            "contexto_inteligente", 
            "validation_applied",
            "validation_stats",
            "metadata"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if not missing_fields:
            print("   ✅ Todos los campos requeridos están presentes")
            
            # Verificar estructura de metadata
            metadata = data.get("metadata", {})
            required_metadata = ["memoria_aplicada", "session_info", "timestamp"]
            missing_metadata = [f for f in required_metadata if f not in metadata]
            
            if not missing_metadata:
                print("   ✅ Estructura de metadata completa")
                return True
            else:
                print(f"   ❌ Campos faltantes en metadata: {missing_metadata}")
                return False
        else:
            print(f"   ❌ Campos faltantes: {missing_fields}")
            return False
    else:
        print(f"   ❌ Error en respuesta: {response.status_code}")
        return False

if __name__ == "__main__":
    print("DIAGNOSTICO DE PROBLEMAS EN PRUEBAS")
    print("=" * 60)
    
    results = []
    
    # Ejecutar pruebas de diagnóstico
    results.append(("Persistencia de Memoria", test_memory_persistence()))
    results.append(("Visibilidad Cruzada", test_cross_agent_visibility()))
    results.append(("Campos Requeridos", test_required_fields()))
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DEL DIAGNÓSTICO")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"📈 TOTAL: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 TODOS LOS PROBLEMAS CORREGIDOS")
        print("🚀 Listo para ejecutar test_production_readiness.py")
    else:
        print("🔧 AÚN HAY PROBLEMAS QUE CORREGIR")
        print("💡 Revisa los logs de Azure Function para más detalles")