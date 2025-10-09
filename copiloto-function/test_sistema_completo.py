#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de pruebas completo para validar el sistema
Valida: ejecutar-cli, wrapper automático, funciones de diagnóstico, Cosmos DB
"""

import json
import requests
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:7071"  # Cambiar por URL de Azure si es necesario
HEADERS = {"Content-Type": "application/json"}

def test_ejecutar_cli_adaptabilidad():
    """Prueba que api/ejecutar-cli sea adaptable a cualquier comando"""
    print("\nPRUEBA 1: Adaptabilidad de /api/ejecutar-cli")
    
    comandos_test = [
        {"comando": "storage account list"},
        {"comando": "group list"},
        {"comando": "webapp list"},
        {"comando": "functionapp list"},
        {"comando": "az storage account list"},  # Con prefijo az
        {"comando": "version"},
        {"comando": "account show"},
    ]
    
    resultados = []
    for i, payload in enumerate(comandos_test, 1):
        print(f"  Test {i}: {payload['comando']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ejecutar-cli",
                json=payload,
                headers=HEADERS,
                timeout=30
            )
            
            result = {
                "comando": payload["comando"],
                "status_code": response.status_code,
                "exito": response.status_code == 200,
                "response_size": len(response.text),
                "tiene_json": False
            }
            
            try:
                data = response.json()
                result["tiene_json"] = True
                result["exito_comando"] = data.get("exito", False)
                result["error"] = data.get("error")
            except:
                result["raw_response"] = response.text[:100]
            
            resultados.append(result)
            print(f"    ✅ Status: {response.status_code}, JSON: {result['tiene_json']}")
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            resultados.append({
                "comando": payload["comando"],
                "error": str(e),
                "exito": False
            })
    
    # Resumen
    exitosos = sum(1 for r in resultados if r.get("exito"))
    print(f"\nResultado: {exitosos}/{len(comandos_test)} comandos procesados correctamente")
    return resultados

def test_manejo_errores_robusto():
    """Prueba el manejo robusto de errores"""
    print("\nPRUEBA 2: Manejo robusto de errores")
    
    casos_error = [
        {},  # Body vacío
        {"comando": ""},  # Comando vacío
        {"comando": "comando-inexistente-xyz"},  # Comando inválido
        {"intencion": "dashboard"},  # Campo incorrecto
        {"comando": "storage account list --invalid-flag"},  # Flag inválido
        "string_directo",  # No es JSON
    ]
    
    resultados = []
    for i, payload in enumerate(casos_error, 1):
        print(f"  Test {i}: {type(payload).__name__} - {str(payload)[:50]}")
        try:
            if isinstance(payload, str):
                response = requests.post(
                    f"{BASE_URL}/api/ejecutar-cli",
                    data=payload,
                    headers={"Content-Type": "text/plain"},
                    timeout=15
                )
            else:
                response = requests.post(
                    f"{BASE_URL}/api/ejecutar-cli",
                    json=payload,
                    headers=HEADERS,
                    timeout=15
                )
            
            result = {
                "payload": str(payload)[:50],
                "status_code": response.status_code,
                "manejo_correcto": response.status_code in [400, 422, 500],
                "response_size": len(response.text)
            }
            
            try:
                data = response.json()
                result["tiene_estructura_error"] = "error" in data
                result["mensaje_error"] = data.get("error", "")[:100]
            except:
                result["tiene_estructura_error"] = False
            
            resultados.append(result)
            status_ok = "✅" if result["manejo_correcto"] else "❌"
            print(f"    {status_ok} Status: {response.status_code}")
            
        except Exception as e:
            print(f"    ❌ Excepción: {str(e)}")
            resultados.append({
                "payload": str(payload)[:50],
                "error": str(e),
                "manejo_correcto": False
            })
    
    correctos = sum(1 for r in resultados if r.get("manejo_correcto"))
    print(f"\nResultado: {correctos}/{len(casos_error)} errores manejados correctamente")
    return resultados

def test_wrapper_automatico():
    """Prueba que el wrapper automático capture intenciones"""
    print("\nPRUEBA 3: Wrapper automatico de memoria")
    
    # Probar diferentes endpoints que deberían tener el wrapper
    endpoints_test = [
        {"url": "/api/ejecutar-cli", "payload": {"comando": "account show"}},
        {"url": "/api/ejecutar", "payload": {"intencion": "dashboard"}},
        {"url": "/api/status", "payload": None},
        {"url": "/api/copiloto", "payload": None},
    ]
    
    resultados = []
    for endpoint_info in endpoints_test:
        url = endpoint_info["url"]
        payload = endpoint_info["payload"]
        
        print(f"  Probando: {url}")
        try:
            if payload:
                response = requests.post(f"{BASE_URL}{url}", json=payload, headers=HEADERS, timeout=15)
            else:
                response = requests.get(f"{BASE_URL}{url}", timeout=15)
            
            result = {
                "endpoint": url,
                "status_code": response.status_code,
                "exito": response.status_code == 200,
                "tiene_metadata": False,
                "tiene_timestamp": False
            }
            
            try:
                data = response.json()
                # Buscar indicios del wrapper (metadata, timestamp, etc.)
                result["tiene_metadata"] = "metadata" in str(data).lower()
                result["tiene_timestamp"] = "timestamp" in str(data).lower()
                result["response_keys"] = list(data.keys()) if isinstance(data, dict) else []
            except:
                pass
            
            resultados.append(result)
            wrapper_ok = "✅" if result["tiene_metadata"] or result["tiene_timestamp"] else "⚠️"
            print(f"    {wrapper_ok} Status: {response.status_code}, Wrapper: {result['tiene_metadata']}")
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            resultados.append({"endpoint": url, "error": str(e), "exito": False})
    
    return resultados

def test_cosmos_db():
    """Prueba que Cosmos DB esté funcionando"""
    print("\nPRUEBA 4: Verificacion de Cosmos DB")
    
    try:
        response = requests.get(f"{BASE_URL}/api/verificar-cosmos", timeout=20)
        
        result = {
            "status_code": response.status_code,
            "exito": response.status_code == 200,
            "cosmos_conectado": False,
            "puede_escribir": False,
            "puede_leer": False
        }
        
        try:
            data = response.json()
            result["cosmos_conectado"] = data.get("cosmos_conectado", False)
            result["puede_escribir"] = data.get("puede_escribir", False)
            result["puede_leer"] = data.get("puede_leer", False)
            result["detalles"] = data.get("detalles", {})
            
            print(f"  ✅ Cosmos conectado: {result['cosmos_conectado']}")
            print(f"  ✅ Puede escribir: {result['puede_escribir']}")
            print(f"  ✅ Puede leer: {result['puede_leer']}")
            
        except Exception as e:
            print(f"  ❌ Error parseando respuesta: {e}")
            result["parse_error"] = str(e)
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error conectando: {e}")
        return {"error": str(e), "exito": False}

def test_app_insights():
    """Prueba que Application Insights esté funcionando"""
    print("\nPRUEBA 5: Verificacion de Application Insights")
    
    try:
        response = requests.get(f"{BASE_URL}/api/verificar-app-insights", timeout=20)
        
        result = {
            "status_code": response.status_code,
            "exito": response.status_code == 200,
            "app_insights_conectado": False,
            "tiene_datos": False
        }
        
        try:
            data = response.json()
            result["app_insights_conectado"] = data.get("exito", False)
            result["tiene_datos"] = data.get("eventos_count", 0) > 0
            result["metodo_parseo"] = data.get("metodo_parseo")
            result["detalles"] = {
                "eventos_count": data.get("eventos_count", 0),
                "workspace_id": data.get("workspace_id", "no_definido")[:20] + "..."
            }
            
            print(f"  ✅ App Insights conectado: {result['app_insights_conectado']}")
            print(f"  ✅ Tiene datos: {result['tiene_datos']}")
            print(f"  ✅ Método parseo: {result['metodo_parseo']}")
            
        except Exception as e:
            print(f"  ❌ Error parseando respuesta: {e}")
            result["parse_error"] = str(e)
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error conectando: {e}")
        return {"error": str(e), "exito": False}

def test_verificar_sistema():
    """Prueba que verificar-sistema esté funcionando"""
    print("\n🧪 PRUEBA 6: Verificación del sistema completo")
    
    try:
        response = requests.get(f"{BASE_URL}/api/verificar-sistema", timeout=20)
        
        result = {
            "status_code": response.status_code,
            "exito": response.status_code == 200,
            "metricas_sistema": False,
            "storage_conectado": False,
            "cache_activo": False
        }
        
        try:
            data = response.json()
            result["metricas_sistema"] = "cpu_percent" in data and "memoria" in data
            result["storage_conectado"] = data.get("storage_connected", False)
            result["cache_activo"] = data.get("cache_size", 0) >= 0
            result["ambiente"] = data.get("ambiente", "desconocido")
            result["detalles"] = {
                "cpu_percent": data.get("cpu_percent"),
                "cache_size": data.get("cache_size"),
                "python_version": data.get("python_version")
            }
            
            print(f"  ✅ Métricas sistema: {result['metricas_sistema']}")
            print(f"  ✅ Storage conectado: {result['storage_conectado']}")
            print(f"  ✅ Cache activo: {result['cache_activo']}")
            print(f"  ✅ Ambiente: {result['ambiente']}")
            
        except Exception as e:
            print(f"  ❌ Error parseando respuesta: {e}")
            result["parse_error"] = str(e)
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error conectando: {e}")
        return {"error": str(e), "exito": False}

def test_guardado_cosmos():
    """Prueba que los comandos se guarden en Cosmos DB"""
    print("\n🧪 PRUEBA 7: Guardado en Cosmos DB")
    
    # Ejecutar un comando que debería guardarse
    comando_test = {"comando": "account show"}
    
    try:
        print("  Ejecutando comando para probar guardado...")
        response = requests.post(
            f"{BASE_URL}/api/ejecutar-cli",
            json=comando_test,
            headers=HEADERS,
            timeout=15
        )
        
        print(f"  Comando ejecutado, status: {response.status_code}")
        
        # Esperar un poco para que se guarde
        time.sleep(2)
        
        # Verificar si se guardó consultando el estado del sistema
        print("  Verificando si se guardó en memoria semántica...")
        response_memoria = requests.get(f"{BASE_URL}/api/contexto-agente", timeout=15)
        
        result = {
            "comando_ejecutado": response.status_code == 200,
            "memoria_consultada": response_memoria.status_code == 200,
            "evidencia_guardado": False
        }
        
        if response_memoria.status_code == 200:
            try:
                data_memoria = response_memoria.json()
                # Buscar evidencia de que se guardó algo
                result["evidencia_guardado"] = (
                    data_memoria.get("total_interacciones", 0) > 0 or
                    "interacciones" in str(data_memoria).lower()
                )
                result["detalles_memoria"] = {
                    "total_interacciones": data_memoria.get("total_interacciones", 0),
                    "exito": data_memoria.get("exito", False)
                }
                
                print(f"  ✅ Evidencia de guardado: {result['evidencia_guardado']}")
                
            except Exception as e:
                print(f"  ❌ Error parseando memoria: {e}")
                result["parse_error"] = str(e)
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error en prueba: {e}")
        return {"error": str(e), "exito": False}

def generar_reporte(resultados):
    """Genera reporte final de todas las pruebas"""
    print("\n" + "="*60)
    print("📋 REPORTE FINAL DE PRUEBAS")
    print("="*60)
    
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "resumen": {},
        "detalles": resultados
    }
    
    # Calcular métricas generales
    total_pruebas = len(resultados)
    pruebas_exitosas = sum(1 for r in resultados.values() if r.get("exito_general", False))
    
    print(f"🎯 Pruebas ejecutadas: {total_pruebas}")
    print(f"✅ Pruebas exitosas: {pruebas_exitosas}")
    print(f"❌ Pruebas fallidas: {total_pruebas - pruebas_exitosas}")
    print(f"📊 Tasa de éxito: {(pruebas_exitosas/total_pruebas)*100:.1f}%")
    
    # Detalles por prueba
    for nombre, resultado in resultados.items():
        status = "✅" if resultado.get("exito_general") else "❌"
        print(f"\n{status} {nombre}:")
        
        if "adaptabilidad" in nombre:
            exitosos = sum(1 for r in resultado.get("resultados", []) if r.get("exito"))
            total = len(resultado.get("resultados", []))
            print(f"   Comandos procesados: {exitosos}/{total}")
            
        elif "errores" in nombre:
            correctos = sum(1 for r in resultado.get("resultados", []) if r.get("manejo_correcto"))
            total = len(resultado.get("resultados", []))
            print(f"   Errores manejados: {correctos}/{total}")
            
        elif "cosmos" in nombre:
            print(f"   Conectado: {resultado.get('cosmos_conectado', False)}")
            print(f"   Puede escribir: {resultado.get('puede_escribir', False)}")
            
        elif "insights" in nombre:
            print(f"   Conectado: {resultado.get('app_insights_conectado', False)}")
            print(f"   Tiene datos: {resultado.get('tiene_datos', False)}")
            
        elif "sistema" in nombre:
            print(f"   Métricas: {resultado.get('metricas_sistema', False)}")
            print(f"   Storage: {resultado.get('storage_conectado', False)}")
    
    # Guardar reporte
    with open("reporte_pruebas.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: reporte_pruebas.json")
    return reporte

def main():
    """Ejecuta todas las pruebas"""
    print("INICIANDO PRUEBAS COMPLETAS DEL SISTEMA")
    print(f"URL Base: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    resultados = {}
    
    # Ejecutar todas las pruebas
    try:
        # Prueba 1: Adaptabilidad
        result1 = test_ejecutar_cli_adaptabilidad()
        exitosos = sum(1 for r in result1 if r.get("exito"))
        resultados["adaptabilidad_ejecutar_cli"] = {
            "exito_general": exitosos >= len(result1) * 0.7,  # 70% éxito mínimo
            "resultados": result1
        }
        
        # Prueba 2: Manejo de errores
        result2 = test_manejo_errores_robusto()
        correctos = sum(1 for r in result2 if r.get("manejo_correcto"))
        resultados["manejo_errores_robusto"] = {
            "exito_general": correctos >= len(result2) * 0.8,  # 80% éxito mínimo
            "resultados": result2
        }
        
        # Prueba 3: Wrapper automático
        result3 = test_wrapper_automatico()
        resultados["wrapper_automatico"] = {
            "exito_general": any(r.get("tiene_metadata") or r.get("tiene_timestamp") for r in result3),
            "resultados": result3
        }
        
        # Prueba 4: Cosmos DB
        result4 = test_cosmos_db()
        resultados["cosmos_db"] = {
            "exito_general": result4.get("cosmos_conectado", False),
            **result4
        }
        
        # Prueba 5: Application Insights
        result5 = test_app_insights()
        resultados["app_insights"] = {
            "exito_general": result5.get("app_insights_conectado", False),
            **result5
        }
        
        # Prueba 6: Verificar sistema
        result6 = test_verificar_sistema()
        resultados["verificar_sistema"] = {
            "exito_general": result6.get("metricas_sistema", False),
            **result6
        }
        
        # Prueba 7: Guardado en Cosmos
        result7 = test_guardado_cosmos()
        resultados["guardado_cosmos"] = {
            "exito_general": result7.get("evidencia_guardado", False),
            **result7
        }
        
    except KeyboardInterrupt:
        print("\n⚠️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando pruebas: {e}")
    
    # Generar reporte final
    generar_reporte(resultados)

if __name__ == "__main__":
    main()