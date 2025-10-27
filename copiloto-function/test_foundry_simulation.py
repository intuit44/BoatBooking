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
                    print("   ✅ RESPUESTA SEMANTICA DETECTADA")
                    return "COMPORTAMIENTO_MEJORADO"
                else:
                    print("   ⚠️ Mensaje basico detectado")
                    return "MENSAJE_BASICO"
            
            else:
                print("   -> Sin contenido utilizable")
                return "SIN_CONTENIDO"
                
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            return "ERROR"
            
    except Exception as e:
        print(f"   ❌ Excepcion: {str(e)}")
        return "EXCEPCION"

def test_multiple_scenarios():
    """Prueba multiples escenarios"""
    
    print("\nPROBANDO MULTIPLES ESCENARIOS")
    print("=" * 50)
    
    scenarios = [
        {"name": "Consulta historica", "query": "¿Cuáles fueron las últimas interacciones?"},
        {"name": "Contexto enriquecido", "query": "necesito contexto semántico enriquecido"},
        {"name": "Continuacion", "query": "continuar con el análisis"}
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n🧪 Escenario: {scenario['name']}")
        print(f"   Query: {scenario['query']}")
        
        # Hacer llamada con query especifica
        url = "http://localhost:7071/api/historial-interacciones"
        headers = {
            "Content-Type": "application/json", 
            "Session-ID": "assistant",
            "Agent-ID": "assistant"
        }
        
        try:
            response = requests.post(url, headers=headers, json={"query": scenario["query"]})
            
            if response.status_code == 200:
                data = response.json()
                
                # Analizar respuesta
                interacciones_count = len(data.get("interacciones", []))
                mensaje_length = len(data.get("mensaje", ""))
                tiene_semantico = "usar_mensaje_semantico" in data
                
                print(f"   - Interacciones: {interacciones_count}")
                print(f"   - Mensaje length: {mensaje_length}")
                print(f"   - Marcador semantico: {tiene_semantico}")
                
                # Determinar comportamiento esperado
                if interacciones_count == 0 and mensaje_length > 100:
                    result = "✅ FORZARA_MENSAJE_SEMANTICO"
                elif interacciones_count > 0:
                    result = "⚠️ USARA_INTERACCIONES_BASICAS"
                else:
                    result = "❌ SIN_CONTENIDO_UTIL"
                
                print(f"   Resultado: {result}")
                results.append((scenario["name"], result))
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                results.append((scenario["name"], "ERROR"))
                
        except Exception as e:
            print(f"   ❌ Excepcion: {str(e)}")
            results.append((scenario["name"], "EXCEPCION"))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("RESUMEN DE RESULTADOS")
    print("=" * 50)
    
    success_count = 0
    for name, result in results:
        status = "✅" if "FORZARA_MENSAJE" in result else "❌"
        print(f"{status} {name}: {result}")
        if "FORZARA_MENSAJE" in result:
            success_count += 1
    
    print(f"\nExito: {success_count}/{len(results)} escenarios")
    
    if success_count == len(results):
        print("🎉 TODOS LOS ESCENARIOS PASARON")
        print("🚀 LISTO PARA DESPLIEGUE")
        return True
    else:
        print("🔧 REQUIERE AJUSTES ADICIONALES")
        return False

if __name__ == "__main__":
    print("🧪 SIMULACION DE FOUNDRY - PRUEBAS PRE-DESPLIEGUE")
    print("=" * 60)
    
    # Prueba basica
    basic_result = simulate_foundry_agent()
    
    # Pruebas de escenarios
    scenarios_passed = test_multiple_scenarios()
    
    print("\n" + "=" * 60)
    print("CONCLUSION FINAL")
    print("=" * 60)
    
    if basic_result == "COMPORTAMIENTO_MEJORADO" and scenarios_passed:
        print("✅ SISTEMA LISTO PARA DESPLIEGUE")
        print("   - Foundry usara respuestas semanticas enriquecidas")
        print("   - Todos los escenarios funcionan correctamente")
    else:
        print("❌ SISTEMA REQUIERE AJUSTES")
        print(f"   - Resultado basico: {basic_result}")
        print(f"   - Escenarios: {'PASS' if scenarios_passed else 'FAIL'}")