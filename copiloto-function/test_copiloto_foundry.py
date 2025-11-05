#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del endpoint /api/copiloto simulando payload de Foundry
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:7071"

def test_foundry_payload():
    """Simula el payload que envía Foundry: body vacío, headers con Session-ID"""
    
    print("🧪 TEST 1: Payload Foundry (body vacío, solo headers)")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        headers={
            "Content-Type": "application/json",
            "Session-ID": "test-session-foundry",
            "Agent-ID": "FoundryAgent"
        },
        json={}  # Body vacío como Foundry
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    # Verificar que NO devuelva panel_inicial
    if result.get("tipo") == "panel_inicial":
        print("❌ FALLÓ: Devolvió panel_inicial (no detectó mensaje)")
        print(f"   Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        return False
    
    print("✅ PASÓ: No devolvió panel_inicial")
    print(f"   Tipo: {result.get('tipo')}")
    print(f"   Fuente: {result.get('fuente_datos')}")
    return True

def test_body_con_mensaje():
    """Test con mensaje en body JSON"""
    
    print("\n🧪 TEST 2: Body con mensaje JSON")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        headers={
            "Content-Type": "application/json",
            "Session-ID": "test-session-json",
            "Agent-ID": "TestAgent"
        },
        json={"mensaje": "en qué quedamos"}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    # Verificar que haga MERGE
    if result.get("tipo") == "panel_inicial":
        print("❌ FALLÓ: Devolvió panel_inicial")
        return False
    
    if not result.get("total_merged"):
        print("⚠️  ADVERTENCIA: No hay total_merged en respuesta")
    
    print("✅ PASÓ: Procesó mensaje correctamente")
    print(f"   Fuente: {result.get('fuente_datos')}")
    print(f"   Docs vectoriales: {result.get('total_docs_semanticos', 0)}")
    print(f"   Docs cosmos: {result.get('total_docs_cosmos', 0)}")
    print(f"   Total merged: {result.get('total_merged', 0)}")
    
    return True

def test_query_params():
    """Test con mensaje en query params"""
    
    print("\n🧪 TEST 3: Query params (GET style)")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/api/copiloto",
        params={"mensaje": "dame un resumen"},
        headers={
            "Session-ID": "test-session-params",
            "Agent-ID": "ParamsAgent"
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get("tipo") == "panel_inicial":
        print("❌ FALLÓ: Devolvió panel_inicial")
        return False
    
    print("✅ PASÓ: Procesó query params correctamente")
    return True

def test_merge_completo():
    """Test específico del MERGE Cosmos + Vectorial"""
    
    print("\n🧪 TEST 4: Verificar MERGE Cosmos + Vectorial")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/copiloto",
        headers={
            "Content-Type": "application/json",
            "Session-ID": "test-merge-session",
            "Agent-ID": "MergeAgent"
        },
        json={"mensaje": "en qué quedamos"}
    )
    
    result = response.json()
    
    checks = {
        "fuente_datos": result.get("fuente_datos") == "Cosmos+AISearch",
        "total_merged": result.get("total_merged", 0) > 0,
        "metadata_wrapper": result.get("metadata", {}).get("wrapper_aplicado"),
        "metadata_memoria": result.get("metadata", {}).get("memoria_aplicada"),
        "contexto_conversacion": bool(result.get("contexto_conversacion"))
    }
    
    print("Verificaciones:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}: {passed}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n✅ MERGE COMPLETO: Todos los checks pasaron")
    else:
        print("\n❌ MERGE INCOMPLETO: Algunos checks fallaron")
        print(f"\nRespuesta completa:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
    
    return all_passed

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE /api/copiloto")
    print("=" * 60)
    print("Simulando payloads de Foundry y otros clientes\n")
    
    results = []
    
    try:
        results.append(("Foundry payload", test_foundry_payload()))
        results.append(("Body JSON", test_body_con_mensaje()))
        results.append(("Query params", test_query_params()))
        results.append(("MERGE completo", test_merge_completo()))
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar a http://localhost:7071")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   cd copiloto-function && func start")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASARON")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests fallaron")
        exit(1)
