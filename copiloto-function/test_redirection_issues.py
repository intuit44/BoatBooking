#!/usr/bin/env python3
"""
Script de diagnostico para detectar problemas de redireccion infinita y perdida de sesiones
"""
import requests
import json
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "http://localhost:7071"
TEST_SESSION_ID = "test_sesion_diagnostico_123"

def test_infinite_redirection():
    """Prueba 1: Detectar redireccion infinita en /api/revisar-correcciones"""
    print("\nPRUEBA 1: Detectando redireccion infinita")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/revisar-correcciones"
    headers = {
        "Session-ID": TEST_SESSION_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Hacer request con timeout corto para detectar loops
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            # Verificar si hay indicios de redireccion
            if "redirect" in str(data).lower() or "redirigir" in str(data).lower():
                print("POSIBLE REDIRECCION DETECTADA en respuesta")
                print(f"   Contenido: {json.dumps(data, indent=2)[:200]}...")
            else:
                print("No hay indicios de redireccion en respuesta")
        
        return True
        
    except requests.exceptions.Timeout:
        print("TIMEOUT - Posible redireccion infinita detectada")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_session_preservation():
    """Prueba 2: Verificar preservacion de Session-ID en redirecciones"""
    print("\nPRUEBA 2: Verificando preservacion de Session-ID")
    print("=" * 50)
    
    # Probar endpoint que podria causar redireccion
    url = f"{BASE_URL}/api/copiloto"
    headers = {
        "Session-ID": TEST_SESSION_ID,
        "Agent-ID": "test_agent_diagnostico"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si el Session-ID se preservo
            session_in_response = data.get("contexto_conversacion", {}).get("session_id", "")
            
            print(f"Session-ID enviado: {TEST_SESSION_ID}")
            print(f"Session-ID en respuesta: {session_in_response}")
            
            if TEST_SESSION_ID in session_in_response:
                print("Session-ID preservado correctamente")
                return True
            elif session_in_response.startswith("auto_"):
                print("Session-ID reemplazado por uno automatico")
                print(f"   Esto indica perdida de sesion en redireccion")
                return False
            else:
                print("Session-ID no encontrado en respuesta")
                return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_memory_cosmos_integration():
    """Prueba 3: Verificar integracion con Cosmos DB"""
    print("\nPRUEBA 3: Verificando integracion con Cosmos DB")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/historial-interacciones"
    headers = {
        "Session-ID": TEST_SESSION_ID
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Cosmos DB responde correctamente")
            print(f"   Interacciones encontradas: {len(data.get('interacciones', []))}")
            return True
        else:
            print(f"Cosmos DB respuesta no exitosa: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR en Cosmos DB: {str(e)}")
        return False

def main():
    """Ejecutar todas las pruebas de diagnostico"""
    print("DIAGNOSTICO DE PROBLEMAS DE REDIRECCION Y SESIONES")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Session ID: {TEST_SESSION_ID}")
    
    results = {
        "redirection_infinite": test_infinite_redirection(),
        "session_preservation": test_session_preservation(), 
        "cosmos_integration": test_memory_cosmos_integration()
    }
    
    print("\nRESUMEN DE DIAGNOSTICO")
    print("=" * 30)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    # Generar recomendaciones
    print("\nRECOMENDACIONES")
    print("=" * 20)
    
    if not results["redirection_infinite"]:
        print("1. Agregar guard clause en revisar_correcciones para evitar redireccion infinita")
        print("   Codigo sugerido:")
        print("   if req.url.endswith('/api/revisar-correcciones') and deteccion.get('redirigir'):")
        print("       if 'revisar-correcciones' in deteccion.get('endpoint_destino', ''):")
        print("           deteccion['redirigir'] = False")
    
    if not results["session_preservation"]:
        print("2. Asegurar propagacion de Session-ID en redirecciones")
        print("   Verificar que headers se propaguen en requests internos")
    
    if results["cosmos_integration"]:
        print("3. Cosmos DB funciona correctamente")
    else:
        print("3. Revisar configuracion de Cosmos DB")
    
    print(f"\nDiagnostico completado - {sum(results.values())}/3 pruebas exitosas")

if __name__ == "__main__":
    main()