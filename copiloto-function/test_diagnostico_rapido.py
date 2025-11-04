#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rápido del endpoint /api/diagnostico con memoria"""

import requests
import json

BASE_URL = "http://localhost:7071"

def test_diagnostico_con_session():
    """Test con Session-ID"""
    print("\n🧪 Test: /api/diagnostico con Session-ID")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/api/diagnostico",
        headers={
            "Session-ID": "constant-session-id",
            "Agent-ID": "foundry-agent"
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Verificar metadata
    metadata = data.get("metadata", {})
    print(f"\n📊 Metadata:")
    print(f"  - wrapper_aplicado: {metadata.get('wrapper_aplicado')}")
    print(f"  - memoria_aplicada: {metadata.get('memoria_aplicada')}")
    print(f"  - memoria_global: {metadata.get('memoria_global')}")
    
    busqueda = metadata.get("busqueda_semantica", {})
    print(f"\n🔍 Búsqueda Semántica:")
    print(f"  - aplicada: {busqueda.get('aplicada')}")
    print(f"  - interacciones_encontradas: {busqueda.get('interacciones_encontradas', 0)}")
    print(f"  - endpoint_buscado: {busqueda.get('endpoint_buscado', 'N/A')}")
    
    if busqueda.get("resumen_contexto"):
        print(f"  - resumen: {busqueda['resumen_contexto'][:100]}...")
    
    # Verificar diagnóstico
    diagnostico = data.get("diagnostico", {})
    print(f"\n📈 Diagnóstico:")
    print(f"  - total_interacciones: {diagnostico.get('total_interacciones')}")
    print(f"  - tasa_exito: {diagnostico.get('metricas', {}).get('tasa_exito')}")
    
    # Resultado
    if metadata.get("memoria_aplicada"):
        print("\n✅ ÉXITO: Memoria aplicada correctamente")
        return True
    else:
        print("\n❌ FALLO: Memoria no aplicada")
        return False


def test_diagnostico_sin_session():
    """Test sin Session-ID"""
    print("\n🧪 Test: /api/diagnostico sin Session-ID")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/diagnostico")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"Message: {data.get('message')}")
    print(f"OK: {data.get('ok')}")
    
    metadata = data.get("metadata", {})
    print(f"\n📊 Metadata:")
    print(f"  - memoria_aplicada: {metadata.get('memoria_aplicada')}")
    
    busqueda = metadata.get("busqueda_semantica", {})
    print(f"  - busqueda_aplicada: {busqueda.get('aplicada')}")
    print(f"  - razon: {busqueda.get('razon', 'N/A')}")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 TEST RÁPIDO: /api/diagnostico")
    print("=" * 60)
    
    try:
        result1 = test_diagnostico_con_session()
        result2 = test_diagnostico_sin_session()
        
        print("\n" + "=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"{'✅' if result1 else '❌'} Test con Session-ID")
        print(f"{'✅' if result2 else '❌'} Test sin Session-ID")
        
        if result1:
            print("\n🎉 ¡Memoria semántica funcionando!")
        else:
            print("\n⚠️ Memoria semántica no aplicada")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
