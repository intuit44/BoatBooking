"""
Test de guardado REAL - Valida que se guarden documentos AHORA
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Si no existe .env, cargar desde local.settings.json
if not os.getenv("COSMOSDB_ENDPOINT"):
    try:
        with open("local.settings.json", "r") as f:
            settings = json.load(f)
            for key, value in settings.get("Values", {}).items():
                if not os.getenv(key):
                    os.environ[key] = value
        print("Variables cargadas desde local.settings.json")
    except:
        print("No se pudo cargar local.settings.json")


def test_cosmos_ultimos_documentos():
    """Consulta Cosmos DB para ver los ultimos documentos guardados"""
    print("\n" + "="*80)
    print("TEST: ULTIMOS DOCUMENTOS EN COSMOS DB")
    print("="*80)

    try:
        from azure.cosmos import CosmosClient

        endpoint = os.getenv("COSMOSDB_ENDPOINT") or os.getenv(
            "COSMOS_ENDPOINT")
        key = os.getenv("COSMOSDB_KEY") or os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE", "agentMemory")
        container_name = os.getenv("COSMOS_CONTAINER", "memory")

        if not endpoint or not key:
            print("\n   [ERROR] Variables de entorno no configuradas:")
            print(f"      COSMOSDB_ENDPOINT: {'OK' if endpoint else 'FALTA'}")
            print(f"      COSMOSDB_KEY: {'OK' if key else 'FALTA'}")
            return False

        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Query: ultimos 10 documentos ordenados por _ts (timestamp interno)
        query = "SELECT TOP 10 c.id, c.timestamp, c.endpoint, c.agent_id, c.texto_semantico FROM c ORDER BY c._ts DESC"

        print(f"\n   Consultando: {database_name}/{container_name}")
        print(f"   Query: {query}")

        items = list(container.query_items(
            query=query, enable_cross_partition_query=True))

        print(f"\n   Documentos encontrados: {len(items)}")

        if not items:
            print("\n   [PROBLEMA CRITICO] No hay documentos en Cosmos DB")
            print("      Posibles causas:")
            print("      1. El wrapper NO esta guardando")
            print("      2. La conexion a Cosmos falla silenciosamente")
            print("      3. El contenedor esta vacio")
            return False

        # Analizar timestamps
        print("\n   Ultimos 10 documentos:")
        ahora = datetime.now()
        recientes = 0

        for i, item in enumerate(items, 1):
            ts_str = item.get("timestamp", "")
            endpoint = item.get("endpoint", "unknown")
            agent = item.get("agent_id", "unknown")
            texto = item.get("texto_semantico", "")[:60]

            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                    edad_horas = (ahora - ts).total_seconds() / 3600
                    edad_str = f"{edad_horas:.1f}h" if edad_horas < 48 else f"{edad_horas/24:.1f}d"

                    if edad_horas < 24:
                        recientes += 1
                        print(
                            f"      {i}. [RECIENTE] {edad_str} | {endpoint} | {agent} | {texto}...")
                    else:
                        print(
                            f"      {i}. [VIEJO] {edad_str} | {endpoint} | {agent} | {texto}...")
                except:
                    print(
                        f"      {i}. [ERROR TIMESTAMP] {ts_str} | {endpoint} | {texto}...")
            else:
                print(f"      {i}. [SIN TIMESTAMP] {endpoint} | {texto}...")

        print(f"\n   Documentos recientes (<24h): {recientes}/10")

        if recientes == 0:
            print("\n   [PROBLEMA] NO hay documentos recientes")
            print("      El sistema NO esta guardando nuevas interacciones")
            return False
        elif recientes < 3:
            print("\n   [ADVERTENCIA] Pocos documentos recientes")
            print("      El sistema guarda pero no frecuentemente")
            return False
        else:
            print("\n   [OK] Sistema guardando documentos recientes")
            return True

    except Exception as e:
        print(f"\n   [ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_ai_search_ultimos_documentos():
    """Consulta AI Search para ver los ultimos documentos indexados"""
    print("\n" + "="*80)
    print("TEST: ULTIMOS DOCUMENTOS EN AI SEARCH")
    print("="*80)

    try:
        from services.azure_search_client import AzureSearchService

        search_service = AzureSearchService()

        # Buscar documentos recientes (sin filtros, ordenados por score)
        resultado = search_service.search(
            query="interaccion reciente",
            top=10,
            filters=None
        )

        if not resultado.get("exito"):
            print(f"\n   [ERROR] Busqueda fallo: {resultado.get('error')}")
            return False

        documentos = resultado.get("documentos", [])
        print(f"\n   Documentos encontrados: {len(documentos)}")

        if not documentos:
            print("\n   [PROBLEMA CRITICO] No hay documentos en AI Search")
            print("      Posibles causas:")
            print("      1. El indice esta vacio")
            print("      2. La indexacion NO esta funcionando")
            print("      3. Los embeddings no se generan")
            return False

        # Analizar timestamps
        print("\n   Ultimos 10 documentos:")
        ahora = datetime.now()
        recientes = 0

        for i, doc in enumerate(documentos, 1):
            ts_str = doc.get("timestamp", "")
            endpoint = doc.get("endpoint", "unknown")
            agent = doc.get("agent_id", "unknown")
            score = doc.get("@search.score", 0)
            texto = doc.get("texto_semantico", "")[:60]

            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                    edad_horas = (ahora - ts).total_seconds() / 3600
                    edad_str = f"{edad_horas:.1f}h" if edad_horas < 48 else f"{edad_horas/24:.1f}d"

                    if edad_horas < 24:
                        recientes += 1
                        print(
                            f"      {i}. [RECIENTE] {edad_str} | Score: {score:.2f} | {endpoint} | {texto}...")
                    else:
                        print(
                            f"      {i}. [VIEJO] {edad_str} | Score: {score:.2f} | {endpoint} | {texto}...")
                except:
                    print(
                        f"      {i}. [ERROR TIMESTAMP] {ts_str} | Score: {score:.2f} | {texto}...")
            else:
                print(
                    f"      {i}. [SIN TIMESTAMP] Score: {score:.2f} | {texto}...")

        print(f"\n   Documentos recientes (<24h): {recientes}/10")

        if recientes == 0:
            print("\n   [PROBLEMA] NO hay documentos recientes en AI Search")
            print("      La indexacion NO esta funcionando O esta muy atrasada")
            return False
        elif recientes < 3:
            print("\n   [ADVERTENCIA] Pocos documentos recientes en AI Search")
            return False
        else:
            print("\n   [OK] AI Search tiene documentos recientes")
            return True

    except Exception as e:
        print(f"\n   [ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_wrapper_esta_guardando():
    """Verifica que el wrapper este configurado para guardar"""
    print("\n" + "="*80)
    print("TEST: CONFIGURACION DEL WRAPPER")
    print("="*80)

    try:
        with open("memory_route_wrapper.py", "r", encoding="utf-8") as f:
            content = f.read()

        checks = {
            "registrar_llamada": "memory_service.registrar_llamada" in content,
            "indexar_memoria": "indexar_memoria_endpoint" in content or "QueueClient" in content,
            "filtro_historial": "historial" in content and "not es_endpoint_historial" in content,
            "texto_semantico": "texto_semantico" in content
        }

        print("\n   Verificaciones:")
        for check, resultado in checks.items():
            print(f"      {check}: {'OK' if resultado else 'FALTA'}")

        if all(checks.values()):
            print("\n   [OK] Wrapper configurado correctamente")
            return True
        else:
            print("\n   [PROBLEMA] Wrapper tiene configuracion incompleta")
            return False

    except Exception as e:
        print(f"\n   [ERROR] {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DIAGNOSTICO DE GUARDADO REAL")
    print("="*80)

    resultados = {
        "cosmos": test_cosmos_ultimos_documentos(),
        "ai_search": test_ai_search_ultimos_documentos(),
        "wrapper": test_wrapper_esta_guardando()
    }

    print("\n" + "="*80)
    print("DIAGNOSTICO FINAL")
    print("="*80)

    if resultados["cosmos"] and resultados["ai_search"]:
        print("\n   [OK] Sistema guardando e indexando correctamente")
        print("\n   El problema NO es el guardado, es la RECUPERACION")
        print("\n   Acciones:")
        print("      1. Verificar que buscar_memoria_endpoint use ordenamiento hibrido")
        print("      2. Verificar que NO haya cache de resultados viejos")
        print("      3. Verificar que filtros no sean muy restrictivos")
    elif resultados["cosmos"] and not resultados["ai_search"]:
        print("\n   [PROBLEMA] Cosmos guarda pero AI Search NO indexa")
        print("\n   Acciones:")
        print("      1. Verificar cola de indexacion (memory-indexing-queue)")
        print("      2. Verificar que indexar_memoria_endpoint funcione")
        print("      3. Verificar embeddings se generen correctamente")
    elif not resultados["cosmos"]:
        print("\n   [PROBLEMA CRITICO] NO se estan guardando documentos")
        print("\n   Acciones:")
        print("      1. Verificar que wrapper este aplicado (apply_memory_wrapper)")
        print("      2. Verificar logs de func start para errores")
        print("      3. Verificar conexion a Cosmos DB")

    print("\n" + "="*80)
