"""
🔄 Migración de Embeddings Reales desde Cosmos DB a Azure AI Search
Genera embeddings con text-embedding-3-large y reindexar memoria completa
"""

import os
import logging
from datetime import datetime
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración
# Cosmos DB - preferir COSMOSDB_* sobre alias heredados
COSMOS_ENDPOINT = os.getenv("COSMOSDB_ENDPOINT") or os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOSDB_KEY") or os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOSDB_DATABASE") or os.getenv("COSMOS_DATABASE") or os.getenv("COSMOS_DATABASE_NAME", "agentMemory")
COSMOS_CONTAINER = os.getenv("COSMOSDB_CONTAINER") or os.getenv("COSMOS_CONTAINER") or os.getenv("COSMOS_CONTAINER_NAME", "memory")

if not COSMOS_ENDPOINT:
    logging.error("❌ COSMOSDB_ENDPOINT no configurada")
    exit(1)

if not COSMOS_KEY:
    logging.error("❌ COSMOSDB_KEY no configurada")
    exit(1)

# Guardrail: rechazar DB/Container incorrectos
if COSMOS_DATABASE != "agentMemory" or COSMOS_CONTAINER != "memory":
    logging.error(f"❌ DB/Container inesperados: {COSMOS_DATABASE}/{COSMOS_CONTAINER}")
    logging.error("Esperado: agentMemory/memory")
    exit(1)

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "agent-memory-index")

# Cliente Azure OpenAI con Managed Identity
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

if not os.getenv("AZURE_OPENAI_ENDPOINT"):
    logging.error("❌ AZURE_OPENAI_ENDPOINT requerido")
    exit(1)

# Usar Managed Identity si no hay API key
if os.getenv("AZURE_OPENAI_KEY"):
    openai_client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    logging.info("✅ Usando Azure OpenAI con API Key")
else:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    openai_client = AzureOpenAI(
        azure_ad_token_provider=token_provider,
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    logging.info("✅ Usando Azure OpenAI con Managed Identity")

EMBEDDING_MODEL = "text-embedding-3-large"

def generar_embedding(texto: str) -> list:
    """Genera embedding real con OpenAI"""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"❌ Error generando embedding: {e}")
        return None

def migrar_desde_cosmos():
    """Lee Cosmos DB, genera embeddings y sube a Azure Search"""
    
    logging.info("🚀 Iniciando migración de embeddings...")
    logging.info(f"📊 Cosmos: {COSMOS_ENDPOINT}")
    logging.info(f"📊 Database: {COSMOS_DATABASE}, Container: {COSMOS_CONTAINER}")
    logging.info(f"🔍 Search: {SEARCH_ENDPOINT}, Index: {SEARCH_INDEX}")
    
    # Conectar a Cosmos DB
    try:
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    except Exception as e:
        logging.error(f"❌ Error conectando a Cosmos DB: {e}")
        return
    database = cosmos_client.get_database_client(COSMOS_DATABASE)
    container = database.get_container_client(COSMOS_CONTAINER)
    
    # Conectar a Azure Search
    if SEARCH_KEY:
        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
    else:
        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=DefaultAzureCredential()
        )
    
    # Obtener IDs ya indexados en Azure Search
    try:
        existing_ids = set()
        results = search_client.search(search_text="*", select="id", top=50000)
        for doc in results:
            existing_ids.add(doc["id"])
        logging.info(f"📊 Documentos ya indexados: {len(existing_ids)}")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo obtener IDs existentes: {e}")
        existing_ids = set()
    
    # Leer todos los documentos de Cosmos
    query = "SELECT * FROM c ORDER BY c._ts DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    logging.info(f"📊 Total documentos en Cosmos: {len(items)}")
    
    documentos_indexados = 0
    documentos_omitidos = 0
    errores = 0
    
    for item in items:
        # Saltar si ya está indexado
        if item.get("id") in existing_ids:
            documentos_omitidos += 1
            if documentos_omitidos % 100 == 0:
                logging.info(f"⏭️ Omitidos: {documentos_omitidos}")
            continue
        try:
            doc_id = item.get("id")
            
            # Extraer texto semántico
            texto_semantico = (
                item.get("texto_semantico") 
                or item.get("comando") 
                or item.get("mensaje")
                or f"{item.get('endpoint', '')} {item.get('tipo', '')}"
            )
            
            if not texto_semantico or len(texto_semantico.strip()) < 5:
                logging.warning(f"⚠️ Documento {item.get('id')} sin texto válido, omitiendo")
                continue
            
            # Generar embedding real
            logging.info(f"🔄 Generando embedding para: {item.get('id')}")
            vector = generar_embedding(texto_semantico)
            
            if not vector:
                logging.error(f"❌ No se pudo generar embedding para {item.get('id')}")
                errores += 1
                continue
            
            # Preparar documento para Azure Search
            timestamp = item.get("timestamp")
            if isinstance(timestamp, str):
                # Asegurar formato ISO 8601 con Z
                if not timestamp.endswith('Z'):
                    timestamp = timestamp.split('.')[0] + 'Z'
            else:
                timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            doc = {
                "id": item.get("id"),
                "agent_id": item.get("agent_id", "unknown"),
                "session_id": item.get("session_id", "unknown"),
                "endpoint": item.get("endpoint", ""),
                "timestamp": timestamp,
                "tipo": item.get("tipo", "memoria"),
                "texto_semantico": texto_semantico,
                "vector": vector,
                "exito": item.get("exito", True)
            }
            
            # Subir a Azure Search
            result = search_client.upload_documents(documents=[doc])
            
            if result[0].succeeded:
                documentos_indexados += 1
                logging.info(f"✅ Indexado: {item.get('id')}")
            else:
                logging.error(f"❌ Fallo indexación: {item.get('id')}")
                errores += 1
                
        except Exception as e:
            logging.error(f"❌ Error procesando {item.get('id', 'unknown')}: {e}")
            errores += 1
    
    logging.info(f"""
    ✅ Migración completada
    📊 Documentos indexados: {documentos_indexados}
    ⏭️ Documentos omitidos (ya existían): {documentos_omitidos}
    ❌ Errores: {errores}
    📈 Total procesados: {len(items)}
    """)

if __name__ == "__main__":
    migrar_desde_cosmos()
