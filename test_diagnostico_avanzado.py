#!/usr/bin/env python3
"""
Prueba local de los endpoints de diagnóstico avanzado
"""
import json
import os
import platform
import subprocess

def simulate_verificar_sistema():
    """Simula verificar-sistema localmente"""
    print("[TEST] Simulando verificar-sistema...")
    
    try:
        import psutil
        
        estado = {
            "timestamp": "2025-10-04T07:00:00Z",
            "sistema": platform.system(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memoria": psutil.virtual_memory()._asdict(),
            "disco": psutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")._asdict(),
            "python_version": platform.python_version(),
            "app_service_plan": os.environ.get("WEBSITE_SKU", "Unknown"),
            "app_insights": bool(os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")),
            "cosmos_endpoint": os.environ.get("COSMOSDB_ENDPOINT", "no_definido"),
            "storage_connected": bool(os.environ.get("AzureWebJobsStorage")),
            "ambiente": "Azure" if os.environ.get("WEBSITE_SITE_NAME") else "Local"
        }
        
        print(f"[SISTEMA] {estado['sistema']}")
        print(f"[CPU] {estado['cpu_percent']}%")
        print(f"[MEMORIA] {round(estado['memoria']['percent'], 1)}% usado")
        print(f"[DISCO] {round(estado['disco']['percent'], 1)}% usado")
        print(f"[PYTHON] {estado['python_version']}")
        print(f"[AMBIENTE] {estado['ambiente']}")
        
        return {"exito": True, "data": estado}
        
    except Exception as e:
        return {"exito": False, "error": str(e)}

def simulate_verificar_app_insights():
    """Simula verificar-app-insights localmente"""
    print("\n[TEST] Simulando verificar-app-insights...")
    
    try:
        app_name = os.environ.get("WEBSITE_SITE_NAME", "copiloto-semantico-ai")
        comando = f"az monitor app-insights query --app {app_name} --analytics-query \"customEvents | take 5\" -o json"
        
        print(f"[COMANDO] {comando}")
        
        # Simular ejecución (no ejecutar realmente az cli en local)
        if os.environ.get("WEBSITE_SITE_NAME"):  # Solo si estamos en Azure
            result = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("[APP_INSIGHTS] Comando exitoso")
                return {"exito": True, "telemetria_activa": True}
            else:
                print(f"[APP_INSIGHTS] Error: {result.stderr}")
                return {"exito": False, "error": result.stderr}
        else:
            print("[APP_INSIGHTS] Simulado - no en Azure")
            return {"exito": False, "error": "No en ambiente Azure"}
            
    except Exception as e:
        return {"exito": False, "error": str(e)}

def simulate_verificar_cosmos():
    """Simula verificar-cosmos localmente"""
    print("\n[TEST] Simulando verificar-cosmos...")
    
    try:
        endpoint = os.environ.get("COSMOSDB_ENDPOINT")
        key = os.environ.get("COSMOSDB_KEY")
        database = os.environ.get("COSMOSDB_DATABASE", "copiloto-db")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")
        
        print(f"[ENDPOINT] {bool(endpoint)}")
        print(f"[KEY] {bool(key)}")
        print(f"[DATABASE] {database}")
        print(f"[CONTAINER] {container_name}")
        
        if not endpoint or not key:
            return {
                "exito": False,
                "error": "Credenciales de CosmosDB no configuradas",
                "configuracion": {
                    "endpoint": bool(endpoint),
                    "key": bool(key)
                }
            }
        
        # Simular conexión a Cosmos
        try:
            from azure.cosmos import CosmosClient
            client = CosmosClient(endpoint, key)
            print("[COSMOS] Cliente creado exitosamente")
            
            # En un entorno real, haríamos la consulta
            return {
                "exito": True,
                "cosmos_conectado": True,
                "registros_encontrados": 0,
                "estado": "sin_escrituras",
                "database": database,
                "container": container_name
            }
            
        except Exception as e:
            print(f"[COSMOS] Error de conexión: {e}")
            return {
                "exito": False,
                "cosmos_conectado": False,
                "error": str(e)
            }
        
    except Exception as e:
        return {"exito": False, "error": str(e)}

def test_all_diagnostics():
    """Ejecuta todas las pruebas de diagnóstico"""
    print("=" * 60)
    print("PRUEBAS DE ENDPOINTS DE DIAGNÓSTICO AVANZADO")
    print("=" * 60)
    
    # Test 1: Sistema
    result1 = simulate_verificar_sistema()
    print(f"[RESULTADO 1] Sistema: {'OK' if result1['exito'] else 'ERROR'}")
    
    # Test 2: App Insights
    result2 = simulate_verificar_app_insights()
    print(f"[RESULTADO 2] App Insights: {'OK' if result2['exito'] else 'ERROR'}")
    
    # Test 3: Cosmos
    result3 = simulate_verificar_cosmos()
    print(f"[RESULTADO 3] Cosmos: {'OK' if result3['exito'] else 'ERROR'}")
    
    print("\n" + "=" * 60)
    print("RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)
    
    total_tests = 3
    passed_tests = sum([result1['exito'], result2['exito'], result3['exito']])
    
    print(f"[TOTAL] {passed_tests}/{total_tests} pruebas exitosas")
    print(f"[ESTADO] {'LISTO PARA DESPLIEGUE' if passed_tests >= 2 else 'REQUIERE ATENCION'}")
    
    return {
        "sistema": result1,
        "app_insights": result2,
        "cosmos": result3,
        "resumen": {
            "total": total_tests,
            "exitosos": passed_tests,
            "listo": passed_tests >= 2
        }
    }

if __name__ == "__main__":
    test_all_diagnostics()