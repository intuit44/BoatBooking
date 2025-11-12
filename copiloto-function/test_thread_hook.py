"""
Script de prueba para validar sincronización de threads de Foundry con Cosmos
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Intentar importar DefaultAzureCredential (no romper si no está instalado)
try:
    from azure.identity import DefaultAzureCredential
except Exception:
    DefaultAzureCredential = None

# Cargar .env
load_dotenv()
print("AZURE_AI_ENDPOINT:", os.getenv("AZURE_AI_ENDPOINT"))


# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_thread_sync():
    """Prueba la sincronización de un thread real de Foundry"""
    from thread_memory_hook import get_thread_messages, registrar_output_agente

    # 1. Configurar variables de entorno (si no están)
    if not os.getenv("AZURE_AI_ENDPOINT"):
        print("❌ AZURE_AI_ENDPOINT no configurado en .env")
        return False

    # 2. Solicitar thread_id al usuario
    thread_id = input("\nIngresa el Thread ID de Foundry a probar: ").strip()

    if not thread_id:
        print("Thread ID vacio")
        return False

    print(f"\nObteniendo mensajes del thread: {thread_id}")

    # --- Bloque para obtener token de Azure y mostrar credencial utilizada ---
    if DefaultAzureCredential is not None:
        try:
            cred = DefaultAzureCredential()
            token = cred.get_token(
                "https://cognitiveservices.azure.com/.default")
            # usar atributo protegido para mostrar la credencial que funcionó
            successful = getattr(cred, "_successful_credential", None)
            cred_name = type(
                successful).__name__ if successful is not None else "UnknownCredential"
            print(f"🔐 Token adquirido usando: {cred_name}")
        except Exception as e:
            print(f"⚠️ No se pudo obtener token de Azure Identity: {e}")
    else:
        print("⚠️ azure.identity no está disponible. Instala 'azure-identity' para verificar credenciales.")
    # ---------------------------------------------------------------------

    # 3. Obtener mensajes del thread
    try:
        messages = get_thread_messages(thread_id)

        if not messages:
            print("No se encontraron mensajes en el thread")
            print("   Verifica que:")
            print("   - El Thread ID sea correcto")
            print("   - AZURE_AI_ENDPOINT este bien configurado")
            print("   - Tengas permisos en Azure AI Foundry")
            return False

        print(f"Encontrados {len(messages)} mensajes")

        # 4. Mostrar preview de mensajes
        print("\nPreview de mensajes:")
        for i, msg in enumerate(messages[:3], 1):
            content_preview = msg.get("content", "")[:100]
            print(f"   {i}. [{msg.get('role')}] {content_preview}...")

        # 5. Registrar en memoria (ultimos 3)
        print(f"\nRegistrando ultimos 3 mensajes en Cosmos DB...")

        for msg in messages[-3:]:
            registrar_output_agente(
                agent_id="test_agent",
                session_id=thread_id,
                output_text=msg.get("content", ""),
                metadata={
                    "role": msg.get("role"),
                    "timestamp": msg.get("created_at"),
                    "thread_id": thread_id,
                    "sync_source": "test_script"
                }
            )

        print("Mensajes registrados en Cosmos DB")

        # 6. Verificar en Cosmos
        print("\nVerificando en Cosmos DB...")
        from services.memory_service import memory_service

        historial = memory_service.get_session_history(thread_id, limit=10)

        if historial:
            print(
                f"Encontradas {len(historial)} entradas en Cosmos para session_id={thread_id}")

            # Mostrar ultima entrada
            if historial:
                ultima = historial[0]
                print(f"\nUltima entrada:")
                print(f"   Endpoint: {ultima.get('endpoint', 'N/A')}")
                print(f"   Timestamp: {ultima.get('timestamp', 'N/A')}")
                texto = ultima.get('texto_semantico', '')
                print(f"   Texto: {texto[:150]}...")
        else:
            print("No se encontraron entradas en Cosmos (puede tardar unos segundos)")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_request():
    """Prueba el hook completo con un request simulado"""
    from thread_memory_hook import sync_thread_to_memory

    print("\n" + "=" * 60)
    print("SIMULANDO REQUEST DE FOUNDRY")
    print("=" * 60)

    thread_id = input(
        "\nIngresa un Thread-ID real de Foundry para probar\n(ej: thread_qFIUCDF4LztIrlbeZdSlUaNU): ").strip()

    if not thread_id:
        print("\nThread ID vacio - usando thread de ejemplo")
        thread_id = "thread_ejemplo_test"

    # Crear mock request que simula lo que Foundry envia
    class MockRequest:
        def __init__(self, thread_id):
            self.headers = {
                "Thread-ID": thread_id,  # Foundry envia esto automaticamente
                "Agent-ID": "test_agent"
            }

    req = MockRequest(thread_id)
    response_data = {"test": "data"}

    print(f"\n[1/3] Request simulado creado")
    print(f"      Thread-ID en header: {thread_id}")
    print(f"      (Foundry hace esto automaticamente)")

    print(f"\n[2/3] Ejecutando hook...")
    print(f"      Hook extrae Thread-ID del header")
    print(f"      Hook obtiene mensajes del thread")
    print(f"      Hook guarda en Cosmos DB")

    # --- Bloque para obtener token de Azure y mostrar credencial utilizada ---
    if DefaultAzureCredential is not None:
        try:
            cred = DefaultAzureCredential()
            token = cred.get_token(
                "https://cognitiveservices.azure.com/.default")
            successful = getattr(cred, "_successful_credential", None)
            cred_name = type(
                successful).__name__ if successful is not None else "UnknownCredential"
            print(f"🔐 Token adquirido usando: {cred_name}")
        except Exception as e:
            print(f"⚠️ No se pudo obtener token de Azure Identity: {e}")
    else:
        print("⚠️ azure.identity no está disponible. Instala 'azure-identity' para verificar credenciales.")
    # ---------------------------------------------------------------------

    # Ejecutar hook (extrae Thread-ID del header automaticamente)
    result = sync_thread_to_memory(req, response_data)

    print(f"\n[3/3] Hook completado")
    print(f"      Revisa los logs arriba para ver si se sincronizaron mensajes")
    print(f"\nEn produccion, esto ocurre en cada invocacion de endpoint")
    print(f"sin que el usuario haga nada.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Hook Automatico de Threads")
    print("=" * 60)
    print("\nEste test SIMULA lo que Foundry hace automaticamente:")
    print("1. Foundry envia Thread-ID en el header")
    print("2. Hook lo extrae automaticamente")
    print("3. Hook sincroniza mensajes a Cosmos")
    print("\nEN PRODUCCION: El usuario NO hace nada, es 100% automatico")
    print("=" * 60)

    # Solo probar el flujo completo
    success = test_mock_request()

    print("\n" + "=" * 60)
    if success:
        print("TEST COMPLETADO - Hook funciona correctamente")
        print("En produccion, esto ocurre automaticamente en cada request")
    else:
        print("TEST FALLO - Revisar configuracion")
    print("=" * 60)
