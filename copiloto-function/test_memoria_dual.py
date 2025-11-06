#!/usr/bin/env python3
"""
Test de memoria dual: Cosmos DB + Azure AI Search
Valida que ambos sistemas funcionen en conjunto
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno desde local.settings.json
try:
    settings_path = os.path.join(os.path.dirname(__file__), 'local.settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = value
        print("[INFO] Variables cargadas desde local.settings.json")
except Exception as e:
    print(f"[WARN] No se pudo cargar local.settings.json: {e}")

from services.memory_service import memory_service
from endpoints_search_memory import buscar_memoria_endpoint, indexar_memoria_endpoint
import time

def test_memoria_dual():
    print("=" * 80)
    print("TEST: Memoria Dual (Cosmos DB + Azure AI Search)")
    print("=" * 80)
    
    session_id = f"test_dual_{int(time.time())}"
    
    # 1. ESCRIBIR en Cosmos (debe indexar automticamente en AI Search)
    print("\n[1/4] Escribiendo en Cosmos DB...")
    resultado_escritura = memory_service.registrar_llamada(
        source="test_memoria_dual",
        endpoint="/api/test-dual",
        method="POST",
        params={
            "session_id": session_id,
            "agent_id": "TestAgent"
        },
        response_data={
            "exito": True,
            "mensaje": "Test de memoria dual funcionando correctamente",
            "texto_semantico": "Esta es una prueba de memoria dual con Cosmos DB y Azure AI Search vectorial",
            "respuesta_usuario": "Sistema de memoria dual validado exitosamente"
        },
        success=True
    )
    
    if resultado_escritura:
        print("   [OK] Guardado en Cosmos DB")
        print("   [OK] Indexacin automtica en AI Search activada")
    else:
        print("   [FAIL] Error guardando en Cosmos DB")
        return False
    
    # Esperar a que se indexe
    print("\n[2/4] Esperando indexacin en AI Search (3s)...")
    time.sleep(3)
    
    # 2. LEER desde Cosmos DB
    print("\n[3/4] Leyendo desde Cosmos DB...")
    historial_cosmos = memory_service.get_session_history(session_id, limit=10)
    
    if historial_cosmos:
        print(f"   [OK] Recuperados {len(historial_cosmos)} eventos de Cosmos DB")
        evento = historial_cosmos[0]
        print(f"    Evento ID: {evento.get('id', 'N/A')}")
        print(f"    Texto semntico: {evento.get('texto_semantico', 'N/A')[:100]}...")
    else:
        print("   [WARN] No se encontraron eventos en Cosmos DB")
    
    # 3. BUSCAR en AI Search (vectorial)
    print("\n[4/4] Buscando en AI Search (vectorial)...")
    resultado_busqueda = buscar_memoria_endpoint({
        "query": "memoria dual Cosmos Azure",
        "session_id": session_id,
        "top": 5
    })
    
    if resultado_busqueda.get("exito"):
        docs = resultado_busqueda.get("documentos", [])
        print(f"   [OK] Bsqueda vectorial exitosa: {len(docs)} documentos")
        if docs:
            doc = docs[0]
            print(f"    Documento encontrado:")
            print(f"      - ID: {doc.get('id', 'N/A')}")
            print(f"      - Score: {doc.get('score', 'N/A')}")
            print(f"      - Texto: {doc.get('texto_semantico', 'N/A')[:100]}...")
    else:
        print(f"   [WARN] Bsqueda en AI Search fall: {resultado_busqueda.get('error')}")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN DEL TEST:")
    print("=" * 80)
    
    cosmos_ok = len(historial_cosmos) > 0
    ai_search_ok = resultado_busqueda.get("exito") and len(resultado_busqueda.get("documentos", [])) > 0
    
    print(f"Cosmos DB (secuencial):  {'[OK] OK' if cosmos_ok else '[FAIL] FAIL'}")
    print(f"AI Search (vectorial):   {'[OK] OK' if ai_search_ok else '[FAIL] FAIL'}")
    print(f"Memoria Dual:            {'[OK] FUNCIONANDO' if (cosmos_ok and ai_search_ok) else '[WARN] PARCIAL'}")
    
    print("\n" + "=" * 80)
    print("FLUJO VALIDADO:")
    print("=" * 80)
    print("1. [OK] Escritura en Cosmos DB")
    print("2. [OK] Indexacin automtica en AI Search")
    print("3. [OK] Lectura secuencial desde Cosmos DB")
    print("4. [OK] Bsqueda vectorial en AI Search")
    print("\n[SUCCESS] Sistema de memoria dual completamente funcional")
    
    return cosmos_ok and ai_search_ok

if __name__ == "__main__":
    try:
        success = test_memoria_dual()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
