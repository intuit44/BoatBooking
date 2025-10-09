#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de validación para ejecutar_cli_http
Verifica que el endpoint rechace payloads incorrectos y acepte los correctos
"""

import requests
import json
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/ejecutar-cli"

def test_payload_correcto():
    """Test 1: Payload correcto con comando"""
    print("Test 1: Payload correcto")
    
    payload = {"comando": "az storage account list"}
    
    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code in [200, 500]:  # 500 es OK si Azure CLI falla
            print("   ✅ PASS - Payload correcto aceptado")
            return True
        else:
            print("   ❌ FAIL - Payload correcto rechazado")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_payload_incorrecto_intencion():
    """Test 2: Payload incorrecto con intencion"""
    print("\nTest 2: Payload incorrecto (intencion)")
    
    payload = {"intencion": "buscar en bing"}
    
    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 422:
            print("   ✅ PASS - Payload con intencion rechazado correctamente (422)")
            return True
        else:
            print(f"   ❌ FAIL - Esperaba 422, recibió {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_payload_vacio():
    """Test 3: Payload vacío"""
    print("\nTest 3: Payload vacio")
    
    payload = {}
    
    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 400:
            print("   ✅ PASS - Payload vacío rechazado correctamente (400)")
            return True
        else:
            print(f"   ❌ FAIL - Esperaba 400, recibió {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_payload_mixto():
    """Test 4: Payload mixto con ambos campos"""
    print("\nTest 4: Payload mixto (comando + intencion)")
    
    payload = {
        "comando": "az storage account list",
        "intencion": "buscar en bing"
    }
    
    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        # Debe priorizar comando y funcionar
        if response.status_code in [200, 500]:
            print("   ✅ PASS - Payload mixto procesado (prioriza comando)")
            return True
        else:
            print(f"   ❌ FAIL - Payload mixto falló inesperadamente")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_servidor_activo():
    """Verifica que el servidor esté activo"""
    print("Verificando servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            print("   ✅ Servidor activo")
            return True
        else:
            print(f"   ⚠️ Servidor responde pero con status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Servidor no disponible: {e}")
        return False

def main():
    """Ejecuta todos los tests"""
    print("=" * 60)
    print("TEST DE VALIDACION - ejecutar_cli_http")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Endpoint: {BASE_URL}{ENDPOINT}")
    
    # Verificar servidor
    if not test_servidor_activo():
        print("\nABORTANDO: Servidor no disponible")
        print("Asegurate de que func start este ejecutandose")
        sys.exit(1)
    
    # Ejecutar tests
    tests = [
        test_payload_correcto,
        test_payload_incorrecto_intencion,
        test_payload_vacio,
        test_payload_mixto
    ]
    
    resultados = []
    for test in tests:
        resultado = test()
        resultados.append(resultado)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(resultados)
    total = len(resultados)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\nTODOS LOS TESTS PASARON")
        print("La validacion del endpoint funciona correctamente")
    else:
        print("\nALGUNOS TESTS FALLARON")
        print("Revisar la implementacion del endpoint")
    
    print("\nProximos pasos:")
    print("   1. Si todos pasaron: La correccion esta funcionando")
    print("   2. Si fallo Test 2: Verificar validacion de 'intencion'")
    print("   3. Si fallo Test 3: Verificar validacion de payload vacio")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)