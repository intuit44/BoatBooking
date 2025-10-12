#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de diagnóstico para verificar si el wrapper de memoria se está aplicando correctamente
"""

import requests
import json
import time
from datetime import datetime

def test_wrapper_diagnostico():
    """
    Prueba específica para verificar si el wrapper de memoria está funcionando
    """
    
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    print("DIAGNOSTICO DEL WRAPPER DE MEMORIA")
    print("=" * 50)
    
    # Test 1: Endpoint básico con parámetros de sesión explícitos
    print("\n1. Test con parámetros de sesión explícitos...")
    
    try:
        response = requests.get(
            f"{base_url}/api/status",
            params={
                "session_id": "test_session_123",
                "agent_id": "DiagnosticAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si tiene metadata de memoria
            has_memory_metadata = False
            wrapper_applied = False
            
            if "metadata" in data:
                if "session_info" in data["metadata"]:
                    has_memory_metadata = True
                    session_info = data["metadata"]["session_info"]
                    print(f"   ✅ Session ID detectado: {session_info.get('session_id')}")
                    print(f"   ✅ Agent ID detectado: {session_info.get('agent_id')}")
                
                if data["metadata"].get("wrapper_aplicado"):
                    wrapper_applied = True
                    print("   ✅ Wrapper aplicado confirmado")
                
                if data["metadata"].get("memoria_disponible"):
                    print("   ✅ Memoria disponible confirmada")
            
            if has_memory_metadata and wrapper_applied:
    print("   WRAPPER FUNCIONANDO CORRECTAMENTE")
            else:
                print("   ❌ WRAPPER NO DETECTADO")
                print(f"   📋 Metadata completa: {json.dumps(data.get('metadata', {}), indent=2)}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    # Test 2: Endpoint con POST y body JSON
    print("\n2. Test con POST y session_id en body...")
    
    try:
        response = requests.post(
            f"{base_url}/api/ejecutar",
            json={
                "intencion": "dashboard",
                "session_id": "test_post_session_456",
                "agent_id": "PostTestAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "metadata" in data and "session_info" in data["metadata"]:
                session_info = data["metadata"]["session_info"]
                print(f"   ✅ POST Session ID: {session_info.get('session_id')}")
                print(f"   ✅ POST Agent ID: {session_info.get('agent_id')}")
                
                if data["metadata"].get("wrapper_aplicado"):
                    print("   ✅ Wrapper aplicado en POST")
                else:
                    print("   ❌ Wrapper NO aplicado en POST")
            else:
                print("   ❌ No se detectó metadata de memoria en POST")
        else:
            print(f"   ❌ Error HTTP en POST: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error en POST: {e}")
    
    # Test 3: Endpoint con headers
    print("\n3. Test con headers X-Session-ID...")
    
    try:
        response = requests.get(
            f"{base_url}/api/listar-blobs",
            headers={
                "X-Session-ID": "header_session_789",
                "X-Agent-ID": "HeaderTestAgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "metadata" in data and "session_info" in data["metadata"]:
                session_info = data["metadata"]["session_info"]
                print(f"   ✅ Header Session ID: {session_info.get('session_id')}")
                print(f"   ✅ Header Agent ID: {session_info.get('agent_id')}")
                
                if data["metadata"].get("wrapper_aplicado"):
                    print("   ✅ Wrapper aplicado con headers")
                else:
                    print("   ❌ Wrapper NO aplicado con headers")
            else:
                print("   ❌ No se detectó metadata de memoria con headers")
        else:
            print(f"   ❌ Error HTTP con headers: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error con headers: {e}")
    
    # Test 4: Verificar auto-generación de session_id
    print("\n4. Test de auto-generación de session_id...")
    
    try:
        response = requests.get(
            f"{base_url}/api/status",
            headers={
                "User-Agent": "TestAgent/1.0"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "metadata" in data and "session_info" in data["metadata"]:
                session_info = data["metadata"]["session_info"]
                session_id = session_info.get('session_id', '')
                
                if session_id.startswith('auto_'):
                    print(f"   ✅ Auto-generación funcionando: {session_id}")
                else:
                    print(f"   ⚠️ Session ID no auto-generado: {session_id}")
                    
                if data["metadata"].get("wrapper_aplicado"):
                    print("   ✅ Wrapper aplicado en auto-generación")
                else:
                    print("   ❌ Wrapper NO aplicado en auto-generación")
            else:
                print("   ❌ No se detectó metadata en auto-generación")
        else:
            print(f"   ❌ Error HTTP en auto-generación: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error en auto-generación: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTICO COMPLETADO")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_wrapper_diagnostico()