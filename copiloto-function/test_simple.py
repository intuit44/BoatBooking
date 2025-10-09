# -*- coding: utf-8 -*-
"""
Test simple para probar el endpoint ejecutar-cli localmente
"""

import json
import requests
import time

def test_ejecutar_cli():
    """Test básico del endpoint ejecutar-cli"""
    
    print("Iniciando test del endpoint /api/ejecutar-cli...")
    
    # URL local de Azure Functions
    base_url = "http://localhost:7071"
    endpoint = f"{base_url}/api/ejecutar-cli"
    
    # Test 1: Payload correcto
    print("\n1. Test payload correcto:")
    payload_correcto = {"comando": "storage account list"}
    print(f"   Enviando: {json.dumps(payload_correcto)}")
    
    try:
        response = requests.post(endpoint, json=payload_correcto, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ CORRECTO - Acepta comandos válidos")
        else:
            print(f"   ❌ ERROR - Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ ERROR de conexión: {e}")
    
    # Test 2: Payload incorrecto con "intencion"
    print("\n2. Test payload incorrecto (intencion):")
    payload_incorrecto = {"intencion": "buscar en bing"}
    print(f"   Enviando: {json.dumps(payload_incorrecto)}")
    
    try:
        response = requests.post(endpoint, json=payload_incorrecto, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 422:
            print("   ✅ CORRECTO - Rechaza intenciones con 422")
            result = response.json()
            print(f"   Mensaje: {result.get('error', 'Sin mensaje')}")
        else:
            print(f"   ❌ ERROR - Debería devolver 422, devolvió {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ ERROR de conexión: {e}")
    
    # Test 3: Payload vacío
    print("\n3. Test payload vacío:")
    payload_vacio = {}
    print(f"   Enviando: {json.dumps(payload_vacio)}")
    
    try:
        response = requests.post(endpoint, json=payload_vacio, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ CORRECTO - Rechaza payload vacío con 400")
        else:
            print(f"   ❌ ERROR - Debería devolver 400, devolvió {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR de conexión: {e}")
    
    print("\n" + "="*50)
    print("Test completado. Verificar logs del servidor para [DEBUG] messages.")

if __name__ == "__main__":
    test_ejecutar_cli()