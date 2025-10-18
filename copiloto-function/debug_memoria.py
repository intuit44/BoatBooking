#!/usr/bin/env python3
"""
Script para debuggear específicamente el problema del texto_semantico vacío
"""
import json
import logging
from services.memory_service import memory_service

def test_cosmos_direct():
    """Test directo de escritura y lectura en Cosmos"""
    print("TEST 1: Escritura directa en Cosmos")
    
    # Test data con texto_semantico explícito
    test_data = {
        "endpoint": "/api/test-debug",
        "success": True,
        "mensaje": "Test de debug directo",
        "texto_semantico": "TEST: Interacción de debug ejecutada por test-agent. Éxito: ✅. Mensaje: Test directo."
    }
    
    # Usar log_event directamente
    result = memory_service.log_event("debug_test", test_data, session_id="debug-session-001")
    print(f"Resultado escritura: {'OK' if result else 'FAIL'}")
    
    # Leer inmediatamente
    print("\nTEST 2: Lectura inmediata")
    history = memory_service.get_session_history("debug-session-001", limit=5)
    
    if history:
        latest = history[0]
        print(f"Documento encontrado: {latest.get('id', 'N/A')}")
        print(f"Texto semantico guardado: '{latest.get('texto_semantico', 'VACIO')}'")
        print(f"Data keys: {list(latest.get('data', {}).keys())}")
        
        # Verificar si está en data
        data_texto = latest.get('data', {}).get('texto_semantico', 'NO ENCONTRADO EN DATA')
        print(f"Texto en data: '{data_texto}'")
        
        # Mostrar documento completo (truncado)
        print(f"Documento completo: {json.dumps(latest, ensure_ascii=False, indent=2)[:500]}...")
    else:
        print("No se encontraron documentos")

def test_registrar_llamada():
    """Test específico del método registrar_llamada"""
    print("\nTEST 3: Metodo registrar_llamada")
    
    # Simular parámetros como los que llegan del wrapper
    params = {
        "session_id": "debug-session-002",
        "agent_id": "debug-agent",
        "limit": 1
    }
    
    response_data = {
        "exito": True,
        "mensaje": "Test de registrar_llamada",
        "interacciones": [],
        "total": 0
    }
    
    # Llamar registrar_llamada directamente
    result = memory_service.registrar_llamada(
        source="debug_test",
        endpoint="/api/debug-registrar",
        method="GET",
        params=params,
        response_data=response_data,
        success=True
    )
    
    print(f"Resultado registrar_llamada: {'OK' if result else 'FAIL'}")
    
    # Verificar qué se guardó
    history = memory_service.get_session_history("debug-session-002", limit=5)
    if history:
        latest = history[0]
        print(f"Texto semantico: '{latest.get('texto_semantico', 'VACIO')}'")
        print(f"Event type: {latest.get('event_type', 'N/A')}")
        
        # Verificar estructura de data
        data = latest.get('data', {})
        print(f"Data texto_semantico: '{data.get('texto_semantico', 'NO EN DATA')}'")
        print(f"Data keys: {list(data.keys())}")
    else:
        print("No se encontro el documento guardado")

def test_wrapper_simulation():
    """Test simulando exactamente lo que hace el wrapper"""
    print("\nTEST 4: Simulacion del wrapper completo")
    
    # Simular response_data como lo genera historial-interacciones
    response_data = {
        "exito": True,
        "interacciones": [{"numero": 1, "timestamp": "2025-10-17T23:36:53.531177"}],
        "total": 1,
        "session_id": "debug-session-003",
        "mensaje": "Se encontraron 1 interacciones recientes"
    }
    
    # Agregar texto_semantico como lo hace el wrapper
    response_data["texto_semantico"] = (
        f"Interacción en '/api/historial-interacciones' ejecutada por debug-agent. "
        f"Éxito: ✅. Mensaje: {response_data.get('mensaje', 'sin mensaje')}."
    )
    
    print(f"Texto semantico generado: '{response_data['texto_semantico']}'")
    
    # Registrar como lo hace el wrapper
    result = memory_service.registrar_llamada(
        source="historial_interacciones",
        endpoint="/api/historial-interacciones",
        method="GET",
        params={"session_id": "debug-session-003", "agent_id": "debug-agent"},
        response_data=response_data,
        success=True
    )
    
    print(f"Resultado wrapper simulation: {'OK' if result else 'FAIL'}")
    
    # Verificar inmediatamente
    history = memory_service.get_session_history("debug-session-003", limit=5)
    if history:
        latest = history[0]
        print(f"Texto semantico guardado: '{latest.get('texto_semantico', 'VACIO')}'")
        
        # Verificar si el texto está en diferentes lugares
        data_texto = latest.get('data', {}).get('texto_semantico', 'NO EN DATA')
        response_texto = latest.get('data', {}).get('response_data', {}).get('texto_semantico', 'NO EN RESPONSE_DATA')
        
        print(f"En data: '{data_texto}'")
        print(f"En response_data: '{response_texto}'")
        
        # Mostrar estructura completa de data
        data = latest.get('data', {})
        print(f"Estructura data: {json.dumps(data, ensure_ascii=False, indent=2)[:800]}...")
    else:
        print("No se encontro el documento")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Iniciando debug de memoria semantica...")
    
    test_cosmos_direct()
    test_registrar_llamada() 
    test_wrapper_simulation()
    
    print("\nDebug completado")