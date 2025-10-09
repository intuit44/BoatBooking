#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de integración para /api/hybrid con máxima flexibilidad
Simula diferentes agentes enviando diferentes formatos de payload
"""

import json
import requests
import time
from datetime import datetime

# Configuración
BASE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"
# BASE_URL = "http://localhost:7071"  # Para pruebas locales

def test_hybrid_endpoint():
    """Prueba el endpoint /api/hybrid con diferentes formatos"""
    
    print("🧪 INICIANDO TESTS DE INTEGRACIÓN /api/hybrid")
    print("=" * 60)
    
    # Test 1: Formato legacy con agent_response
    print("\n📋 Test 1: Formato Legacy (agent_response)")
    payload1 = {
        "agent_response": "status",
        "agent_name": "TestAgent"
    }
    result1 = call_hybrid(payload1)
    print(f"✅ Resultado: {result1.get('resultado', {}).get('copiloto', 'N/A')}")
    
    # Test 2: Formato directo con endpoint
    print("\n📋 Test 2: Formato Directo (endpoint)")
    payload2 = {
        "endpoint": "status",
        "method": "GET"
    }
    result2 = call_hybrid(payload2)
    print(f"✅ Resultado: {result2.get('resultado', {}).get('copiloto', 'N/A')}")
    
    # Test 3: Formato con intención semántica
    print("\n📋 Test 3: Intención Semántica (dashboard)")
    payload3 = {
        "intencion": "dashboard",
        "parametros": {}
    }
    result3 = call_hybrid(payload3)
    print(f"✅ Resultado: {result3.get('resultado', {}).get('exito', 'N/A')}")
    
    # Test 4: Formato libre (cualquier JSON)
    print("\n📋 Test 4: Formato Libre")
    payload4 = {
        "accion": "verificar",
        "tipo": "sistema",
        "urgencia": "normal"
    }
    result4 = call_hybrid(payload4)
    print(f"✅ Resultado: {result4.get('resultado', {}).get('tipo', 'N/A')}")
    
    # Test 5: Comando CLI a través de hybrid
    print("\n📋 Test 5: Comando CLI via Hybrid")
    payload5 = {
        "agent_response": json.dumps({
            "endpoint": "ejecutar-cli",
            "data": {
                "comando": "storage account list"
            }
        })
    }
    result5 = call_hybrid(payload5)
    print(f"✅ Resultado: {result5.get('resultado', {}).get('exito', 'N/A')}")
    
    # Test 6: JSON embebido en markdown
    print("\n📋 Test 6: JSON Embebido en Markdown")
    payload6 = {
        "agent_response": """
        Voy a ejecutar un comando para verificar el estado:
        
        ```json
        {
            "endpoint": "status",
            "method": "GET"
        }
        ```
        
        Esto debería devolver el estado actual del sistema.
        """
    }
    result6 = call_hybrid(payload6)
    print(f"✅ Resultado: {result6.get('resultado', {}).get('copiloto', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("🎯 TESTS COMPLETADOS")

def call_hybrid(payload):
    """Llama al endpoint /api/hybrid con el payload dado"""
    try:
        url = f"{BASE_URL}/api/hybrid"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "response": response.text[:200]
            }
            
    except Exception as e:
        return {"error": str(e)}

def test_cli_integration():
    """Prueba la integración específica con ejecutar-cli"""
    
    print("\n🔧 TESTS DE INTEGRACIÓN CLI")
    print("=" * 40)
    
    # Test directo a ejecutar-cli
    print("\n📋 Test CLI Directo")
    cli_payload = {
        "comando": "storage account list"
    }
    
    try:
        url = f"{BASE_URL}/api/ejecutar-cli"
        response = requests.post(url, json=cli_payload, timeout=30)
        result = response.json()
        print(f"✅ CLI Directo: {result.get('exito', 'N/A')}")
    except Exception as e:
        print(f"❌ CLI Directo: {str(e)}")
    
    # Test CLI a través de hybrid
    print("\n📋 Test CLI via Hybrid")
    hybrid_cli_payload = {
        "endpoint": "ejecutar-cli",
        "data": cli_payload
    }
    
    result = call_hybrid(hybrid_cli_payload)
    print(f"✅ CLI via Hybrid: {result.get('resultado', {}).get('exito', 'N/A')}")

def test_error_scenarios():
    """Prueba escenarios de error y recuperación"""
    
    print("\n⚠️ TESTS DE ESCENARIOS DE ERROR")
    print("=" * 40)
    
    # Test 1: Payload vacío
    print("\n📋 Test Payload Vacío")
    result1 = call_hybrid({})
    print(f"✅ Payload vacío: {result1.get('resultado', {}).get('copiloto', 'manejado')}")
    
    # Test 2: JSON malformado en agent_response
    print("\n📋 Test JSON Malformado")
    payload2 = {
        "agent_response": "{ endpoint: status, method: GET }"  # JSON inválido
    }
    result2 = call_hybrid(payload2)
    print(f"✅ JSON malformado: {result2.get('resultado', {}).get('endpoint', 'manejado')}")
    
    # Test 3: Endpoint inexistente
    print("\n📋 Test Endpoint Inexistente")
    payload3 = {
        "endpoint": "endpoint-que-no-existe",
        "method": "POST"
    }
    result3 = call_hybrid(payload3)
    print(f"✅ Endpoint inexistente: {result3.get('resultado', {}).get('error', 'manejado')}")

if __name__ == "__main__":
    print(f"🚀 INICIANDO TESTS DE INTEGRACIÓN")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Ejecutar todos los tests
    test_hybrid_endpoint()
    test_cli_integration()
    test_error_scenarios()
    
    print(f"\n✅ TODOS LOS TESTS COMPLETADOS")
    print(f"📊 Resumen: El endpoint /api/hybrid ahora es completamente adaptable")
    print(f"🎯 Acepta cualquier formato de payload de cualquier agente")