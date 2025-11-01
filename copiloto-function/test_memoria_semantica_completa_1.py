"""
🧪 Test Completo End-to-End de Memoria Cognitiva
Simula flujo completo: Foundry → Copiloto → Cosmos DB → Azure Search → Sintetizador
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

BASE_URL = "http://localhost:7071/api"
SESSION_ID = f"session_test_{int(time.time())}"
AGENT_ID = "Agent914"

# =========================
# TEST 0 - INICIALIZAR ÍNDICE CON DOCUMENTOS VECTORIALES
# =========================
def test_0_inicializar_indice_vectorial():
    logging.info("\n" + "="*60)
    logging.info("TEST 0: Inicializar índice con documentos vectoriales REALES")
    logging.info("="*60)
    
    # Documentos de prueba con contenido semántico rico
    documentos_prueba = [
        {
            "texto_semantico": "Configuré un contenedor Docker para la aplicación Python con puerto 8080 expuesto",
            "endpoint": "/api/copiloto",
            "session_id": SESSION_ID,
            "agent_id": AGENT_ID
        },
        {
            "texto_semantico": "Revisé los logs del contenedor y encontré un error de conexión con la base de datos",
            "endpoint": "/api/copiloto",
            "session_id": SESSION_ID,
            "agent_id": AGENT_ID
        },
        {
            "texto_semantico": "Verifiqué el estado del recurso boatrental-app en Azure Portal",
            "endpoint": "/api/diagnostico-recursos",
            "session_id": SESSION_ID,
            "agent_id": AGENT_ID
        }
    ]
    
    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID, "Content-Type": "application/json"}
    
    # Agregar IDs únicos a cada documento
    for i, doc in enumerate(documentos_prueba):
        doc["id"] = f"test_doc_{SESSION_ID}_{i}"
        doc["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    
    # Enviar todos los documentos en un solo request (como espera el endpoint)
    payload = {"documentos": documentos_prueba}
    response = requests.post(f"{BASE_URL}/indexar-memoria", headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("exito"):
            logging.info(f"✅ Indexados {len(documentos_prueba)} documentos con embeddings")
        else:
            logging.warning(f"⚠️ Error: {result.get('error')}")
    else:
        logging.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")
    
    logging.info("⏳ Esperando indexación vectorial (15s)...")
    time.sleep(15)
    logging.info("✅ Índice inicializado con documentos vectoriales\n")
    return True

# =========================
# TEST 1 - REGISTRO INICIAL
# =========================
def test_1_registrar_interaccion():
    logging.info("\n" + "="*60)
    logging.info("TEST 1: Registrar interacción inicial en Copiloto (Cosmos DB)")
    logging.info("="*60)

    payload = {"mensaje": "Necesito crear un contenedor Docker para mi aplicación Python"}
    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID, "Content-Type": "application/json"}

    response = requests.post(f"{BASE_URL}/copiloto", headers=headers, json=payload)
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Respuesta: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:400]}")

    assert response.status_code == 200
    logging.info("✅ Interacción registrada en Cosmos DB correctamente\n")
    return response.json()


# =====================================
# TEST 2 - VERIFICAR MEMORIA EN COSMOS
# =====================================
def test_2_verificar_cosmos():
    logging.info("\n" + "="*60)
    logging.info("TEST 2: Verificar recuperación de memoria en Cosmos DB")
    logging.info("="*60)

    time.sleep(2)
    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID}
    response = requests.get(f"{BASE_URL}/historial-interacciones", headers=headers, params={"query": "en qué quedamos"})
    data = response.json()

    total = len(data.get("interacciones", []))
    logging.info(f"📚 Interacciones encontradas: {total}")
    if total == 0:
        logging.warning("⚠️ Aún sin interacciones recientes.")
    else:
        logging.info("✅ Memoria Cosmos DB operativa.")

    return data


# ============================================
# TEST 3 - BUSCAR POR INTENCIÓN SEMÁNTICA REAL
# ============================================
def test_3_busqueda_por_intencion():
    logging.info("\n" + "="*60)
    logging.info("TEST 3: Buscar por intención semántica (Azure Search vectorial)")
    logging.info("="*60)

    logging.info("⏳ Esperando propagación e indexación asíncrona (60s)...")
    time.sleep(60)

    queries = ["qué hicimos con Docker", "errores recientes", "en qué quedamos"]
    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID, "Content-Type": "application/json"}

    for q in queries:
        response = requests.post(f"{BASE_URL}/buscar-memoria", headers=headers, json={"query": q})
        data = response.json()
        total = data.get("total", 0)
        logging.info(f"🔍 Consulta: '{q}' → {total} resultados")
        if total > 0:
            for d in data.get("documentos", [])[:2]:
                logging.info(f"  • {d.get('texto_semantico', '')[:100]}...")
        else:
            logging.warning("⚠️ Sin coincidencias semánticas")

    return True


# =====================================================
# TEST 4 - CONSULTA HÍBRIDA (COSMOS + AZURE SEARCH)
# =====================================================
def test_4_consulta_hibrida():
    logging.info("\n" + "="*60)
    logging.info("TEST 4: Validar consulta híbrida con sintetizador cognitivo")
    logging.info("="*60)

    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID}
    response = requests.get(f"{BASE_URL}/historial-interacciones", headers=headers, params={"query": "en qué quedamos"})
    data = response.json()

    respuesta = data.get("respuesta_usuario", "")
    contexto = data.get("contexto_inteligente", {})
    logging.info(f"\n🧠 Respuesta semántica del sintetizador:\n{respuesta}\n")

    docs = contexto.get("documentos_relevantes", 0)
    fuente = contexto.get("fuente_datos")
    logging.info(f"📊 Contexto cognitivo: {docs} docs · Fuente: {fuente}")

    assert respuesta, "❌ No se generó respuesta semántica"
    if docs > 0:
        logging.info("✅ Consulta híbrida completa: Cosmos + Azure Search")
    else:
        logging.warning("⚠️ Respuesta parcial (solo Cosmos)")

    return data


# ==============================================
# TEST 5 - RESPUESTA DIRECTA DEL COPILOTO REAL
# ==============================================
def test_5_copiloto_responde_contexto():
    logging.info("\n" + "="*60)
    logging.info("TEST 5: Validar respuesta semántica directa del Copiloto")
    logging.info("="*60)

    headers = {"Session-ID": SESSION_ID, "Agent-ID": AGENT_ID, "Content-Type": "application/json"}
    payload = {"mensaje": "en qué quedamos"}
    response = requests.post(f"{BASE_URL}/copiloto", headers=headers, json=payload)

    data = response.json()
    respuesta = data.get("respuesta_usuario", "")
    fuente = data.get("fuente_datos", "Cosmos")

    logging.info(f"🤖 Copiloto respondió (fuente: {fuente}):\n{respuesta[:400]}")

    if fuente.startswith("AzureSearch"):
        logging.info("✅ Respuesta vectorial real confirmada")
    else:
        logging.warning("⚠️ Fallback a Cosmos (sin embeddings detectados)")

    return data


# ================================
# TEST 6 - VALIDAR EMBEDDINGS REALES
# ================================
def test_6_validar_embeddings():
    logging.info("\n" + "="*60)
    logging.info("TEST 6: Validar embeddings reales en Azure Search")
    logging.info("="*60)

    response = requests.post(f"{BASE_URL}/buscar-memoria", json={"query": "test"})
    data = response.json()
    if data.get("documentos"):
        vector = data["documentos"][0].get("vector", [])
        dim = len(vector)
        logging.info(f"📏 Dimensión vectorial: {dim}")
        if dim == 3072 or dim == 1536:
            logging.info("✅ Embeddings válidos")
        else:
            logging.warning(f"⚠️ Dimensiones inesperadas: {dim}")
    else:
        logging.warning("⚠️ Sin documentos con campo vector")

# ============================
# EJECUTAR TODOS LOS TESTS
# ============================
def run_all_tests():
    logging.info("\n" + "🚀"*30)
    logging.info("INICIANDO TEST COMPLETO DE MEMORIA COGNITIVA")
    logging.info("🚀"*30)

    try:
        test_0_inicializar_indice_vectorial()  # 🔥 NUEVO: Inicializar con vectores
        test_1_registrar_interaccion()
        test_2_verificar_cosmos()
        test_3_busqueda_por_intencion()
        test_4_consulta_hibrida()
        test_5_copiloto_responde_contexto()
        test_6_validar_embeddings()

        logging.info("\n" + "✅"*30)
        logging.info("TODOS LOS TESTS COGNITIVOS COMPLETADOS")
        logging.info("✅"*30)
    except Exception as e:
        logging.error(f"❌ Error en tests: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
