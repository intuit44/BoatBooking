#!/usr/bin/env python3
"""
Test del endpoint diagnostico-recursos con memoria dual
Simula una llamada real al endpoint y valida la memoria
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno
try:
    settings_path = os.path.join(os.path.dirname(__file__), 'local.settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = value
        print("[INFO] Variables cargadas desde local.settings.json\n")
except Exception as e:
    print(f"[WARN] No se pudo cargar local.settings.json: {e}\n")

import azure.functions as func
from function_app import app
from services.memory_service import memory_service
from endpoints_search_memory import buscar_memoria_endpoint
import time

def test_diagnostico_con_memoria():
    print("=" * 80)
    print("TEST: Endpoint diagnostico-recursos con Memoria Dual")
    print("=" * 80)
    
    session_id = f"test_diag_{int(time.time())}"
    agent_id = "TestDiagAgent"
    
    # Crear request simulado (POST con recurso)
    print("\n[1/5] Creando request simulado...")
    body_data = json.dumps({"recurso": "test-resource", "profundidad": "basico"})
    req = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/diagnostico-recursos",
        headers={
            "Session-ID": session_id,
            "Agent-ID": agent_id
        },
        params={},
        body=body_data.encode('utf-8')
    )
    print(f"   Session-ID: {session_id}")
    print(f"   Agent-ID: {agent_id}")
    
    # Obtener función de app
    print("\n[2/5] Ejecutando endpoint diagnostico-recursos...")
    try:
        func_obj = None
        for f in app.get_functions():
            if f.get_function_name() == "diagnostico_recursos_http":
                func_obj = f
                break
        
        if not func_obj:
            print("   [FAIL] Función no encontrada en app")
            return False
        
        response = func_obj.get_user_function()(req)
        if response is None:
            print("   [FAIL] Endpoint devolvio None")
            return False
    except Exception as e:
        print(f"   [FAIL] Error ejecutando endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Parsear respuesta
    try:
        response_data = json.loads(response.get_body().decode())
    except Exception as e:
        print(f"   [FAIL] Error parseando respuesta: {e}")
        return False
    print(f"   Status: {response.status_code}")
    print(f"   OK: {response_data.get('ok', False)}")
    
    # Verificar que se guardó en Cosmos
    print("\n[3/5] Verificando guardado en Cosmos DB...")
    time.sleep(2)  # Esperar guardado
    
    historial = memory_service.get_session_history(session_id, limit=5)
    if historial:
        print(f"   [OK] Encontrados {len(historial)} eventos en Cosmos")
        evento = historial[0]
        print(f"   Evento ID: {evento.get('id', 'N/A')}")
        texto = str(evento.get('texto_semantico', 'N/A'))[:100]
        print(f"   Texto semantico: {texto.encode('ascii', 'ignore').decode('ascii')}...")
        cosmos_ok = True
    else:
        print("   [FAIL] No se encontraron eventos en Cosmos")
        cosmos_ok = False
    
    # Verificar indexación en AI Search
    print("\n[4/5] Verificando indexacion en AI Search...")
    time.sleep(2)  # Esperar indexación
    
    resultado_busqueda = buscar_memoria_endpoint({
        "query": "diagnostico recursos sistema",
        "session_id": session_id,
        "top": 5
    })
    
    if resultado_busqueda.get("exito"):
        docs = resultado_busqueda.get("documentos", [])
        print(f"   [OK] Busqueda vectorial: {len(docs)} documentos")
        if docs:
            print(f"   Documento: {docs[0].get('id', 'N/A')}")
            print(f"   Score: {docs[0].get('score', 'N/A')}")
        ai_search_ok = len(docs) > 0
    else:
        print(f"   [FAIL] Busqueda fallo: {resultado_busqueda.get('error')}")
        ai_search_ok = False
    
    # Segunda llamada para verificar recuperación de memoria
    print("\n[5/5] Segunda llamada para verificar recuperacion de memoria...")
    body_data2 = json.dumps({"recurso": "test-resource-2", "profundidad": "basico"})
    req2 = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/diagnostico-recursos",
        headers={
            "Session-ID": session_id,
            "Agent-ID": agent_id
        },
        params={},
        body=body_data2.encode('utf-8')
    )
    
    response2 = func_obj.get_user_function()(req2)
    response_data2 = json.loads(response2.get_body().decode())
    
    # Verificar metadata de memoria
    metadata = response_data2.get("metadata", {})
    memoria_aplicada = metadata.get("memoria_aplicada", False)
    
    if memoria_aplicada:
        print("   [OK] Memoria aplicada en segunda llamada")
        print(f"   Interacciones previas: {metadata.get('interacciones_previas', 0)}")
    else:
        print("   [WARN] Memoria no aplicada en segunda llamada")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN:")
    print("=" * 80)
    print(f"1. Endpoint ejecutado:        [OK]")
    print(f"2. Guardado en Cosmos DB:     {'[OK]' if cosmos_ok else '[FAIL]'}")
    print(f"3. Indexado en AI Search:     {'[OK]' if ai_search_ok else '[FAIL]'}")
    print(f"4. Memoria recuperada:        {'[OK]' if memoria_aplicada else '[FAIL]'}")
    
    print("\n" + "=" * 80)
    print("UBICACION DE LA LOGICA:")
    print("=" * 80)
    print("Consulta memoria:  endpoints/diagnostico_recursos.py (linea 38)")
    print("Aplica memoria:    endpoints/diagnostico_recursos.py (linea 210)")
    print("Registra llamada:  endpoints/diagnostico_recursos.py (linea 217)")
    print("Indexa AI Search:  services/memory_service.py (linea 127)")
    
    all_ok = cosmos_ok and ai_search_ok and memoria_aplicada
    
    if all_ok:
        print("\n[SUCCESS] Endpoint modular con memoria dual funcionando correctamente")
    else:
        print("\n[PARTIAL] Algunas funcionalidades no estan completas")
    
    return all_ok

if __name__ == "__main__":
    try:
        success = test_diagnostico_con_memoria()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
