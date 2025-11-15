"""
Test: Simular el comportamiento de Foundry con el payload real
"""
import requests
import json

def test_foundry_simulation():
    """Simula cómo Foundry procesa la respuesta del endpoint"""
    
    url = "http://localhost:7071/api/historial-interacciones"
    
    headers = {
        "Session-ID": "assistant-3bQkwzfHq1mxV98fqdw2Em",
        "Agent-ID": "assistant",
        "Content-Type": "application/json"
    }
    
    params = {"limit": 5}
    
    print("🔍 Llamando al endpoint...")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    
    print("\n📊 DATOS RECIBIDOS POR EL MODELO:\n")
    print(f"respuesta_usuario: '{data.get('respuesta_usuario')}'")
    print(f"texto_semantico: '{data.get('texto_semantico')}'")
    print(f"eventos: {len(data.get('eventos', []))} eventos")
    
    # Simular lo que el modelo debería hacer
    eventos = data.get('eventos', [])
    
    print("\n🤖 SIMULACIÓN: Lo que el modelo DEBERÍA generar:\n")
    
    if not eventos:
        print("No hay eventos para procesar")
        return
    
    # Analizar eventos
    endpoints_usados = {}
    for evento in eventos:
        endpoint = evento.get('endpoint', 'unknown')
        endpoints_usados[endpoint] = endpoints_usados.get(endpoint, 0) + 1
    
    # Generar respuesta interpretativa
    print("Basándome en el historial, veo que:")
    for endpoint, count in endpoints_usados.items():
        if endpoint == 'crear-contenedor':
            print(f"  - Creaste {count} cuenta(s) de almacenamiento")
        elif endpoint == 'eliminar-archivo':
            print(f"  - Intentaste eliminar {count} archivo(s)")
        elif endpoint == 'configurar-app-settings':
            print(f"  - Configuraste {count} aplicación(es)")
        elif endpoint == 'copiloto':
            print(f"  - Realizaste {count} consulta(s) al copiloto")
        else:
            print(f"  - Usaste {endpoint} {count} vez/veces")
    
    print("\n✅ ESTO ES LO QUE EL MODELO DEBERÍA RESPONDER")
    print("   (No copiar literalmente texto_semantico)")
    
    # Verificar si hay instrucciones para el modelo
    if "_instruccion_modelo" in data:
        print(f"\n📝 Instrucción para el modelo: {data['_instruccion_modelo']}")
    else:
        print("\n⚠️  NO hay instrucción explícita para el modelo")
        print("   El modelo podría copiar texto_semantico literalmente")

if __name__ == "__main__":
    print("="*60)
    print("🧪 SIMULACIÓN DE FOUNDRY")
    print("="*60)
    print()
    
    test_foundry_simulation()
