#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Endpoints de Búsqueda - Simula requests desde Foundry
"""

import json
import requests
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:7071"  # Cambiar a URL de Azure en producción

def test_buscar_memoria():
    """Test del endpoint /api/buscar-memoria"""
    
    print("\n" + "="*60)
    print("TEST: /api/buscar-memoria")
    print("="*60 + "\n")
    
    # Payload simulando Foundry
    payload = {
        "query": "errores en ejecutar_cli",
        "agent_id": "Agent914",
        "top": 5
    }
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/buscar-memoria",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response ({response.status_code}):")
        result = response.json()
        print(json.dumps(result, indent=2, default=str))
        
        if result.get("exito"):
            print(f"\n✅ Búsqueda exitosa: {result.get('total', 0)} documentos")
        else:
            print(f"\n⚠️ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_indexar_memoria():
    """Test del endpoint /api/indexar-memoria"""
    
    print("\n" + "="*60)
    print("TEST: /api/indexar-memoria")
    print("="*60 + "\n")
    
    # Documento de prueba
    test_doc = {
        "id": f"test_foundry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "agent_id": "Agent914",
        "session_id": "foundry_test_session",
        "endpoint": "/api/ejecutar-cli",
        "timestamp": datetime.utcnow().isoformat(),
        "tipo": "test_foundry",
        "texto_semantico": "Test de indexación desde Foundry usando Managed Identity",
        "vector": [0.1] * 1536,
        "exito": True
    }
    
    payload = {
        "documentos": [test_doc]
    }
    
    print("📤 Request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/indexar-memoria",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response ({response.status_code}):")
        result = response.json()
        print(json.dumps(result, indent=2, default=str))
        
        if result.get("exito"):
            print(f"\n✅ Indexación exitosa: {result.get('documentos_subidos', 0)} documentos")
        else:
            print(f"\n⚠️ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_flujo_completo():
    """Test del flujo completo: indexar y buscar"""
    
    print("\n" + "="*60)
    print("TEST: FLUJO COMPLETO (Indexar → Buscar)")
    print("="*60 + "\n")
    
    # 1. Indexar documento
    print("1️⃣ Indexando documento...")
    doc_id = f"flujo_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    payload_indexar = {
        "documentos": [{
            "id": doc_id,
            "agent_id": "Agent914",
            "session_id": "flujo_test",
            "endpoint": "/api/test",
            "timestamp": datetime.utcnow().isoformat(),
            "tipo": "flujo_completo",
            "texto_semantico": "Documento de prueba para validar flujo completo con Managed Identity",
            "vector": [0.2] * 1536,
            "exito": True
        }]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/indexar-memoria",
            json=payload_indexar,
            headers={"Content-Type": "application/json"}
        )
        
        if response.json().get("exito"):
            print("   ✅ Documento indexado")
        else:
            print(f"   ❌ Error indexando: {response.json().get('error')}")
            return
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return
    
    # 2. Esperar indexación
    print("\n2️⃣ Esperando indexación...")
    import time
    time.sleep(3)
    
    # 3. Buscar documento
    print("\n3️⃣ Buscando documento...")
    payload_buscar = {
        "query": "flujo completo Managed Identity",
        "agent_id": "Agent914",
        "top": 10
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/buscar-memoria",
            json=payload_buscar,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        if result.get("exito"):
            total = result.get("total", 0)
            print(f"   ✅ Búsqueda exitosa: {total} documentos")
            
            # Verificar si encontró nuestro documento
            found = any(doc.get("id") == doc_id for doc in result.get("documentos", []))
            if found:
                print(f"   ✅ Documento encontrado: {doc_id}")
            else:
                print(f"   ⚠️ Documento no encontrado aún (indexación pendiente)")
        else:
            print(f"   ⚠️ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n✅ Flujo completo ejecutado")

if __name__ == "__main__":
    print("\n🚀 Iniciando tests de endpoints...\n")
    print("⚠️ Asegúrate de que la Function App esté corriendo:")
    print("   func start\n")
    
    input("Presiona ENTER para continuar...")
    
    # Ejecutar tests
    test_buscar_memoria()
    test_indexar_memoria()
    test_flujo_completo()
    
    print("\n✅ Tests completados\n")
