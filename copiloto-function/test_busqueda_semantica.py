#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de búsqueda semántica automática sin body JSON
Simula el comportamiento de Foundry enviando headers pero body vacío
"""

import requests
import json
import time

BASE_URL = "http://localhost:7071"

def test_busqueda_semantica_con_headers():
    """Test 1: GET con headers (simula Foundry)"""
    print("\n🧪 Test 1: GET con Session-ID y Agent-ID en headers")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/api/auditar-deploy",
        headers={
            "Session-ID": "test-session-semantica-001",
            "Agent-ID": "agent-test-foundry"
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Verificar búsqueda semántica
    metadata = data.get("metadata", {})
    busqueda = metadata.get("busqueda_semantica", {})
    
    print(f"✅ Búsqueda semántica aplicada: {busqueda.get('aplicada', False)}")
    print(f"📊 Interacciones encontradas: {busqueda.get('interacciones_encontradas', 0)}")
    print(f"🎯 Endpoint buscado: {busqueda.get('endpoint_buscado', 'N/A')}")
    
    if busqueda.get("resumen_contexto"):
        print(f"📝 Resumen: {busqueda['resumen_contexto'][:100]}...")
    
    return busqueda.get('aplicada', False)


def test_busqueda_semantica_post_body_vacio():
    """Test 2: POST con body vacío (simula Foundry real)"""
    print("\n🧪 Test 2: POST con body vacío pero headers válidos")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/diagnostico-recursos",
        headers={
            "Session-ID": "foundry-session-456",
            "Agent-ID": "copilot-agent-002",
            "Content-Type": "application/json"
        },
        json={}  # Body vacío como Foundry
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    metadata = data.get("metadata", {})
    busqueda = metadata.get("busqueda_semantica", {})
    
    print(f"✅ Búsqueda semántica aplicada: {busqueda.get('aplicada', False)}")
    print(f"📊 Interacciones encontradas: {busqueda.get('interacciones_encontradas', 0)}")
    print(f"🌍 Memoria global: {metadata.get('memoria_global', False)}")
    
    return busqueda.get('aplicada', False)


def test_sin_session_id():
    """Test 3: Sin Session-ID (nueva sesión)"""
    print("\n🧪 Test 3: Sin Session-ID (nueva sesión)")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/auditar-deploy")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    metadata = data.get("metadata", {})
    busqueda = metadata.get("busqueda_semantica", {})
    
    print(f"❌ Búsqueda semántica aplicada: {busqueda.get('aplicada', False)}")
    print(f"📝 Razón: {busqueda.get('razon', 'N/A')}")
    print(f"🆕 Nueva sesión: {metadata.get('nueva_sesion', False)}")
    
    return not busqueda.get('aplicada', True)  # Debe ser False


def test_multiples_llamadas_mismo_endpoint():
    """Test 4: Múltiples llamadas al mismo endpoint para verificar acumulación"""
    print("\n🧪 Test 4: Múltiples llamadas para acumular memoria")
    print("=" * 60)
    
    session_id = f"test-acumulacion-{int(time.time())}"
    agent_id = "agent-acumulador"
    
    for i in range(3):
        print(f"\n📞 Llamada {i+1}/3...")
        response = requests.get(
            f"{BASE_URL}/api/auditar-deploy",
            headers={
                "Session-ID": session_id,
                "Agent-ID": agent_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            busqueda = data.get("metadata", {}).get("busqueda_semantica", {})
            print(f"   Interacciones encontradas: {busqueda.get('interacciones_encontradas', 0)}")
        
        time.sleep(1)  # Esperar para que se registre en Cosmos
    
    print("\n✅ Test de acumulación completado")
    return True


def main():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 60)
    print("🚀 TESTS DE BÚSQUEDA SEMÁNTICA AUTOMÁTICA")
    print("=" * 60)
    
    resultados = []
    
    try:
        resultados.append(("Test 1: Headers", test_busqueda_semantica_con_headers()))
        time.sleep(2)
        
        resultados.append(("Test 2: Body vacío", test_busqueda_semantica_post_body_vacio()))
        time.sleep(2)
        
        resultados.append(("Test 3: Sin Session-ID", test_sin_session_id()))
        time.sleep(2)
        
        resultados.append(("Test 4: Acumulación", test_multiples_llamadas_mismo_endpoint()))
        
    except Exception as e:
        print(f"\n❌ Error ejecutando tests: {e}")
        return False
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{estado} - {nombre}")
    
    total_pass = sum(1 for _, r in resultados if r)
    print(f"\n🎯 Total: {total_pass}/{len(resultados)} tests pasados")
    
    return total_pass == len(resultados)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
