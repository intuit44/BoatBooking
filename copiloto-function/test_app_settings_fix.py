#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar la corrección del endpoint /api/configurar-app-settings
"""

import json
import requests
import time

def test_app_settings_fix():
    """
    Prueba la corrección del endpoint configurar-app-settings con diferentes tipos de datos
    """
    
    # URL del endpoint (ajustar según el entorno)
    base_url = "http://localhost:7071"  # Para desarrollo local
    # base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"  # Para Azure
    
    endpoint = f"{base_url}/api/configurar-app-settings"
    
    # Casos de prueba con diferentes tipos de datos
    test_cases = [
        {
            "name": "Caso 1: Valores mixtos (el que causaba el error)",
            "payload": {
                "function_app": "copiloto-semantico-func-us2",
                "resource_group": "boat-rental-app-group",
                "settings": {
                    "temperatura": "0.35",
                    "herramientas": ["diagnostico-recursos"],  # Lista - debe convertirse a JSON
                    "eliminar_herramientas": ["bateria-endpoints"],  # Lista - debe convertirse a JSON
                    "CUSTOM_SETTING": "valor_string",
                    "NUMERIC_SETTING": 42,  # Número - debe convertirse a string
                    "BOOLEAN_SETTING": True,  # Boolean - debe convertirse a "true"
                    "NULL_SETTING": None,  # None - debe convertirse a string vacío
                    "DICT_SETTING": {"key": "value"}  # Dict - debe convertirse a JSON
                }
            }
        },
        {
            "name": "Caso 2: Solo strings (debería funcionar sin conversiones)",
            "payload": {
                "function_app": "copiloto-semantico-func-us2", 
                "resource_group": "boat-rental-app-group",
                "settings": {
                    "SETTING_1": "valor1",
                    "SETTING_2": "valor2",
                    "SETTING_3": "valor3"
                }
            }
        },
        {
            "name": "Caso 3: Payload inválido (debería devolver error 400)",
            "payload": {
                "function_app": "copiloto-semantico-func-us2",
                "resource_group": "boat-rental-app-group"
                # Falta 'settings' - debería fallar con error descriptivo
            }
        }
    ]
    
    print("🧪 Iniciando pruebas del endpoint /api/configurar-app-settings")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 50)
        
        try:
            # Enviar request
            print(f"📤 Enviando payload: {json.dumps(test_case['payload'], ensure_ascii=False, indent=2)}")
            
            response = requests.post(
                endpoint,
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📥 Status Code: {response.status_code}")
            
            # Parsear respuesta
            try:
                result = response.json()
                print(f"📄 Respuesta: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # Análisis del resultado
                if response.status_code == 200 and result.get("ok"):
                    print("✅ ÉXITO: El endpoint funcionó correctamente")
                    if "conversions_applied" in result:
                        print(f"🔄 Conversiones aplicadas: {result['conversions_applied']}")
                        if result.get("conversion_details"):
                            print(f"📝 Detalles: {result['conversion_details']}")
                elif response.status_code == 400:
                    print("⚠️ ERROR ESPERADO: Validación falló (esto es correcto para casos inválidos)")
                else:
                    print("❌ ERROR: El endpoint falló")
                    if result.get("error"):
                        print(f"💬 Error: {result['error']}")
                        
            except json.JSONDecodeError:
                print(f"❌ ERROR: Respuesta no es JSON válido")
                print(f"📄 Raw response: {response.text[:500]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR DE CONEXIÓN: {str(e)}")
            print("💡 Sugerencia: Verificar que la Function App esté ejecutándose")
            
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {str(e)}")
            
        print()
        time.sleep(1)  # Pausa entre pruebas
    
    print("🏁 Pruebas completadas")
    print("\n📊 Resumen:")
    print("- Si el Caso 1 funciona ✅, la corrección fue exitosa")
    print("- Si el Caso 2 funciona ✅, no se rompió la funcionalidad existente") 
    print("- Si el Caso 3 falla ⚠️ con error 400, la validación funciona correctamente")

def test_conversion_logic():
    """
    Prueba la lógica de conversión de tipos de forma aislada
    """
    print("\n🔬 Probando lógica de conversión de tipos...")
    
    # Simular la lógica de conversión
    test_settings = {
        "string_value": "test",
        "int_value": 42,
        "float_value": 3.14,
        "bool_true": True,
        "bool_false": False,
        "none_value": None,
        "list_value": ["item1", "item2"],
        "dict_value": {"key": "value"},
        "empty_string": ""
    }
    
    normalized_settings = {}
    conversion_log = []
    
    for key, value in test_settings.items():
        if not isinstance(key, str):
            key = str(key)
        
        if value is None:
            normalized_value = ""
            conversion_log.append(f"{key}: None -> empty string")
        elif isinstance(value, (list, dict)):
            normalized_value = json.dumps(value, ensure_ascii=False)
            conversion_log.append(f"{key}: {type(value).__name__} -> JSON string")
        elif isinstance(value, bool):
            normalized_value = "true" if value else "false"
            conversion_log.append(f"{key}: bool -> string")
        elif isinstance(value, (int, float)):
            normalized_value = str(value)
            conversion_log.append(f"{key}: {type(value).__name__} -> string")
        else:
            normalized_value = str(value)
        
        normalized_settings[key] = normalized_value
    
    print("📥 Valores originales:")
    for key, value in test_settings.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    print("\n📤 Valores convertidos:")
    for key, value in normalized_settings.items():
        print(f"  {key}: '{value}' (string)")
    
    print(f"\n🔄 Conversiones aplicadas: {len(conversion_log)}")
    for log in conversion_log:
        print(f"  - {log}")
    
    # Verificar que todos los valores son strings
    all_strings = all(isinstance(v, str) for v in normalized_settings.values())
    print(f"\n✅ Todos los valores son strings: {all_strings}")
    
    return all_strings

if __name__ == "__main__":
    print("🚀 Iniciando verificación de la corrección del endpoint configurar-app-settings")
    print("=" * 80)
    
    # Primero probar la lógica de conversión
    conversion_ok = test_conversion_logic()
    
    if conversion_ok:
        print("\n" + "=" * 80)
        # Luego probar el endpoint real
        test_app_settings_fix()
    else:
        print("❌ La lógica de conversión falló, no se puede continuar con las pruebas del endpoint")
    
    print("\n🎯 Instrucciones:")
    print("1. Ejecutar este script después de aplicar la corrección")
    print("2. Verificar que el Caso 1 (valores mixtos) funcione correctamente")
    print("3. Si funciona, el problema original debería estar resuelto")