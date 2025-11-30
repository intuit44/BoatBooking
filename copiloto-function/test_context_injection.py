#!/usr/bin/env python3
"""
Test avanzado de inyección de contexto conversacional

Verifica si el contexto se está inyectando correctamente en el prompt del usuario
"""

import requests
import json
import time
from datetime import datetime

ENDPOINT_URL = "http://localhost:7071/api/ejecutar-cli"


def test_context_injection():
    session_id = f"context_test_{int(time.time())}"

    print(f"🔍 Test de inyección de contexto")
    print(f"   Session: {session_id}")
    print("="*50)

    # Primera consulta para establecer contexto
    print("\n1️⃣ Estableciendo contexto inicial...")

    response1 = requests.post(ENDPOINT_URL, json={
        "comando": "echo 'Soy un agente especializado en análisis de datos financieros. Esta es nuestra primera interacción donde hablamos sobre inversiones.'"
    }, headers={
        "Session-ID": session_id,
        "Agent-ID": "financial_analyst",
        "X-Source": "context_injection_test"
    }, timeout=15)

    if response1.status_code == 200:
        data1 = response1.json()
        print("✅ Primera consulta exitosa")
        print(f"   Resultado: {data1.get('salida', '')[:100]}...")

        # Verificar metadata
        metadata1 = data1.get('metadata', {})
        print(
            f"   Memoria aplicada: {metadata1.get('memoria_aplicada', False)}")
        print(
            f"   Wrapper aplicado: {metadata1.get('wrapper_aplicado', False)}")
    else:
        print(f"❌ Error en primera consulta: {response1.status_code}")
        return

    # Esperar para procesamiento
    print("\n⏳ Esperando procesamiento de memoria...")
    time.sleep(5)

    # Segunda consulta - debería tener contexto inyectado
    print("\n2️⃣ Segunda consulta con continuidad...")

    response2 = requests.post(ENDPOINT_URL, json={
        "comando": "echo 'Continuando nuestra discusión sobre inversiones, ¿qué opinas del mercado actual?'"
    }, headers={
        "Session-ID": session_id,
        "Agent-ID": "financial_analyst",
        "X-Source": "context_injection_test"
    }, timeout=15)

    if response2.status_code == 200:
        data2 = response2.json()
        print("✅ Segunda consulta exitosa")
        print(f"   Resultado: {data2.get('salida', '')[:100]}...")

        # Verificar metadata detallada
        metadata2 = data2.get('metadata', {})
        contexto2 = data2.get('contexto_conversacion', {})

        print(f"\n📊 METADATA DETALLADA:")
        print(
            f"   Memoria aplicada: {metadata2.get('memoria_aplicada', False)}")
        print(
            f"   Wrapper aplicado: {metadata2.get('wrapper_aplicado', False)}")
        print(
            f"   Interacciones previas: {metadata2.get('interacciones_previas', 0)}")

        print(f"\n🧠 CONTEXTO CONVERSACIONAL:")
        print(f"   Mensaje: {contexto2.get('mensaje', 'Sin mensaje')}")
        print(f"   Session ID: {contexto2.get('session_id', 'N/A')}")
        print(f"   Agent ID: {contexto2.get('agent_id', 'N/A')}")
        print(f"   Estrategia: {contexto2.get('estrategia_memoria', 'N/A')}")

        # Verificar si hay indicios de context injection
        if metadata2.get('memoria_aplicada') and metadata2.get('interacciones_previas', 0) > 0:
            print(f"\n🎯 CONTINUIDAD DETECTADA:")
            print(f"   ✅ El middleware está aplicando memoria")
            print(
                f"   ✅ Se detectaron {metadata2.get('interacciones_previas', 0)} interacciones previas")
            print(f"   🔄 Contexto conversacional activo")

            # Buscar indicios de inyección en headers o respuesta
            if hasattr(response2, 'request') and response2.request.body:
                request_body = json.loads(response2.request.body)
                comando_enviado = request_body.get('comando', '')
                print(f"   📝 Comando original: {comando_enviado[:50]}...")

        else:
            print(f"\n⚠️ CONTINUIDAD NO DETECTADA:")
            print(
                f"   Memoria aplicada: {metadata2.get('memoria_aplicada', False)}")
            print(
                f"   Interacciones previas: {metadata2.get('interacciones_previas', 0)}")
    else:
        print(f"❌ Error en segunda consulta: {response2.status_code}")
        return

    # Tercera consulta para verificar continuidad acumulativa
    print("\n3️⃣ Tercera consulta - continuidad acumulativa...")

    time.sleep(2)

    response3 = requests.post(ENDPOINT_URL, json={
        "comando": "echo 'Como mencioné anteriormente sobre análisis financieros, ahora veamos el siguiente paso.'"
    }, headers={
        "Session-ID": session_id,
        "Agent-ID": "financial_analyst",
        "X-Source": "context_injection_test"
    }, timeout=15)

    if response3.status_code == 200:
        data3 = response3.json()
        metadata3 = data3.get('metadata', {})

        print("✅ Tercera consulta exitosa")
        print(
            f"   Interacciones previas: {metadata3.get('interacciones_previas', 0)}")
        print(
            f"   Memoria aplicada: {metadata3.get('memoria_aplicada', False)}")

        # Comparar evolución de interacciones
        prev_count_2 = metadata2.get('interacciones_previas', 0)
        prev_count_3 = metadata3.get('interacciones_previas', 0)

        print(f"\n📈 EVOLUCIÓN DE MEMORIA:")
        print(f"   Consulta 2: {prev_count_2} interacciones previas")
        print(f"   Consulta 3: {prev_count_3} interacciones previas")

        if prev_count_3 >= prev_count_2:
            print(f"   ✅ La memoria se está acumulando correctamente")
        else:
            print(f"   ⚠️ Posible problema en acumulación de memoria")

    print(f"\n🏁 Test de inyección de contexto completado")
    print(f"   Timestamp: {datetime.now().isoformat()}")


if __name__ == "__main__":
    test_context_injection()
