"""
Verificar qué documentos están indexados en AI Search
"""
import requests
import json

BASE_URL = "http://localhost:7071"

def check_ai_search():
    """Verifica documentos en AI Search con diferentes queries"""
    print("\n" + "="*80)
    print("VERIFICANDO DOCUMENTOS INDEXADOS EN AI SEARCH")
    print("="*80)
    
    queries = [
        "Docker",
        "contenedor",
        "error",
        "configuración",
        "*"  # Búsqueda universal
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        response = requests.post(
            f"{BASE_URL}/api/buscar-memoria",
            json={"query": query, "top": 5},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"   Status: 200 | Documentos: {total}")
            
            if data.get('documentos'):
                for i, doc in enumerate(data['documentos'][:3], 1):
                    texto = doc.get('texto_semantico', 'N/A')
                    score = doc.get('@search.score', 0)
                    session = doc.get('session_id', 'N/A')
                    tipo = doc.get('tipo', 'N/A')
                    print(f"   {i}. [{tipo}] Score: {score:.3f}")
                    print(f"      Session: {session}")
                    print(f"      Texto: {texto[:100]}...")
        else:
            print(f"   Error: {response.status_code}")

def check_cosmos():
    """Verifica documentos en Cosmos DB"""
    print("\n" + "="*80)
    print("VERIFICANDO DOCUMENTOS EN COSMOS DB")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/historial-interacciones",
        json={"limit": 10},
        headers={
            "Session-ID": "universal",
            "Agent-ID": "test"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        print(f"   Status: 200 | Interacciones: {total}")
        
        if data.get('interacciones'):
            for i, inter in enumerate(data['interacciones'][:5], 1):
                texto = inter.get('texto_semantico', 'N/A')
                session = inter.get('session_id', 'N/A')
                tipo = inter.get('tipo', 'N/A')
                exito = inter.get('exito', False)
                print(f"   {i}. [{tipo}] {'OK' if exito else 'ERROR'}")
                print(f"      Session: {session}")
                print(f"      Texto: {texto[:100]}...")
    else:
        print(f"   Error: {response.status_code}")

def main():
    print("\n" + "="*80)
    print("DIAGNOSTICO DE MEMORIA INDEXADA")
    print("="*80)
    
    check_ai_search()
    check_cosmos()
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print("Si AI Search tiene 0 documentos pero Cosmos tiene datos,")
    print("ejecuta: python test_cosmos_memory.py para indexar.")

if __name__ == "__main__":
    main()
