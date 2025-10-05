#!/usr/bin/env python3
"""
Endpoints de diagnóstico avanzado para automonitoreo inteligente
"""
import azure.functions as func
import json
import os
import platform
import subprocess
import datetime
from datetime import datetime

# Agregar estos endpoints al final de function_app.py

@app.function_name(name="verificar_estado_sistema")
@app.route(route="verificar-sistema", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def verificar_estado_sistema(req: func.HttpRequest) -> func.HttpResponse:
    """Autodiagnóstico completo del sistema"""
    try:
        import psutil
        
        estado = {
            "timestamp": datetime.utcnow().isoformat(),
            "sistema": platform.system(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memoria": psutil.virtual_memory()._asdict(),
            "disco": psutil.disk_usage("/" if platform.system() != "Windows" else "C:\\")._asdict(),
            "python_version": platform.python_version(),
            "app_service_plan": os.environ.get("WEBSITE_SKU", "Unknown"),
            "app_insights": bool(os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")),
            "cosmos_endpoint": os.environ.get("COSMOSDB_ENDPOINT", "no_definido"),
            "storage_connected": bool(os.environ.get("AzureWebJobsStorage")),
            "ambiente": "Azure" if os.environ.get("WEBSITE_SITE_NAME") else "Local"
        }
        
        return func.HttpResponse(
            json.dumps(estado, indent=2),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "tipo_error": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="verificar_app_insights")
@app.route(route="verificar-app-insights", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def verificar_app_insights(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica telemetría de Application Insights"""
    try:
        app_name = os.environ.get("WEBSITE_SITE_NAME", "copiloto-semantico-ai")
        comando = (
            f"az monitor app-insights query "
            f"--app {app_name} "
            f"--analytics-query \"customEvents | take 5\" -o json"
        )
        
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                return func.HttpResponse(
                    json.dumps({
                        "exito": True,
                        "telemetria_activa": len(data.get("tables", [])) > 0,
                        "eventos_recientes": data,
                        "app_name": app_name
                    }),
                    mimetype="application/json"
                )
            except json.JSONDecodeError:
                return func.HttpResponse(
                    json.dumps({
                        "exito": True,
                        "raw_output": result.stdout,
                        "app_name": app_name
                    }),
                    mimetype="application/json"
                )
        else:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": result.stderr,
                    "sugerencia": "Verificar configuración de Application Insights"
                }),
                mimetype="application/json",
                status_code=200
            )
            
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "tipo_error": type(e).__name__
            }),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="verificar_cosmos")
@app.route(route="verificar-cosmos", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def verificar_cosmos(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica conectividad y escrituras en CosmosDB"""
    try:
        from azure.cosmos import CosmosClient
        
        endpoint = os.environ.get("COSMOSDB_ENDPOINT")
        key = os.environ.get("COSMOSDB_KEY")
        database = os.environ.get("COSMOSDB_DATABASE", "copiloto-db")
        container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")
        
        if not endpoint or not key:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Credenciales de CosmosDB no configuradas",
                    "configuracion": {
                        "endpoint": bool(endpoint),
                        "key": bool(key)
                    }
                }),
                mimetype="application/json",
                status_code=200
            )
        
        client = CosmosClient(endpoint, key)
        db = client.get_database_client(database)
        container = db.get_container_client(container_name)
        
        # Consultar últimos registros
        items = list(container.query_items(
            "SELECT TOP 5 * FROM c ORDER BY c._ts DESC",
            enable_cross_partition_query=True
        ))
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "cosmos_conectado": True,
                "registros_encontrados": len(items),
                "ultimo_registro": items[0] if items else None,
                "estado": "funcionando" if items else "sin_escrituras",
                "database": database,
                "container": container_name
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "cosmos_conectado": False,
                "error": str(e),
                "tipo_error": type(e).__name__,
                "sugerencia": "Verificar credenciales y configuración de CosmosDB"
            }),
            mimetype="application/json",
            status_code=200
        )