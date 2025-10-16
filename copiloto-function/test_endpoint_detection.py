#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de detección automática de endpoints
Verifica que el sistema detecte correctamente los endpoints y los registre en Cosmos DB
"""

import json
import requests
import time
from datetime import datetime

def test_endpoint_detection():
    """Prueba la detección automática de endpoints"""
    
    base_url = "http://localhost:7071"
    
    # Test cases con diferentes endpoints
    test_cases = [
        {
            "name": "Historial Interacciones",
            "url": f"{base_url}/api/historial-interacciones",
            "method": "GET",
            "headers": {
                "Session-ID": "test_endpoint_detection_001",
                "Agent-ID": "TestAgent"
            },
            "expected_endpoint": "historial_interacciones"
        },
        {
            "name": "Status",
            "url": f"{base_url}/api/status",
            "method": "GET", 
            "headers": {
                "Session-ID": "test_endpoint_detection_001",
                "Agent-ID": "TestAgent"
            },
            "expected_endpoint": "status"
        },
        {
            "name": "Copiloto",
            "url": f"{base_url}/api/copiloto",
            "method": "GET",
            "headers": {
                "Session-ID": "test_endpoint_detection_001", 
                "Agent-ID": "TestAgent"
            },
            "expected_endpoint": "copiloto"
        },
        {
            "name": "Listar Blobs",
            "url": f"{base_url}/api/listar-blobs",
            "method": "GET",
            "headers": {
                "Session-ID": "test_endpoint_detection_001",
                "Agent-ID": "TestAgent"
            },
            "expected_endpoint": "listar_blobs"
        }
    ]
    
    print("🧪 Iniciando test de detección automática de endpoints...")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        print(f"   URL: {test_case['url']}")
        print(f"   Expected endpoint: {test_case['expected_endpoint']}")
        
        try:
            # Hacer request
            response = requests.request(
                method=test_case["method"],
                url=test_case["url"],
                headers=test_case["headers"],
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            # Verificar respuesta
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Buscar endpoint detectado en metadata
                    endpoint_detectado = None
                    if "metadata" in data:
                        endpoint_detectado = data["metadata"].get("endpoint_detectado")
                    
                    if endpoint_detectado:
                        print(f"   ✅ Endpoint detectado: {endpoint_detectado}")
                        
                        if endpoint_detectado == test_case["expected_endpoint"]:
                            print(f"   ✅ CORRECTO: Coincide con esperado")
                            results.append({"test": test_case["name"], "status": "PASS", "detected": endpoint_detectado})
                        else:
                            print(f"   ❌ ERROR: Esperado {test_case['expected_endpoint']}, obtenido {endpoint_detectado}")
                            results.append({"test": test_case["name"], "status": "FAIL", "detected": endpoint_detectado, "expected": test_case["expected_endpoint"]})
                    else:
                        print(f"   ⚠️  WARNING: No se encontró endpoint_detectado en metadata")
                        results.append({"test": test_case["name"], "status": "WARNING", "detected": "not_found"})
                        
                except json.JSONDecodeError:
                    print(f"   ❌ ERROR: Respuesta no es JSON válido")
                    results.append({"test": test_case["name"], "status": "ERROR", "error": "invalid_json"})
            else:
                print(f"   ❌ ERROR: Status code {response.status_code}")
                results.append({"test": test_case["name"], "status": "ERROR", "error": f"status_{response.status_code}"})
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            results.append({"test": test_case["name"], "status": "EXCEPTION", "error": str(e)})
        
        # Pausa entre tests
        time.sleep(1)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS:")
    
    passed = len([r for r in results if r["status"] == "PASS"])
    failed = len([r for r in results if r["status"] in ["FAIL", "ERROR", "EXCEPTION"]])
    warnings = len([r for r in results if r["status"] == "WARNING"])
    
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"⚠️  WARNINGS: {warnings}")
    print(f"📈 SUCCESS RATE: {(passed / len(results)) * 100:.1f}%")
    
    # Detalles de fallos
    if failed > 0:
        print("\n🔍 DETALLES DE FALLOS:")
        for result in results:
            if result["status"] in ["FAIL", "ERROR", "EXCEPTION"]:
                print(f"   - {result['test']}: {result['status']}")
                if "detected" in result:
                    print(f"     Detectado: {result['detected']}")
                if "expected" in result:
                    print(f"     Esperado: {result['expected']}")
                if "error" in result:
                    print(f"     Error: {result['error']}")
    
    print("\n🔍 Verificar en Cosmos DB que los registros tengan el endpoint correcto")
    print("   Query sugerida: SELECT * FROM c WHERE c.session_id = 'test_endpoint_detection_001' ORDER BY c._ts DESC")
    
    return results

def test_historial_specific():
    """Test específico para el endpoint historial-interacciones"""
    
    print("\n🎯 TEST ESPECÍFICO: /api/historial-interacciones")
    print("=" * 50)
    
    url = "http://localhost:7071/api/historial-interacciones"
    headers = {
        "Session-ID": "test_deduplicado_001",
        "Agent-ID": "TestAgent"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Respuesta exitosa")
            print(f"Total interacciones: {data.get('total', 0)}")
            
            # Verificar que las interacciones tengan endpoint correcto
            interacciones = data.get("interacciones", [])
            
            if interacciones:
                print(f"\n📋 Verificando endpoints en {len(interacciones)} interacciones:")
                
                for i, interaccion in enumerate(interacciones[:5], 1):
                    endpoint = interaccion.get("endpoint", "unknown")
                    timestamp = interaccion.get("timestamp", "")
                    
                    if endpoint == "unknown":
                        print(f"   {i}. ❌ UNKNOWN - {timestamp}")
                    else:
                        print(f"   {i}. ✅ {endpoint} - {timestamp}")
            else:
                print("ℹ️  No hay interacciones en el historial")
                
            # Verificar metadata
            metadata = data.get("metadata", {})
            endpoint_detectado = metadata.get("endpoint_detectado")
            
            if endpoint_detectado:
                print(f"\n🎯 Endpoint detectado en esta llamada: {endpoint_detectado}")
                if endpoint_detectado == "historial_interacciones":
                    print("✅ CORRECTO: Endpoint detectado correctamente")
                else:
                    print(f"⚠️  INESPERADO: Se esperaba 'historial_interacciones', se obtuvo '{endpoint_detectado}'")
            else:
                print("⚠️  No se encontró endpoint_detectado en metadata")
        
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE DETECCIÓN DE ENDPOINTS")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test general
    results = test_endpoint_detection()
    
    # Test específico para historial
    test_historial_specific()
    
    print(f"\n🏁 Tests completados: {datetime.now().isoformat()}")