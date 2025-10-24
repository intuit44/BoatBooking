#!/usr/bin/env python3
"""
Test de verificación para la corrección de Foundry Metrics Integration
Verifica que la ruta semántica /api/ejecutar con diagnosticar:completo devuelve métricas
"""

import requests
import json
import sys
from datetime import datetime

def test_foundry_semantic_route():
    """
    Test que verifica que la ruta semántica devuelve métricas de Function App
    """
    print("FOUNDRY METRICS INTEGRATION - TEST DE VERIFICACION")
    print("=" * 60)
    
    base_url = "http://localhost:7071"
    
    # Test 1: Endpoint directo (debe funcionar)
    print("\n1. Probando endpoint directo...")
    try:
        response = requests.get(f"{base_url}/api/diagnostico-recursos-completo?metricas=true", timeout=30)
        if response.status_code == 200:
            data = response.json()
            function_app_metrics = data.get("metricas", {}).get("function_app")
            if function_app_metrics and not function_app_metrics.get("error"):
                print("   ✅ Endpoint directo: FUNCIONA - Métricas obtenidas")
                print(f"   📊 Métricas encontradas: {list(function_app_metrics.keys())}")
            else:
                print("   ❌ Endpoint directo: Sin métricas o con error")
                print(f"   🔍 Error: {function_app_metrics.get('error', 'No error específico')}")
        else:
            print(f"   ❌ Endpoint directo: Error HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Endpoint directo: Excepción - {str(e)}")
    
    # Test 2: Ruta semántica (debe funcionar después de las correcciones)
    print("\n2. Probando ruta semantica...")
    try:
        payload = {"intencion": "diagnosticar:completo"}
        response = requests.post(
            f"{base_url}/api/ejecutar", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            function_app_metrics = data.get("data", {}).get("metricas", {}).get("function_app")
            
            if function_app_metrics and not function_app_metrics.get("error"):
                print("   ✅ Ruta semántica: FUNCIONA - Métricas obtenidas")
                print(f"   📊 Métricas encontradas: {list(function_app_metrics.keys())}")
                return True
            else:
                print("   ❌ Ruta semántica: Sin métricas o con error")
                
                # Verificar si el problema es el resource group
                function_app_info = data.get("data", {}).get("recursos", {}).get("function_app", {})
                error_msg = function_app_info.get("error", "")
                
                if "boat-rental-rg" in error_msg:
                    print("   🔍 Problema detectado: Usando resource group incorrecto 'boat-rental-rg'")
                    print("   💡 Solución: Reiniciar el servidor de Azure Functions para aplicar correcciones")
                    return False
                else:
                    print(f"   🔍 Error: {error_msg}")
                    return False
        else:
            print(f"   ❌ Ruta semántica: Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ruta semántica: Excepción - {str(e)}")
        return False

def test_resource_group_fix():
    """
    Test específico para verificar que se usa el resource group correcto
    """
    print("\n3. Verificando resource group...")
    try:
        payload = {"intencion": "diagnosticar:completo"}
        response = requests.post(
            "http://localhost:7071/api/ejecutar", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            function_app_info = data.get("data", {}).get("recursos", {}).get("function_app", {})
            error_msg = function_app_info.get("error", "")
            
            if "boat-rental-app-group" in error_msg or function_app_info.get("estado") != "NotFound":
                print("   ✅ Resource group: Usando 'boat-rental-app-group' correctamente")
                return True
            elif "boat-rental-rg" in error_msg:
                print("   ❌ Resource group: Todavía usando 'boat-rental-rg' incorrecto")
                print("   💡 Necesita reinicio del servidor para aplicar correcciones")
                return False
            else:
                print(f"   ⚠️ Resource group: Estado unclear - {error_msg}")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")
        return False

def main():
    """
    Función principal del test
    """
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Objetivo: Verificar que Foundry puede obtener metricas via ruta semantica")
    
    # Ejecutar tests
    semantic_works = test_foundry_semantic_route()
    resource_group_fixed = test_resource_group_fix()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    if semantic_works and resource_group_fixed:
        print("🎉 ÉXITO: Todas las correcciones funcionan correctamente")
        print("✅ Foundry puede obtener métricas via ruta semántica")
        sys.exit(0)
    elif resource_group_fixed and not semantic_works:
        print("⚠️ PARCIAL: Resource group corregido pero métricas no disponibles")
        print("💡 Posible causa: Problemas de conectividad o permisos Azure")
        sys.exit(1)
    elif not resource_group_fixed:
        print("❌ PENDIENTE: Correcciones aplicadas pero servidor necesita reinicio")
        print("🔄 Acción requerida: Reiniciar Azure Functions para aplicar cambios")
        print("📝 Correcciones aplicadas:")
        print("   - procesar_intencion_semantica(): params={'metricas': 'true'}")
        print("   - invocar_endpoint_directo(): X-Resource-Group='boat-rental-app-group'")
        print("   - diagnostico_recursos_completo_http(): RESOURCE_GROUP='boat-rental-app-group'")
        sys.exit(2)
    else:
        print("❌ ERROR: Problema no identificado")
        sys.exit(3)

if __name__ == "__main__":
    main()