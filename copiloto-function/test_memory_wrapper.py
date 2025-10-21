#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que el wrapper de memoria está funcionando
"""

import requests
import json
import time

def test_memory_wrapper():
    """Prueba el wrapper de memoria con varios endpoints"""
    
    base_url = "http://localhost:7071"  # Cambiar si es necesario
    
    # Headers para simular un agente
    headers = {
        "Content-Type": "application/json",
        "Agent-ID": "TestAgent",
        "Session-ID": "test-session-123"
    }
    
    print("INICIANDO TESTS DEL WRAPPER DE MEMORIA")
    print("=" * 50)
    
    # Test 1: Endpoint status
    print("\n1. Probando /api/status...")
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("OK Status: Wrapper aplicado correctamente")
            else:
                print("ERROR Status: Wrapper NO aplicado")
                print(f"   Respuesta: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"❌ Status: Error HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Status: Error de conexión: {e}")
    
    # Test 2: Endpoint historial-interacciones
    print("\n2️⃣ Probando /api/historial-interacciones...")
    try:
        response = requests.get(f"{base_url}/api/historial-interacciones", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("✅ Historial: Wrapper aplicado correctamente")
                if data.get("contexto_conversacion"):
                    print(f"   📝 Contexto encontrado: {data['contexto_conversacion']['mensaje']}")
                else:
                    print("   📝 Sin contexto previo (normal para primera ejecución)")
            else:
                print("❌ Historial: Wrapper NO aplicado")
                print(f"   Respuesta: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"❌ Historial: Error HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Historial: Error de conexión: {e}")
    
    # Test 3: Endpoint copiloto
    print("\n3️⃣ Probando /api/copiloto...")
    try:
        payload = {"consulta": "test wrapper memoria"}
        response = requests.post(f"{base_url}/api/copiloto", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data and data["metadata"].get("wrapper_aplicado"):
                print("✅ Copiloto: Wrapper aplicado correctamente")
                if data.get("contexto_conversacion"):
                    print(f"   📝 Contexto encontrado: {data['contexto_conversacion']['mensaje']}")
            else:
                print("❌ Copiloto: Wrapper NO aplicado")
        else:
            print(f"❌ Copiloto: Error HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Copiloto: Error de conexión: {e}")
    
    # Test 4: Verificar que se está registrando en memoria
    print("\n4️⃣ Verificando registro en memoria...")
    time.sleep(2)  # Esperar a que se registre
    try:
        response = requests.get(f"{base_url}/api/historial-interacciones", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            if total > 0:
                print(f"✅ Memoria: {total} interacciones registradas")
                interacciones = data.get("interacciones", [])
                if interacciones:
                    ultima = interacciones[0]
                    print(f"   📝 Última: {ultima.get('texto_semantico', 'Sin texto semántico')[:80]}...")
            else:
                print("⚠️ Memoria: Sin interacciones registradas aún")
        else:
            print(f"❌ Memoria: Error HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Memoria: Error de conexión: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 TESTS COMPLETADOS")
    print("\n💡 DIAGNÓSTICO:")
    print("   - Si ves '✅ Wrapper aplicado correctamente' en todos los endpoints, el wrapper funciona")
    print("   - Si ves 'Sin contexto previo' es normal en la primera ejecución")
    print("   - Si ves interacciones registradas, la memoria está funcionando")
    print("\n🔧 SOLUCIÓN si hay problemas:")
    print("   1. Verificar que la Function App esté ejecutándose")
    print("   2. Verificar que Cosmos DB esté configurado")
    print("   3. Verificar que el wrapper se aplique ANTES de definir endpoints")

if __name__ == "__main__":
    test_memory_wrapper()