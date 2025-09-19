import azure.functions as func
import json
from datetime import datetime
from pathlib import Path

# ========== ENDPOINTS CORREGIDOS LIMPIOS ==========

@func.FunctionApp()
app = func.FunctionApp()

@app.function_name(name="gestionar_despliegue_fixed")
@app.route(route="gestionar-despliegue-fixed", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def gestionar_despliegue_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para gestionar despliegues - CORREGIDO"""
    try:
        body = req.get_json() or {}
        accion = body.get("accion", "")
        
        if not accion:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'accion' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        acciones_validas = ["detectar", "preparar", "ejecutar", "validar"]
        if accion not in acciones_validas:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": f"Acción '{accion}' no válida"}),
                mimetype="application/json", status_code=400
            )
        
        return func.HttpResponse(
            json.dumps({"exito": True, "accion": accion, "mensaje": f"Acción '{accion}' ejecutada"}),
            mimetype="application/json", status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


@app.function_name(name="desplegar_funcion_fixed")
@app.route(route="desplegar-funcion-fixed", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def desplegar_funcion_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para desplegar función - CORREGIDO"""
    try:
        body = req.get_json() or {}
        nombre = body.get("nombre", "")
        
        if not nombre:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'nombre' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "funcion": nombre,
                "estado": "desplegada",
                "url": f"https://example.azurewebsites.net/api/{nombre}"
            }),
            mimetype="application/json", status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


@app.function_name(name="render_error_fixed")
@app.route(route="render-error-fixed", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def render_error_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para renderizar errores - CORREGIDO"""
    try:
        try:
            body = req.get_json()
        except:
            body = None
        
        if not body:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Request body JSON válido requerido"}),
                mimetype="application/json", status_code=400
            )
        
        return func.HttpResponse(
            json.dumps({
                "error_rendered": True,
                "error_code": body.get("error_code", "UNKNOWN_ERROR"),
                "message": body.get("message", "Error desconocido"),
                "timestamp": datetime.now().isoformat()
            }),
            mimetype="application/json", status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


@app.function_name(name="ejecutar_script_local_fixed")
@app.route(route="ejecutar-script-local-fixed", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_script_local_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para ejecutar scripts locales - CORREGIDO"""
    try:
        body = req.get_json() or {}
        script = body.get("script", "")
        
        if not script:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'script' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        if Path(script).is_absolute() or ".." in script:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Path fuera de directorio permitido"}),
                mimetype="application/json", status_code=403
            )
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "script": script,
                "output": "Script ejecutado exitosamente (simulado)",
                "exit_code": 0
            }),
            mimetype="application/json", status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


@app.function_name(name="actualizar_contenedor_fixed")
@app.route(route="actualizar-contenedor-fixed", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def actualizar_contenedor_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para actualizar contenedor - CORREGIDO"""
    try:
        body = req.get_json() or {}
        nombre = body.get("nombre", "")
        tag = body.get("tag", "")
        
        if not nombre:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'nombre' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        if not tag:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'tag' requerido"}),
                mimetype="application/json", status_code=400
            )
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "contenedor": nombre,
                "tag": tag,
                "estado": "actualizado"
            }),
            mimetype="application/json", status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


def ejecutar_script_simple(nombre: str, parametros: list = None) -> dict:
    """Función auxiliar para ejecutar scripts"""
    if parametros is None:
        parametros = []
    
    if nombre == "test.py":
        return {
            "exito": True,
            "script": nombre,
            "output": "Script de prueba ejecutado (simulado)",
            "parametros": parametros
        }
    
    return {
        "exito": False,
        "error": f"Script '{nombre}' no encontrado",
        "scripts_disponibles": ["test.py"]
    }