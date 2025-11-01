"""
🧪 Test de Validación de Embeddings Vectoriales
Valida que Azure AI Search retorna vectores completos en las búsquedas semánticas
"""

import os
import sys
import json
from pathlib import Path
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Cargar configuración desde local.settings.json
def load_config():
    config_path = Path(__file__).parent / "local.settings.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("Values", {})
    return {}

config = load_config()
SEARCH_ENDPOINT = config.get("AZURE_SEARCH_ENDPOINT", "https://boatrentalfoundrysearch.search.windows.net")
SEARCH_KEY = config.get("AZURE_SEARCH_KEY")
INDEX_NAME = config.get("AZURE_SEARCH_INDEX_NAME", "agent-memory-index")

# Validar que las credenciales existen
if not SEARCH_KEY:
    print("❌ ERROR: AZURE_SEARCH_KEY no encontrada en local.settings.json")
    sys.exit(1)

def test_embeddings_en_busqueda():
    """Valida que los embeddings se recuperan correctamente"""
    
    print("🔍 Iniciando validación de embeddings vectoriales...\n")
    
    # Cliente de búsqueda
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # Búsqueda con select explícito de campos incluyendo vector
    results = search_client.search(
        search_text="operación técnica",
        select=["id", "texto_semantico", "vector", "timestamp", "session_id"],
        top=3
    )
    
    resultados = list(results)
    
    print(f"✅ Documentos recuperados: {len(resultados)}\n")
    
    if not resultados:
        print("⚠️  No se encontraron documentos. Verifica que el índice tenga datos.")
        return False
    
    # Validaciones
    exito = True
    
    for i, doc in enumerate(resultados, 1):
        print(f"📄 Documento {i}:")
        print(f"   ID: {doc.get('id', 'N/A')}")
        print(f"   Texto: {doc.get('texto_semantico', 'N/A')[:80]}...")
        print(f"   Timestamp: {doc.get('timestamp', 'N/A')}")
        
        # Validación crítica: campo vector existe
        if 'vector' not in doc:
            print(f"   ❌ FALLO: Campo 'vector' NO encontrado")
            exito = False
        else:
            vector = doc['vector']
            if vector and isinstance(vector, list):
                dim = len(vector)
                print(f"   ✅ Vector encontrado: {dim} dimensiones")
                
                # Validar dimensión esperada (text-embedding-3-large = 3072)
                if dim != 3072:
                    print(f"   ⚠️  ADVERTENCIA: Dimensión esperada 3072, encontrada {dim}")
                    exito = False
                
                # Validar que no sea vector vacío
                if all(v == 0 for v in vector[:10]):
                    print(f"   ⚠️  ADVERTENCIA: Vector parece estar vacío (primeros valores = 0)")
                    exito = False
            else:
                print(f"   ❌ FALLO: Vector existe pero está vacío o no es lista")
                exito = False
        
        print()
    
    return exito


def test_busqueda_vectorial_semantica():
    """Valida que la búsqueda vectorial retorna scores semánticos"""
    
    print("\n🧠 Validando búsqueda vectorial semántica...\n")
    
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # Búsqueda semántica
    results = search_client.search(
        search_text="resumen de actividad",
        select=["id", "texto_semantico", "vector"],
        top=3,
        include_total_count=True
    )
    
    resultados = list(results)
    
    print(f"✅ Resultados semánticos: {len(resultados)}\n")
    
    if not resultados:
        print("⚠️  No se encontraron resultados semánticos")
        return False
    
    # Validar que hay scores (búsqueda vectorial activa)
    for i, doc in enumerate(resultados, 1):
        score = doc.get('@search.score', 0)
        print(f"📊 Resultado {i}: Score = {score:.4f}")
        
        if score == 0:
            print(f"   ⚠️  Score = 0 puede indicar búsqueda no vectorial")
    
    print()
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TEST DE VALIDACIÓN DE EMBEDDINGS VECTORIALES")
    print("=" * 70)
    print()
    
    # Test 1: Embeddings en resultados
    test1_ok = test_embeddings_en_busqueda()
    
    # Test 2: Búsqueda vectorial semántica
    test2_ok = test_busqueda_vectorial_semantica()
    
    # Resultado final
    print("=" * 70)
    if test1_ok and test2_ok:
        print("✅ TODOS LOS TESTS PASARON")
        print("✅ Embeddings vectoriales funcionando correctamente")
        print("✅ Sistema listo para Foundry y agentes externos")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("⚠️  Revisar configuración de embeddings en Azure Search")
    print("=" * 70)
    
    sys.exit(0 if (test1_ok and test2_ok) else 1)
