"""
Limpia AI Search y re-indexa solo los últimos documentos relevantes
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from services.memory_service import memory_service
from services.azure_search_client import get_search_service
from endpoints_search_memory import indexar_memoria_endpoint

def limpiar_ai_search():
    """Elimina todos los documentos de AI Search"""
    print("\n" + "="*80)
    print("LIMPIANDO AI SEARCH")
    print("="*80)
    
    try:
        search_service = get_search_service()
        
        # Buscar todos los documentos
        resultado = search_service.search(query="*", top=1000)
        
        if not resultado.get("exito"):
            print(f"Error buscando documentos: {resultado.get('error')}")
            return False
        
        documentos = resultado.get("documentos", [])
        print(f"\nDocumentos encontrados: {len(documentos)}")
        
        if not documentos:
            print("No hay documentos para eliminar")
            return True
        
        # Eliminar documentos
        ids_a_eliminar = [{"id": doc["id"]} for doc in documentos]
        resultado_delete = search_service.eliminar_documentos(ids_a_eliminar)
        
        if resultado_delete.get("exito"):
            print(f"✅ Eliminados {len(ids_a_eliminar)} documentos")
            return True
        else:
            print(f"❌ Error eliminando: {resultado_delete.get('error')}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def indexar_ultimos_documentos(limite=200):
    """Indexa solo los últimos N documentos de Cosmos"""
    print("\n" + "="*80)
    print(f"INDEXANDO ÚLTIMOS {limite} DOCUMENTOS")
    print("="*80)
    
    try:
        container = memory_service.memory_container
        
        # Query para obtener solo los últimos documentos con texto_semantico
        query = """
        SELECT TOP @limite * FROM c 
        WHERE c.texto_semantico != null 
        AND c.texto_semantico != ''
        AND LENGTH(c.texto_semantico) > 10
        ORDER BY c._ts DESC
        """
        
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@limite", "value": limite}],
            enable_cross_partition_query=True
        ))
        
        print(f"\nDocumentos encontrados: {len(items)}")
        
        if not items:
            print("No hay documentos para indexar")
            return True
        
        # Indexar en lotes de 50
        batch_size = 50
        indexados = 0
        errores = 0
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            documentos = []
            for item in batch:
                doc = {
                    "id": item.get("id", str(item.get("_ts", i))),
                    "session_id": item.get("session_id", "unknown"),
                    "agent_id": item.get("agent_id") or item.get("data", {}).get("agent_id", "unknown"),
                    "endpoint": item.get("data", {}).get("endpoint", "unknown"),
                    "texto_semantico": item.get("texto_semantico", ""),
                    "exito": item.get("data", {}).get("success", True),
                    "tipo": item.get("event_type", "interaccion"),
                    "timestamp": item.get("timestamp", datetime.utcnow().isoformat())
                }
                documentos.append(doc)
            
            payload = {"documentos": documentos}
            result = indexar_memoria_endpoint(payload)
            
            if result.get("exito"):
                indexados += len(batch)
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} documentos indexados")
            else:
                errores += len(batch)
                print(f"   ❌ Batch {i//batch_size + 1}: Error - {result.get('error')}")
        
        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"Total procesados: {len(items)}")
        print(f"Indexados: {indexados}")
        print(f"Errores: {errores}")
        print(f"Tasa de éxito: {(indexados/len(items)*100):.1f}%")
        
        return indexados > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("LIMPIEZA Y RE-INDEXACIÓN INTELIGENTE")
    print("="*80)
    
    # Paso 1: Limpiar AI Search
    if not limpiar_ai_search():
        print("\n❌ Error en limpieza")
        return
    
    # Paso 2: Indexar solo últimos 200 documentos
    if indexar_ultimos_documentos(200):
        print("\n✅ Re-indexación completada")
        print("\n💡 A partir de ahora, los nuevos documentos se indexarán automáticamente")
    else:
        print("\n❌ Error en re-indexación")

if __name__ == "__main__":
    main()
