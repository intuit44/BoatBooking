#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que el fix del session_id funciona correctamente
"""

import json
import requests
import time

def test_session_id_consistency():
    """
    Prueba que el session_id se mantenga consistente y no genere fallbacks automáticos
    """
    
    # URL del endpoint
    url = "http://localhost:7071/api/revisar-correcciones"
    
    # Session ID de prueba
    test_session_id = "test_deduplicado_001"
    
    # Headers con session_id
    headers = {
        "Content-Type": "application/json",
        "Session-ID": test_session_id,
        "Agent-ID": "test_agent"
    }
    
    print("🧪 Iniciando test de consistencia de session_id...")
    print(f"📋 Session ID de prueba: {test_session_id}")
    
    # Realizar múltiples llamadas
    for i in range(3):
        print(f"\n🔄 Llamada {i+1}/3...")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"consulta": f"test consulta {i+1}"},
                timeout=30
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta exitosa")
                
                # Verificar metadata
                if "metadata" in data:
                    session_info = data["metadata"].get("session_info", {})
                    if session_info:
                        returned_session = session_info.get("session_id")
                        print(f"🔍 Session ID retornado: {returned_session}")
                        
                        if returned_session == test_session_id:
                            print("✅ Session ID preservado correctamente")
                        else:
                            print(f"❌ Session ID cambió: {test_session_id} -> {returned_session}")
                    else:
                        print("⚠️ No se encontró session_info en metadata")
                else:
                    print("⚠️ No se encontró metadata en respuesta")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error en llamada: {e}")
        
        # Esperar un poco entre llamadas
        time.sleep(1)
    
    print("\n🏁 Test completado")

def test_headers_vs_params():
    """
    Prueba que los headers tengan prioridad sobre los params
    """
    
    url = "http://localhost:7071/api/revisar-correcciones"
    
    # Session ID en headers (debe tener prioridad)
    headers_session = "test_headers_priority"
    params_session = "test_params_secondary"
    
    headers = {
        "Content-Type": "application/json",
        "Session-ID": headers_session,
        "Agent-ID": "test_agent"
    }
    
    # Enviar con session_id en ambos lugares
    payload = {
        "consulta": "test prioridad headers",
        "session_id": params_session  # Este NO debe usarse
    }
    
    print(f"\n🧪 Test de prioridad Headers vs Params...")
    print(f"📋 Headers Session-ID: {headers_session}")
    print(f"📋 Params session_id: {params_session}")
    print(f"🎯 Esperado: {headers_session} (headers debe ganar)")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "metadata" in data and "session_info" in data["metadata"]:
                returned_session = data["metadata"]["session_info"].get("session_id")
                print(f"🔍 Session ID retornado: {returned_session}")
                
                if returned_session == headers_session:
                    print("✅ Headers tiene prioridad correctamente")
                elif returned_session == params_session:
                    print("❌ Params tiene prioridad (incorrecto)")
                else:
                    print(f"⚠️ Session ID inesperado: {returned_session}")
            else:
                print("⚠️ No se encontró session_info en respuesta")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")

if __name__ == "__main__":
    print("🚀 Ejecutando tests de session_id fix...")
    
    # Test 1: Consistencia
    test_session_id_consistency()
    
    # Test 2: Prioridad headers vs params
    test_headers_vs_params()
    
    print("\n✅ Tests completados")