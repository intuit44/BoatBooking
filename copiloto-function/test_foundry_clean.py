"""
Simulacion del comportamiento de Foundry
Prueba los cambios antes del despliegue
"""

import requests
import json

def simulate_foundry_agent():
    """Simula exactamente como Foundry hace la llamada"""
    
    print("SIMULANDO COMPORTAMIENTO DE FOUNDRY")
    print("=" * 50)
    
    # Simular la llamada exacta que hace Foundry
    url = "http://localhost:7071/api/historial-interacciones"
    headers = {
        "Content-Type": "application/json",
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    }
    
    print("1. Haciendo llamada como Foundry...")
    print(f"   URL: {url}")
    print(f"   Headers: {headers}")
    
    try:
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n2. Respuesta recibida (Status: {response.status_code})")
            print("   Campos principales:")
            for key in ["exito", "mensaje", "interacciones", "total"]:
                if key in data:
                    if key == "mensaje":
                        mensaje = data[key][:200] + "..." if len(data[key]) > 200 else data[key]
                        print(f"   - {key}: {mensaje}")
                    elif key == "interacciones":
                        print(f"   - {key}: {len(data[key])} elementos")
                    else:
                        print(f"   - {key}: {data[key]}")
            
            # Simular como Foundry procesaria la respuesta
            print("\n3. SIMULACION DE PROCESAMIENTO FOUNDRY:")
            
            # Foundry prioriza interacciones si existen
            if data.get("interacciones") and len(data["interacciones"]) > 0:
                print("   -> Foundry usaria el array 'interacciones' (comportamiento anterior)")
                print("   -> Respuesta: Lista basica de interacciones")
                return "COMPORTAMIENTO_ANTERIOR"
            
            # Si no hay interacciones, usa el mensaje
            elif data.get("mensaje"):
                print("   -> Foundry usaria el campo 'mensaje' (comportamiento deseado)")
                print("   -> Respuesta: Analisis semantico enriquecido")
                mensaje = data["mensaje"]
                
                # Verificar si es respuesta semantica enriquecida
                if "ANALISIS CONTEXTUAL" in mensaje or "Patron de Actividad" in mensaje:
                    print("   OK RESPUESTA SEMANTICA DETECTADA")
                    return "COMPORTAMIENTO_MEJORADO"
                else:
                    print("   WARN Mensaje basico detectado")
                    return "MENSAJE_BASICO"
            
            else:
                print("   -> Sin contenido utilizable")
                return "SIN_CONTENIDO"
                
        else:
            print(f"   ERROR: Status {response.status_code}")
            return "ERROR"
            
    except Exception as e:
        print(f"   EXCEPCION: {str(e)}")
        return "EXCEPCION"

if __name__ == "__main__":
    print("SIMULACION DE FOUNDRY - PRUEBAS PRE-DESPLIEGUE")
    print("=" * 60)
    
    # Prueba basica
    result = simulate_foundry_agent()
    
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    if result == "COMPORTAMIENTO_MEJORADO":
        print("PASS - SISTEMA LISTO PARA DESPLIEGUE")
        print("   - Foundry usara respuestas semanticas enriquecidas")
    elif result == "COMPORTAMIENTO_ANTERIOR":
        print("FAIL - Foundry seguira usando interacciones basicas")
        print("   - Necesita forzar mensaje semantico")
    else:
        print(f"ERROR - Resultado inesperado: {result}")