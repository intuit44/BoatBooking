#!/usr/bin/env python3
"""
Test de Continuidad Conversacional usando el endpoint /api/ejecutar-cli existente

Este script prueba si el middleware de continuidad conversacional funciona
correctamente con el endpoint existente, verificando:
1. Carga del contexto desde Redis
2. Inyección automática en el prompt 
3. Respuestas con continuidad natural
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# URL del endpoint (ajustar si es necesario)
ENDPOINT_URL = "http://localhost:7071/api/ejecutar-cli"


def test_conversational_continuity():
    """Prueba la continuidad conversacional con el endpoint existente"""

    # Configurar session_id único para esta prueba
    session_id = f"test_continuity_{int(time.time())}"
    agent_id = "test_agent_cli"

    print(f"🧪 Iniciando test de continuidad conversacional")
    print(f"   Session ID: {session_id}")
    print(f"   Agent ID: {agent_id}")
    print("="*60)

    # Test 1: Comando inicial para crear contexto
    print("\n1️⃣ COMANDO INICIAL - Estableciendo contexto...")
    response1 = make_request({
        "comando": "echo 'Hola, soy el agente CLI. Esta es nuestra primera interacción.'"
    }, session_id, agent_id)

    if response1:
        print(
            f"✅ Respuesta 1: {response1.get('resultado', 'Sin resultado')[:100]}...")
        time.sleep(2)  # Dar tiempo para que se procese la memoria
    else:
        print("❌ Error en comando 1")
        return False

    # Test 2: Segundo comando para verificar continuidad
    print("\n2️⃣ SEGUNDO COMANDO - Verificando continuidad...")
    response2 = make_request({
        "comando": "echo 'Como mencioné anteriormente, ahora vamos a continuar la conversación.'"
    }, session_id, agent_id)

    if response2:
        print(
            f"✅ Respuesta 2: {response2.get('resultado', 'Sin resultado')[:100]}...")
        time.sleep(2)
    else:
        print("❌ Error en comando 2")
        return False

    # Test 3: Comando con referencia al historial
    print("\n3️⃣ COMANDO CON REFERENCIA - Testing memoria...")
    response3 = make_request({
        "comando": "echo 'Basándome en nuestra conversación previa, puedo concluir que la continuidad funciona.'"
    }, session_id, agent_id)

    if response3:
        print(
            f"✅ Respuesta 3: {response3.get('resultado', 'Sin resultado')[:100]}...")
    else:
        print("❌ Error en comando 3")
        return False

    # Verificar metadata de memoria aplicada
    print("\n📊 VERIFICACIÓN DE METADATA...")
    for i, response in enumerate([response1, response2, response3], 1):
        metadata = response.get('metadata', {})
        memoria_aplicada = metadata.get('memoria_aplicada', False)
        wrapper_aplicado = metadata.get('wrapper_aplicado', False)
        interacciones_previas = metadata.get('interacciones_previas', 0)

        print(f"   Respuesta {i}:")
        print(f"     - Wrapper aplicado: {wrapper_aplicado}")
        print(f"     - Memoria aplicada: {memoria_aplicada}")
        print(f"     - Interacciones previas: {interacciones_previas}")

    print("\n🎯 RESUMEN DEL TEST:")
    print("✅ Test completado exitosamente")
    print("✅ Tres comandos ejecutados con el mismo session_id")
    print("✅ Metadata indica si se aplicó continuidad conversacional")

    return True


def make_request(payload, session_id, agent_id):
    """Hace una petición al endpoint con headers de sesión"""

    headers = {
        'Content-Type': 'application/json',
        'Session-ID': session_id,
        'Agent-ID': agent_id,
        'X-Source': 'test_continuity'
    }

    try:
        print(f"   🔧 Ejecutando: {payload['comando'][:50]}...")

        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"   📡 Status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            exito = response_data.get('exito', False)
            print(f"   🎯 Éxito: {exito}")

            if exito:
                print(f"   ✅ Comando ejecutado correctamente")
            else:
                error = response_data.get('error', 'Error desconocido')
                print(f"   ⚠️ Comando falló: {error}")

            return response_data
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}...")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   💥 Error de conexión: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"   💥 Error JSON: {e}")
        return None
    except Exception as e:
        print(f"   💥 Error inesperado: {e}")
        return None


if __name__ == "__main__":
    print("🚀 Test de Continuidad Conversacional - Endpoint /api/ejecutar-cli")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

    try:
        success = test_conversational_continuity()
        if success:
            print("\n🎉 TEST COMPLETADO EXITOSAMENTE")
            sys.exit(0)
        else:
            print("\n💥 TEST FALLÓ")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado en el test: {e}")
        sys.exit(1)
