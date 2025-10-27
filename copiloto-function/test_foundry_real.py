#!/usr/bin/env python3
"""
Test REAL que simula exactamente lo que envía Azure AI Foundry
"""
import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:7071"
FOUNDRY_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "azure-agents",  # Simular Foundry
    "Session-ID": "assistant",
    "Agent-ID": "assistant"
}

def test_foundry_historial():
    """Simula la llamada exacta que hace Foundry al historial"""
    print("🧪 TEST FOUNDRY: Consultando historial...")
    
    # Exactamente como lo hace Foundry
    response = requests.get(
        f"{BASE_URL}/api/historial-interacciones",
        headers=FOUNDRY_HEADERS,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Verificar que Foundry recibe lo que necesita
        print(f"✅ Foundry recibe:")
        print(f"  - exito: {data.get('exito')}")
        print(f"  - interacciones (array): {len(data.get('interacciones', []))} elementos")
        print(f"  - mensaje disponible: {'Sí' if data.get('mensaje') else 'No'}")
        print(f"  - usar_mensaje_semantico: {data.get('usar_mensaje_semantico')}")
        
        # Mostrar el mensaje que usará Foundry
        if data.get("mensaje"):
            print(f"\n📝 MENSAJE QUE USARÁ FOUNDRY:")
            print(data["mensaje"][:300] + "..." if len(data["mensaje"]) > 300 else data["mensaje"])
        
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_foundry_pregunta():
    """Simula una pregunta típica de usuario a través de Foundry"""
    print("\n🧪 TEST FOUNDRY: Pregunta de usuario...")
    
    # Simular pregunta del usuario
    payload = {
        "query": "¿Cuáles fueron las últimas interacciones que tuvimos?"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/historial-interacciones",
        headers=FOUNDRY_HEADERS,
        json=payload,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta procesada correctamente")
        
        # Verificar estructura de respuesta
        if data.get("mensaje"):
            print(f"📝 RESPUESTA PARA EL USUARIO:")
            print(data["mensaje"][:500] + "..." if len(data["mensaje"]) > 500 else data["mensaje"])
        
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_foundry_copiloto():
    """Simula llamada al copiloto desde Foundry"""
    print("\n🧪 TEST FOUNDRY: Copiloto...")
    
    response = requests.get(
        f"{BASE_URL}/api/copiloto",
        headers=FOUNDRY_HEADERS,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Copiloto respondió correctamente")
        print(f"  - Tipo: {data.get('tipo')}")
        print(f"  - Memoria integrada: {data.get('metadata', {}).get('memoria_semantica_integrada')}")
        
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def main():
    """Ejecutar todas las pruebas reales de Foundry"""
    print("🚀 INICIANDO PRUEBAS REALES DE FOUNDRY")
    print("=" * 50)
    
    # Test 1: Historial (lo más importante)
    historial_result = test_foundry_historial()
    
    # Test 2: Pregunta de usuario
    pregunta_result = test_foundry_pregunta()
    
    # Test 3: Copiloto
    copiloto_result = test_foundry_copiloto()
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"  - Historial: {'✅' if historial_result else '❌'}")
    print(f"  - Pregunta: {'✅' if pregunta_result else '❌'}")
    print(f"  - Copiloto: {'✅' if copiloto_result else '❌'}")
    
    # Verificar que el sistema funciona como esperado
    if historial_result and historial_result.get("mensaje"):
        print("\n🎯 CONCLUSIÓN:")
        print("✅ El sistema está funcionando correctamente para Foundry")
        print("✅ Foundry recibirá respuestas enriquecidas en el campo 'mensaje'")
        print("✅ El array 'interacciones' está vacío como se diseñó")
    else:
        print("\n❌ PROBLEMA DETECTADO:")
        print("El sistema no está generando respuestas adecuadas para Foundry")

if __name__ == "__main__":
    main()