#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de memoria de sesión - Verifica que los agentes recuerden interacciones previas
"""

import json
import requests
import time
import uuid
from datetime import datetime

def test_session_memory():
    """
    Prueba el sistema de memoria de sesión
    """
    
    # Configuración
    base_url = "http://localhost:7071"  # Cambiar según entorno
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    agent_id = "AzureSupervisor"
    
    print(f"🧪 Iniciando prueba de memoria de sesión")
    print(f"📋 Session ID: {session_id}")
    print(f"🤖 Agent ID: {agent_id}")
    print("=" * 70)
    
    # Test 1: Primera interacción (nueva sesión)
    print("\n📤 Test 1: Primera interacción (nueva sesión)")
    response1 = call_endpoint("/api/ejecutar", {
        "intencion": "dashboard",
        "session_id": session_id,
        "agent_id": agent_id,
        "parametros": {}
    })
    
    print_response("Primera llamada", response1)
    
    # Esperar un poco para que se registre en Cosmos
    time.sleep(2)
    
    # Test 2: Segunda interacción (debería recordar la primera)
    print("\n📤 Test 2: Segunda interacción (debería tener memoria)")
    response2 = call_endpoint("/api/ejecutar", {
        "intencion": "diagnosticar:completo", 
        "session_id": session_id,
        "agent_id": agent_id,
        "parametros": {}
    })
    
    print_response("Segunda llamada", response2)
    
    # Test 3: Tercera interacción con endpoint diferente
    print("\n📤 Test 3: Tercera interacción (hybrid endpoint)")
    response3 = call_endpoint("/api/hybrid", {
        "agent_response": "status",
        "session_id": session_id,
        "agent_id": agent_id
    })
    
    print_response("Tercera llamada", response3)
    
    # Test 4: Consulta directa de memoria
    print("\n📤 Test 4: Consulta directa de memoria de sesión")
    try:
        from services.session_memory import consultar_memoria_sesion
        memoria_directa = consultar_memoria_sesion(session_id, agent_id)
        print(f"📄 Memoria directa: {json.dumps(memoria_directa, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ Error consultando memoria directa: {e}")
    
    # Análisis de resultados
    print("\n" + "=" * 70)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("-" * 30)
    
    # Verificar si las respuestas incluyen información de memoria
    memoria_detectada = []
    
    for i, response in enumerate([response1, response2, response3], 1):
        if response and isinstance(response, dict):
            metadata = response.get("metadata", {})
            
            # Verificar indicadores de memoria
            memoria_disponible = metadata.get("memoria_disponible", False)
            session_info = metadata.get("session_info", {})
            memoria_sesion = metadata.get("memoria_sesion", {})
            contexto_memoria = response.get("contexto_memoria", "")
            
            memoria_detectada.append({
                "llamada": i,
                "memoria_disponible": memoria_disponible,
                "session_id_detectado": session_info.get("session_id") == session_id,
                "interacciones_previas": memoria_sesion.get("interacciones_previas", 0),
                "tiene_contexto": bool(contexto_memoria)
            })
            
            print(f"Llamada {i}:")
            print(f"  ✅ Memoria disponible: {memoria_disponible}")
            print(f"  ✅ Session ID correcto: {session_info.get('session_id') == session_id}")
            print(f"  📊 Interacciones previas: {memoria_sesion.get('interacciones_previas', 0)}")
            print(f"  📝 Contexto: {'Sí' if contexto_memoria else 'No'}")
    
    # Verificar progresión esperada
    print(f"\n🎯 VERIFICACIÓN DE PROGRESIÓN:")
    
    # La primera llamada no debería tener memoria previa
    if len(memoria_detectada) >= 1:
        primera = memoria_detectada[0]
        if not primera["memoria_disponible"] and primera["interacciones_previas"] == 0:
            print("✅ Primera llamada: Correctamente sin memoria previa")
        else:
            print("❌ Primera llamada: Debería ser nueva sesión")
    
    # Las siguientes llamadas deberían tener memoria
    if len(memoria_detectada) >= 2:
        segunda = memoria_detectada[1]
        if segunda["memoria_disponible"] and segunda["interacciones_previas"] > 0:
            print("✅ Segunda llamada: Correctamente con memoria previa")
        else:
            print("❌ Segunda llamada: Debería recordar interacción anterior")
    
    if len(memoria_detectada) >= 3:
        tercera = memoria_detectada[2]
        if tercera["memoria_disponible"] and tercera["interacciones_previas"] >= 2:
            print("✅ Tercera llamada: Correctamente con memoria acumulada")
        else:
            print("❌ Tercera llamada: Debería recordar interacciones anteriores")
    
    print(f"\n🏁 Prueba completada para sesión: {session_id}")

def call_endpoint(endpoint: str, payload: dict) -> dict:
    """
    Llama a un endpoint y retorna la respuesta
    """
    try:
        url = f"http://localhost:7071{endpoint}"
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "response": response.text[:200]
            }
            
    except Exception as e:
        return {"error": str(e)}

def print_response(title: str, response: dict):
    """
    Imprime una respuesta de forma legible
    """
    print(f"📄 {title}:")
    
    if not response:
        print("  ❌ Sin respuesta")
        return
    
    if "error" in response:
        print(f"  ❌ Error: {response['error']}")
        return
    
    # Extraer información relevante
    metadata = response.get("metadata", {})
    memoria_info = metadata.get("memoria_sesion", {})
    
    print(f"  📊 Status: {'✅ OK' if response.get('exito', True) else '❌ Error'}")
    print(f"  🕐 Timestamp: {metadata.get('timestamp', 'N/A')}")
    print(f"  🆔 Session ID: {metadata.get('session_info', {}).get('session_id', 'N/A')}")
    print(f"  🧠 Memoria: {metadata.get('memoria_disponible', False)}")
    
    if memoria_info:
        print(f"  📈 Interacciones previas: {memoria_info.get('interacciones_previas', 0)}")
        print(f"  🕒 Última actividad: {memoria_info.get('ultima_actividad', 'N/A')}")
    
    contexto = response.get("contexto_memoria", "")
    if contexto:
        print(f"  📝 Contexto: {contexto[:100]}...")

def test_memory_isolation():
    """
    Prueba que las sesiones estén aisladas entre sí
    """
    print(f"\n🔒 Test de aislamiento de sesiones")
    print("-" * 40)
    
    session_a = f"session_a_{uuid.uuid4().hex[:6]}"
    session_b = f"session_b_{uuid.uuid4().hex[:6]}"
    
    # Crear actividad en sesión A
    call_endpoint("/api/ejecutar", {
        "intencion": "dashboard",
        "session_id": session_a,
        "agent_id": "TestAgent"
    })
    
    time.sleep(1)
    
    # Verificar que sesión B no vea la actividad de A
    response_b = call_endpoint("/api/ejecutar", {
        "intencion": "status", 
        "session_id": session_b,
        "agent_id": "TestAgent"
    })
    
    memoria_b = response_b.get("metadata", {}).get("memoria_disponible", False)
    
    if not memoria_b:
        print("✅ Aislamiento correcto: Sesión B no ve actividad de sesión A")
    else:
        print("❌ Fallo de aislamiento: Sesión B ve actividad de otras sesiones")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema de memoria de sesión")
    print("=" * 80)
    
    try:
        test_session_memory()
        test_memory_isolation()
        
        print("\n" + "=" * 80)
        print("🎉 Pruebas completadas")
        print("\n💡 Si las pruebas muestran ✅, el sistema de memoria funciona correctamente")
        print("💡 Si muestran ❌, revisar la configuración de Cosmos DB y los decoradores")
        
    except Exception as e:
        print(f"\n💥 Error ejecutando pruebas: {e}")
        print("💡 Verificar que la Function App esté ejecutándose y Cosmos DB configurado")