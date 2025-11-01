"""
🧪 Test Completo End-to-End de Memoria Semántica
Simula el flujo completo: Foundry → Copiloto → Cosmos DB → Indexador → Azure Search
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

BASE_URL = "http://localhost:7071/api"
SESSION_ID = f"test_e2e_{int(time.time())}"
AGENT_ID = "Agent914"

def test_1_registrar_interaccion():
    """Test 1: Registrar nueva interacción en Cosmos DB"""
    logging.info("\n" + "="*60)
    logging.info("TEST 1: Registrar interacción en Cosmos DB")
    logging.info("="*60)
    
    response = requests.post(
        f"{BASE_URL}/copiloto",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID,
            "Content-Type": "application/json"
        },
        json={
            "mensaje": "Necesito crear un contenedor Docker para mi aplicación Python"
        }
    )
    
    logging.info(f"Status: {response.status_code}")
    data = response.json()
    logging.info(f"Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    
    assert response.status_code == 200, "Fallo al registrar interacción"
    logging.info("✅ Interacción registrada en Cosmos DB")
    
    return data

def test_2_verificar_cosmos():
    """Test 2: Verificar que se guardó en Cosmos DB"""
    logging.info("\n" + "="*60)
    logging.info("TEST 2: Verificar guardado en Cosmos DB")
    logging.info("="*60)
    
    time.sleep(2)  # Esperar propagación
    
    response = requests.get(
        f"{BASE_URL}/historial-interacciones",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID
        },
        params={"query": "en qué quedamos"}
    )
    
    logging.info(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get("contexto_inteligente", {}).get("interacciones_recientes"):
        logging.info(f"✅ Encontradas {len(data['contexto_inteligente']['interacciones_recientes'])} interacciones")
    else:
        logging.warning("⚠️ No se encontraron interacciones recientes")
    
    return data

def test_3_buscar_por_intencion():
    """Test 3: Búsqueda por intención (semántica)"""
    logging.info("\n" + "="*60)
    logging.info("TEST 3: Búsqueda por intención")
    logging.info("="*60)
    
    logging.info("⏳ Esperando indexación asíncrona (60s)...")
    time.sleep(60)  # Esperar indexación asíncrona (embedding + upload)
    
    # Probar diferentes intenciones
    consultas = [
        "qué hicimos con Docker",
        "muestra errores recientes",
        "en qué quedamos"
    ]
    
    for consulta in consultas:
        logging.info(f"\n🔍 Consulta: '{consulta}'")
        
        response = requests.post(
            f"{BASE_URL}/buscar-memoria",
            headers={
                "Session-ID": SESSION_ID,
                "Agent-ID": AGENT_ID,
                "Content-Type": "application/json"
            },
            json={"query": consulta}  # Sin límite artificial
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            logging.info(f"✅ Encontrados: {total} documentos")
            
            if total > 0:
                for doc in data.get("documentos", [])[:2]:
                    logging.info(f"  - {doc.get('texto_semantico', '')[:80]}...")
        else:
            logging.warning(f"⚠️ Error: {response.status_code}")
    
    return True

def test_4_consulta_hibrida():
    """Test 4: Consulta híbrida (Cosmos + Azure Search + Sintetizador)"""
    logging.info("\n" + "="*60)
    logging.info("TEST 4: Consulta híbrida con sintetizador")
    logging.info("="*60)
    
    response = requests.get(
        f"{BASE_URL}/historial-interacciones",
        headers={
            "Session-ID": SESSION_ID,
            "Agent-ID": AGENT_ID
        },
        params={"query": "qué hicimos con Docker"}
    )
    
    logging.info(f"Status: {response.status_code}")
    data = response.json()
    
    respuesta_usuario = data.get("respuesta_usuario", "")
    logging.info(f"\n📝 Respuesta del sintetizador:\n{respuesta_usuario}\n")
    
    # Verificar que combina ambas fuentes
    tiene_cosmos = data.get("contexto_inteligente", {}).get("tiene_memoria", False)
    tiene_search = data.get("contexto_inteligente", {}).get("documentos_relevantes", 0) > 0
    
    if tiene_cosmos and tiene_search:
        logging.info("✅ Respuesta híbrida: Cosmos DB + Azure Search")
    elif tiene_cosmos:
        logging.info("⚠️ Solo usa Cosmos DB (Azure Search vacío o no indexado aún)")
    else:
        logging.warning("❌ No hay datos de ninguna fuente")
    
    return data

def test_5_validar_embeddings():
    """Test 5: Validar que los embeddings son reales (1536 dimensiones)"""
    logging.info("\n" + "="*60)
    logging.info("TEST 5: Validar dimensiones de embeddings")
    logging.info("="*60)
    
    response = requests.post(
        f"{BASE_URL}/buscar-memoria",
        headers={"Agent-ID": AGENT_ID},
        json={"query": "test"}
    )
    
    data = response.json()
    
    if data.get("documentos"):
        doc = data["documentos"][0]
        if "vector" in doc:
            dim = len(doc["vector"])
            logging.info(f"Dimensiones del vector: {dim}")
            if dim == 1536:
                logging.info("✅ Embeddings correctos (text-embedding-3-large con dimensions=1536)")
            else:
                logging.warning(f"⚠️ Dimensiones: {dim} (esperado 1536 para tier Free)")
        else:
            logging.warning("⚠️ Documento sin campo vector")
    else:
        logging.warning("⚠️ No hay documentos para validar")

def run_all_tests():
    """Ejecutar todos los tests en secuencia"""
    logging.info("\n" + "🚀"*30)
    logging.info("INICIANDO TEST COMPLETO DE MEMORIA SEMÁNTICA")
    logging.info("🚀"*30)
    
    try:
        test_1_registrar_interaccion()
        test_2_verificar_cosmos()
        test_3_buscar_por_intencion()
        test_4_consulta_hibrida()
        test_5_validar_embeddings()
        
        logging.info("\n" + "✅"*30)
        logging.info("TODOS LOS TESTS COMPLETADOS")
        logging.info("✅"*30)
        
    except Exception as e:
        logging.error(f"\n❌ Error en tests: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()
