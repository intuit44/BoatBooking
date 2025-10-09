#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir y validar funciones del sistema
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def verificar_wrapper_memoria():
    """Verifica que el wrapper de memoria esté aplicado"""
    print("Verificando wrapper automatico de memoria...")
    
    function_app_path = Path("function_app.py")
    if not function_app_path.exists():
        print("ERROR: function_app.py no encontrado")
        return False
    
    content = function_app_path.read_text(encoding='utf-8')
    
    # Buscar evidencia del wrapper
    wrapper_indicators = [
        "apply_memory_wrapper",
        "memory_route_wrapper",
        "memory_service.log_semantic_event",
        "@app.route"
    ]
    
    found_indicators = []
    for indicator in wrapper_indicators:
        if indicator in content:
            found_indicators.append(indicator)
    
    print(f"OK: Indicadores encontrados: {found_indicators}")
    return len(found_indicators) >= 2

def verificar_ejecutar_cli():
    """Verifica que ejecutar-cli esté completo"""
    print("Verificando funcion ejecutar_cli_http...")
    
    function_app_path = Path("function_app.py")
    content = function_app_path.read_text(encoding='utf-8')
    
    # Buscar la función
    if "def ejecutar_cli_http" not in content:
        print("ERROR: Funcion ejecutar_cli_http no encontrada")
        return False
    
    # Verificar elementos clave
    elementos_clave = [
        "comando = body.get(\"comando\")",
        "az_binary = None",
        "subprocess.run",
        "json.dumps",
        "status_code"
    ]
    
    elementos_encontrados = []
    for elemento in elementos_clave:
        if elemento in content:
            elementos_encontrados.append(elemento)
    
    print(f"OK: Elementos clave: {len(elementos_encontrados)}/{len(elementos_clave)}")
    return len(elementos_encontrados) >= 4

def corregir_analizar_error_cli():
    """Corrige la función _analizar_error_cli si está mal"""
    print("Corrigiendo funcion _analizar_error_cli...")
    
    funcion_corregida = '''
def _analizar_error_cli(intentos_log: list, comando: str) -> dict:
    """Analiza errores de CLI para detectar parámetros faltantes"""
    if not intentos_log:
        return {"tipo_error": "NoLogs", "campo_faltante": None}
    
    for intento in intentos_log:
        stderr = intento.get("stderr", "").lower()
        
        # Patrones comunes de Azure CLI
        if "resource group" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "resourceGroup"}
        elif "location" in stderr and ("required" in stderr or "must be specified" in stderr):
            return {"tipo_error": "MissingParameter", "campo_faltante": "location"}
        elif "subscription" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "subscriptionId"}
        elif "template" in stderr and ("not found" in stderr or "required" in stderr):
            return {"tipo_error": "MissingParameter", "campo_faltante": "template"}
        elif "storage account" in stderr and "required" in stderr:
            return {"tipo_error": "MissingParameter", "campo_faltante": "storageAccount"}
        elif "authentication" in stderr or "login" in stderr:
            return {"tipo_error": "AuthenticationError", "campo_faltante": "credentials"}
        elif "not found" in stderr and "command" in stderr:
            return {"tipo_error": "CommandNotFound", "campo_faltante": "command"}
    
    return {"tipo_error": "GenericError", "campo_faltante": None}
'''
    
    return funcion_corregida

def verificar_cosmos_completo():
    """Verifica que verificar_cosmos esté completo"""
    print("Verificando funcion verificar_cosmos...")
    
    function_app_path = Path("function_app.py")
    content = function_app_path.read_text(encoding='utf-8')
    
    # Buscar la función completa
    start_marker = "def verificar_cosmos"
    end_marker = "def "  # Próxima función
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("ERROR: Funcion verificar_cosmos no encontrada")
        return False
    
    # Buscar el final de la función
    lines = content[start_idx:].split('\n')
    function_lines = []
    indent_level = None
    
    for line in lines:
        if line.strip().startswith("def ") and function_lines:
            # Nueva función encontrada, terminar
            break
        function_lines.append(line)
        
        # Determinar nivel de indentación
        if line.strip() and indent_level is None and not line.startswith("def"):
            indent_level = len(line) - len(line.lstrip())
    
    function_content = '\n'.join(function_lines)
    
    # Verificar elementos clave
    elementos_cosmos = [
        "CosmosClient",
        "endpoint",
        "container.query_items",
        "json.dumps",
        "return func.HttpResponse"
    ]
    
    elementos_encontrados = []
    for elemento in elementos_cosmos:
        if elemento in function_content:
            elementos_encontrados.append(elemento)
    
    print(f"OK: Elementos Cosmos: {len(elementos_encontrados)}/{len(elementos_cosmos)}")
    
    # Verificar si la función está completa (tiene return)
    tiene_return = "return func.HttpResponse" in function_content
    print(f"OK: Funcion completa: {tiene_return}")
    
    return len(elementos_encontrados) >= 3 and tiene_return

def generar_funcion_cosmos_completa():
    """Genera una función verificar_cosmos completa"""
    return '''
@app.function_name(name="verificar_cosmos")
@app.route(route="verificar-cosmos", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def verificar_cosmos(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica conectividad y escrituras en CosmosDB usando clave o MI"""
    endpoint = os.environ.get("COSMOSDB_ENDPOINT")
    key = os.environ.get("COSMOSDB_KEY")
    database = os.environ.get("COSMOSDB_DATABASE", "copiloto-db")
    container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")

    if not endpoint:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": "Endpoint de CosmosDB no configurado",
                "configuracion": {"endpoint": False}
            }),
            mimetype="application/json",
            status_code=200
        )

    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        
        auth_method = "MI"
        client = None
        
        # Intentar con clave primero
        if key:
            try:
                client = CosmosClient(endpoint, key)
                auth_method = "clave"
            except Exception:
                client = None

        # Fallback a Managed Identity
        if not client:
            try:
                credential = DefaultAzureCredential()
                client = CosmosClient(endpoint, credential)
                auth_method = "MI"
            except Exception as e:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": f"No se pudo autenticar con Cosmos: {str(e)}",
                        "auth_method": "failed"
                    }),
                    mimetype="application/json",
                    status_code=500
                )

        # Probar conexión
        db = client.get_database_client(database)
        container = db.get_container_client(container_name)
        
        # Test de lectura
        items = list(container.query_items(
            "SELECT TOP 5 * FROM c ORDER BY c._ts DESC",
            enable_cross_partition_query=True
        ))
        
        # Test de escritura
        test_item = {
            "id": f"test-{int(time.time())}",
            "tipo": "test_conectividad",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        container.create_item(test_item)
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "cosmos_conectado": True,
                "puede_leer": True,
                "puede_escribir": True,
                "auth_method": auth_method,
                "items_recientes": len(items),
                "database": database,
                "container": container_name,
                "endpoint": endpoint[:50] + "..." if len(endpoint) > 50 else endpoint
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__,
                "cosmos_conectado": False,
                "puede_leer": False,
                "puede_escribir": False
            }),
            mimetype="application/json",
            status_code=500
        )
'''

def main():
    """Ejecuta todas las verificaciones y correcciones"""
    print("INICIANDO VERIFICACION Y CORRECCION DEL SISTEMA")
    print("="*60)
    
    resultados = {}
    
    # Verificar wrapper
    resultados["wrapper_memoria"] = verificar_wrapper_memoria()
    
    # Verificar ejecutar-cli
    resultados["ejecutar_cli"] = verificar_ejecutar_cli()
    
    # Verificar cosmos
    resultados["cosmos_completo"] = verificar_cosmos_completo()
    
    # Mostrar resumen
    print("\nRESUMEN DE VERIFICACIONES:")
    for nombre, resultado in resultados.items():
        status = "OK" if resultado else "ERROR"
        print(f"{status} {nombre}: {'OK' if resultado else 'NECESITA CORRECCIÓN'}")
    
    # Generar correcciones si es necesario
    if not resultados["cosmos_completo"]:
        print("\nGenerando correccion para verificar_cosmos...")
        cosmos_fix = generar_funcion_cosmos_completa()
        
        with open("cosmos_fix.py", "w", encoding="utf-8") as f:
            f.write(cosmos_fix)
        print("OK: Correccion guardada en cosmos_fix.py")
    
    # Generar corrección para _analizar_error_cli
    print("\nGenerando correccion para _analizar_error_cli...")
    error_cli_fix = corregir_analizar_error_cli()
    
    with open("analizar_error_cli_fix.py", "w", encoding="utf-8") as f:
        f.write(error_cli_fix)
    print("OK: Correccion guardada en analizar_error_cli_fix.py")
    
    # Resumen final
    total_ok = sum(resultados.values())
    total_checks = len(resultados)
    
    print(f"\nRESULTADO FINAL: {total_ok}/{total_checks} verificaciones OK")
    
    if total_ok == total_checks:
        print("Todas las funciones estan correctas!")
    else:
        print("Algunas funciones necesitan correccion. Revisa los archivos generados.")
    
    return resultados

if __name__ == "__main__":
    main()