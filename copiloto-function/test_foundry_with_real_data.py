"""
Test del flujo Foundry con documentos reales indexados
"""
import requests
import json

BASE_URL = "http://localhost:7071"

def test_foundry_flow():
    """Simula exactamente lo que hace Foundry"""
    print("\n" + "="*80)
    print("SIMULANDO FLUJO DE FOUNDRY CON DATOS REALES")
    print("="*80)
    
    # Paso 1: Copiloto inicial
    print("\n1. Llamando /api/copiloto (Session-ID=assistant)...")
    response1 = requests.post(
        f"{BASE_URL}/api/copiloto",
        json={},
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant",
            "Content-Type": "application/json"
        }
    )
    
    print(f"   Status: {response1.status_code}")
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"   Tipo: {data1.get('tipo', 'N/A')}")
        print(f"   Memoria disponible: {data1.get('metadata', {}).get('memoria_disponible', False)}")
    
    # Paso 2: Historial con tipo=error (como lo hace Foundry)
    print("\n2. Llamando /api/historial-interacciones con tipo=error...")
    print("   (Foundry pregunta: 'configuraciones del contenedor Docker y errores de conexión')")
    
    response2 = requests.post(
        f"{BASE_URL}/api/historial-interacciones",
        json={
            "limit": 10,
            "tipo": "error"
        },
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "assistant",
            "Content-Type": "application/json"
        }
    )
    
    print(f"   Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"   Exito: {data2.get('exito', False)}")
        print(f"   Total interacciones: {data2.get('total', 0)}")
        
        # Verificar metadata de búsqueda semántica
        metadata = data2.get('metadata', {})
        
        print("\n   METADATA:")
        print(f"   - Query SQL aplicada: {bool(metadata.get('query_sql'))}")
        print(f"   - Wrapper aplicado: {metadata.get('wrapper_aplicado', False)}")
        
        if 'busqueda_semantica' in metadata:
            bs = metadata['busqueda_semantica']
            print(f"\n   BUSQUEDA SEMANTICA:")
            print(f"   - Ejecutada: SI")
            print(f"   - Query: {bs.get('query', 'N/A')}")
            print(f"   - Docs encontrados: {bs.get('total_docs', 0)}")
            print(f"   - Tiempo: {bs.get('tiempo_ms', 0)}ms")
            
            if bs.get('documentos'):
                print(f"\n   DOCUMENTOS RECUPERADOS:")
                for i, doc in enumerate(bs['documentos'][:3], 1):
                    print(f"   {i}. Score: {doc.get('@search.score', 0):.3f}")
                    print(f"      {doc.get('texto_semantico', 'N/A')[:80]}...")
        else:
            print(f"\n   BUSQUEDA SEMANTICA: NO EJECUTADA")
        
        # Respuesta al usuario
        print(f"\n   RESPUESTA AL USUARIO:")
        respuesta = data2.get('respuesta_usuario', '')
        if len(respuesta) > 200:
            print(f"   {respuesta[:200]}...")
        else:
            print(f"   {respuesta}")
        
        return 'busqueda_semantica' in metadata and metadata['busqueda_semantica'].get('total_docs', 0) > 0
    else:
        print(f"   Error: {response2.text}")
        return False

def main():
    print("\n" + "="*80)
    print("TEST: Flujo Foundry con Documentos Reales")
    print("="*80)
    print("Documentos indexados: 3 (Docker, contenedor, errores)")
    
    exito = test_foundry_flow()
    
    print("\n" + "="*80)
    print("RESULTADO")
    print("="*80)
    
    if exito:
        print("OK - Busqueda semantica ejecutada y documentos recuperados")
        print("LISTO PARA PROBAR EN FOUNDRY")
    else:
        print("FALLO - Busqueda semantica NO se ejecuto o no encontro documentos")
        print("REVISAR: historial_interacciones.py")

if __name__ == "__main__":
    main()
