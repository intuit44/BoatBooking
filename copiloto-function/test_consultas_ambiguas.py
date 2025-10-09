#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar consultas ambiguas que deben activar Bing Grounding automáticamente
"""

import requests
import json
import time

BASE_URL = "http://localhost:7071"

def test_consulta_ambigua(consulta, descripcion):
    """Prueba una consulta ambigua específica"""
    print(f"\n=== {descripcion} ===")
    print(f"Consulta: '{consulta}'")
    
    try:
        # Probar con /api/hybrid (que debería detectar automáticamente)
        payload = {"agent_response": consulta}
        
        response = requests.post(
            f"{BASE_URL}/api/hybrid",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si se activó Bing Grounding
            metadata = data.get("metadata", {})
            used_grounding = metadata.get("used_grounding", False)
            parsed_endpoint = metadata.get("parsed_endpoint", "unknown")
            
            print(f"Endpoint detectado: {parsed_endpoint}")
            print(f"Usó Bing Grounding: {used_grounding}")
            
            resultado = data.get("resultado", {})
            if resultado.get("exito"):
                print("✅ ÉXITO")
                
                # Mostrar comando sugerido si existe
                if "comando_sugerido" in resultado:
                    print(f"Comando sugerido: {resultado['comando_sugerido']}")
                elif "comando_ejecutable" in resultado:
                    print(f"Comando ejecutable: {resultado['comando_ejecutable']}")
                
                # Mostrar sugerencias si existen
                if "sugerencias" in resultado:
                    print("Sugerencias:")
                    for sug in resultado["sugerencias"][:3]:
                        print(f"  - {sug}")
                        
                return True
            else:
                print(f"❌ Error: {resultado.get('error', 'unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Ejecuta todas las pruebas de consultas ambiguas"""
    print("🧪 PRUEBAS DE CONSULTAS AMBIGUAS")
    print(f"URL Base: {BASE_URL}")
    print("="*60)
    
    # Consultas ambiguas que deben activar Bing Grounding
    consultas_test = [
        # La consulta original del usuario
        ("No sé cómo listar las cuentas de cosmos db en Azure??", 
         "Consulta original del usuario"),
        
        # Variaciones de incertidumbre
        ("no se como ver storage accounts en azure", 
         "Consulta con 'no se como'"),
        
        ("necesito ayuda para listar resource groups", 
         "Consulta con 'necesito ayuda'"),
        
        ("¿cómo hago para ver las function apps?", 
         "Pregunta directa con ¿cómo hago?"),
        
        ("qué comando uso para cosmos db", 
         "Pregunta sobre comando específico"),
        
        # Consultas muy ambiguas
        ("cosmos cosas azure lista", 
         "Consulta fragmentada sin estructura"),
        
        ("ayuda con storage azure porfa", 
         "Consulta informal"),
        
        # Consultas técnicas pero sin comando claro
        ("ver todas las bases de datos cosmos en mi suscripción", 
         "Descripción técnica sin comando"),
        
        ("mostrar cuentas de almacenamiento", 
         "Acción sin contexto Azure CLI"),
        
        # Casos extremos
        ("no tengo idea como hacer esto de azure cosmos", 
         "Expresión de total incertidumbre"),
    ]
    
    resultados = []
    exitosos = 0
    
    for consulta, descripcion in consultas_test:
        resultado = test_consulta_ambigua(consulta, descripcion)
        resultados.append((consulta, resultado))
        if resultado:
            exitosos += 1
        
        # Pausa entre pruebas
        time.sleep(1)
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    total = len(consultas_test)
    print(f"Total de consultas probadas: {total}")
    print(f"Consultas resueltas exitosamente: {exitosos}")
    print(f"Tasa de éxito: {(exitosos/total)*100:.1f}%")
    
    print("\n📋 DETALLE POR CONSULTA:")
    for consulta, resultado in resultados:
        status = "✅" if resultado else "❌"
        print(f"{status} {consulta[:50]}...")
    
    if exitosos >= total * 0.8:  # 80% éxito mínimo
        print("\n🎉 PRUEBAS EXITOSAS - El sistema maneja consultas ambiguas correctamente")
    else:
        print("\n⚠️ MEJORAS NECESARIAS - El sistema necesita ajustes en el parser semántico")
    
    return exitosos, total

if __name__ == "__main__":
    main()