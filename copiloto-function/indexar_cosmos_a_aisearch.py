"""
Script para indexar documentos de Cosmos DB en AI Search
"""
import os
import sys
from datetime import datetime

# Configurar path
sys.path.insert(0, os.path.dirname(__file__))

from services.memory_service import memory_service
from endpoints_search_memory import indexar_memoria_endpoint

def indexar_documentos_cosmos():
    """Indexa todos los documentos de Cosmos DB en AI Search"""
    print("\n" + "="*80)
    print("INDEXANDO DOCUMENTOS DE COSMOS DB EN AI SEARCH")
    print("="*80)
    
    try:
        # Obtener container de Cosmos
        container = memory_service.memory_container
        
        # Query para obtener todos los documentos
        query = "SELECT * FROM c WHERE c.texto_semantico != null AND c.texto_semantico != ''"
        
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        print(f"\nDocumentos encontrados en Cosmos: {len(items)}")
        
        if not items:
            print("No hay documentos para indexar")
            return
        
        # Indexar en lotes de 100 documentos
        indexados = 0
        errores = 0
        batch_size = 100
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            try:
                # Preparar batch de documentos
                documentos = []
                for item in batch:
                    doc = {
                        "id": item.get("id", str(item.get("_ts", i))),
                        "session_id": item.get("session_id", "unknown"),
                        "agent_id": item.get("agent_id", "unknown"),
                        "endpoint": item.get("endpoint", "unknown"),
                        "texto_semantico": item.get("texto_semantico", ""),
                        "exito": item.get("exito", True),
                        "tipo": item.get("tipo", "interaccion"),
                        "timestamp": item.get("timestamp", datetime.now().isoformat())
                    }
                    documentos.append(doc)
                
                # Payload correcto con array de documentos
                payload = {"documentos": documentos}
                
                # Indexar batch en AI Search
                result = indexar_memoria_endpoint(payload)
                
                if result.get("exito"):
                    indexados += len(batch)
                    print(f"   Progreso: {i+len(batch)}/{len(items)} documentos procesados...")
                else:
                    errores += len(batch)
                    print(f"   Error indexando batch {i//batch_size + 1}: {result.get('error')}")
                    
            except Exception as e:
                errores += len(batch)
                print(f"   Error procesando batch {i//batch_size + 1}: {e}")
        
        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"Total documentos: {len(items)}")
        print(f"Indexados exitosamente: {indexados}")
        print(f"Errores: {errores}")
        print(f"Tasa de éxito: {(indexados/len(items)*100):.1f}%")
        
        return {
            "total": len(items),
            "indexados": indexados,
            "errores": errores
        }
        
    except Exception as e:
        print(f"\nError fatal: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultado = indexar_documentos_cosmos()
    
    if resultado:
        print("\n✅ Indexación completada")
        sys.exit(0)
    else:
        print("\n❌ Indexación falló")
        sys.exit(1)
