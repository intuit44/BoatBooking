# -*- coding: utf-8 -*-
"""
Test de captura de entrada del usuario desde Foundry UI
Simula el payload que envía Azure AI Foundry y valida que se persista correctamente.
"""
import os
import json
import requests
import time
from datetime import datetime

# Cargar variables de entorno desde local.settings.json
try:
    with open("local.settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        for key, value in settings.get("Values", {}).items():
            os.environ[key] = str(value)
    print("✅ Variables de entorno cargadas desde local.settings.json\n")
except Exception as e:
    print(f"⚠️ No se pudo cargar local.settings.json: {e}\n")

# Configuración
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/copiloto"


def test_foundry_input_capture():
    """Simula mensaje desde Foundry y valida persistencia completa."""

    print("\n" + "="*80)
    print("🧪 TEST: Captura de entrada del usuario desde Foundry")
    print("="*80 + "\n")

    # Payload simulando Foundry
    payload = {
        "mensaje": "valida si puedes ver los últimos cambios que he realizado",
        "session_id": "test_foundry_session",
        "agent_id": "foundry_test_agent"
    }

    headers = {
        "Content-Type": "application/json",
        "Session-ID": "universal_session",
        "Agent-ID": "foundry_user"
    }

    print(f"📤 Enviando mensaje a {BASE_URL}{ENDPOINT}")
    print(f"📝 Mensaje: {payload['mensaje']}")
    print(f"🔑 Session: {headers['Session-ID']}")
    print(f"👤 Agent: {headers['Agent-ID']}\n")

    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa del endpoint\n")
            print(
                f"📄 Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...\n")
        else:
            print(f"⚠️ Respuesta no exitosa: {response.text[:500]}\n")

        # Esperar a que se complete la indexación
        print("⏳ Esperando 3 segundos para indexación completa...")
        time.sleep(3)

        # Validar en Cosmos DB
        print("\n" + "-"*80)
        print("🔍 VALIDACIÓN EN COSMOS DB")
        print("-"*80 + "\n")

        validate_cosmos_storage(headers['Session-ID'], payload['mensaje'])

        # Validar en Azure AI Search
        print("\n" + "-"*80)
        print("🔍 VALIDACIÓN EN AZURE AI SEARCH")
        print("-"*80 + "\n")

        validate_ai_search_index(payload['mensaje'])

        # Validar respuesta semántica del agente
        print("\n" + "-"*80)
        print("🤖 VALIDACIÓN DE RESPUESTA SEMÁNTICA DEL AGENTE")
        print("-"*80 + "\n")

        validate_agent_response(headers['Session-ID'])

        print("\n" + "="*80)
        print("✅ TEST COMPLETADO")
        print("="*80 + "\n")

    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()


def validate_cosmos_storage(session_id: str, mensaje: str):
    """Valida que el mensaje se guardó en Cosmos DB."""
    try:
        from services.memory_service import memory_service

        # Buscar en historial de sesión
        historial = memory_service.get_session_history(session_id, limit=10)

        print(
            f"📊 Total de documentos en sesión '{session_id}': {len(historial)}")

        # Buscar el mensaje específico
        encontrado = False
        for doc in historial:
            texto = doc.get("texto_semantico", "")
            if mensaje in texto:
                encontrado = True
                print(f"\n✅ Documento encontrado en Cosmos:")
                print(f"   ID: {doc.get('id')}")
                print(f"   Session: {doc.get('session_id')}")
                print(f"   Event Type: {doc.get('event_type')}")
                print(f"   Texto: {texto[:100]}...")
                print(f"   Timestamp: {doc.get('timestamp')}")
                break

        if not encontrado:
            print(f"\n⚠️ Mensaje NO encontrado en Cosmos DB")
            print(f"📋 Últimos 3 documentos:")
            for i, doc in enumerate(historial[:3], 1):
                print(f"\n   {i}. ID: {doc.get('id')}")
                print(f"      Texto: {doc.get('texto_semantico', '')[:80]}...")

    except Exception as e:
        print(f"❌ Error validando Cosmos: {e}")


def validate_ai_search_index(mensaje: str):
    """Valida que el mensaje se indexó en Azure AI Search."""
    try:
        from endpoints_search_memory import buscar_memoria_endpoint

        # Buscar el mensaje
        resultado = buscar_memoria_endpoint({
            "query": mensaje,
            "top": 5
        })

        if resultado.get("exito"):
            docs = resultado.get("documentos", [])
            print(f"📊 Total de documentos encontrados: {len(docs)}")

            # Buscar coincidencia exacta
            encontrado = False
            for doc in docs:
                texto = doc.get("texto_semantico", "")
                if mensaje in texto:
                    encontrado = True
                    print(f"\n✅ Documento encontrado en AI Search:")
                    print(f"   ID: {doc.get('id')}")
                    print(f"   Score: {doc.get('@search.score', 'N/A')}")
                    print(f"   Texto: {texto[:100]}...")
                    break

            if not encontrado:
                print(f"\n⚠️ Mensaje NO encontrado en AI Search")
                print(f"📋 Documentos similares:")
                for i, doc in enumerate(docs[:3], 1):
                    print(
                        f"\n   {i}. Score: {doc.get('@search.score', 'N/A')}")
                    print(
                        f"      Texto: {doc.get('texto_semantico', '')[:80]}...")
        else:
            print(f"❌ Error en búsqueda: {resultado.get('error')}")

    except Exception as e:
        print(f"❌ Error validando AI Search: {e}")


def validate_agent_response(session_id: str):
    """Valida que la respuesta del agente se guardó como evento semántico."""
    try:
        from services.memory_service import memory_service

        # Buscar respuestas semánticas en la sesión
        historial = memory_service.get_session_history(session_id, limit=20)

        respuestas = [doc for doc in historial if doc.get(
            "event_type") == "respuesta_semantica"]

        print(f"📊 Total de respuestas semánticas: {len(respuestas)}")

        if respuestas:
            for i, doc in enumerate(respuestas[:3], 1):
                print(f"\n✅ Respuesta semántica {i}:")
                print(f"   ID: {doc.get('id')}")
                print(f"   Texto: {doc.get('texto_semantico', '')[:150]}...")
                print(f"   Timestamp: {doc.get('timestamp')}")
                print(f"   Vector: {len(doc.get('vector', []))} dimensiones")
        else:
            print("\n⚠️ No se encontraron respuestas semánticas del agente")
            print("📋 Tipos de eventos en la sesión:")
            tipos = {}
            for doc in historial:
                tipo = doc.get("event_type", "unknown")
                tipos[tipo] = tipos.get(tipo, 0) + 1
            for tipo, count in tipos.items():
                print(f"   - {tipo}: {count}")

    except Exception as e:
        print(f"❌ Error validando respuesta del agente: {e}")


if __name__ == "__main__":
    test_foundry_input_capture()
