# simbolo_gpt4_api.py
import os
import sys
import subprocess
import json
import yaml
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_processor import procesar_lenguaje_natural

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR 

sys.path.append(str(BASE_DIR))

def ruta_relativa(*subrutas):
    """Devuelve una ruta absoluta desde el directorio BASE_DIR"""
    return str(BASE_DIR.joinpath(*subrutas).resolve())

# ===================== IMPORTACIONES PROPIAS =====================
from ejecutor_sistemico import procesar_accion_simbolica, ejecutar_accion

app = Flask(__name__)
CORS(app)

# Logger simple
def log(mensaje, tipo="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{tipo}] {mensaje}")

# Definición de agentes especializados
AGENTES = {
    "dynamodb_creator": {
        "descripcion": "Crea y gestiona tablas DynamoDB en serverless.yml",
        "capacidades": ["crear_tabla", "agregar_indices", "configurar_iam", "eliminar_tabla"]
    },
    "function_registrar": {
        "descripcion": "Registra funciones Lambda en serverless.yml",
        "capacidades": ["registrar_funcion", "eliminar_funcion", "actualizar_eventos"]
    },
    "code_generator": {
        "descripcion": "Genera código para handlers, utils y tests",
        "capacidades": ["crear_handler", "crear_util", "generar_test", "fix_sintaxis"]
    },
    "file_manager": {
        "descripcion": "Lee y modifica archivos del proyecto",
        "capacidades": ["leer_archivo", "escribir_archivo", "crear_directorio", "listar_archivos"]
    },
    "serverless_deployer": {
        "descripcion": "Gestiona deployments de Serverless",
        "capacidades": ["deploy", "remove", "logs", "info"]
    }
}

# ===================== RUTAS PRINCIPALES =====================


@app.route("/codegpt/execute", methods=["POST", "GET"])
def ejecutar_desde_codegpt():
    """Endpoint específico para ejecución desde CodeGPT"""
    log(f"🔥 MÉTODO RECIBIDO: {request.method}", "DEBUG")

    if request.method != "POST":
        return jsonify({
            "success": False,
            "output": f"❌ Método no permitido: {request.method} (se esperaba POST)"
        }), 405

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON payload provided"}), 400

        # Log para debugging
        log(f"CodeGPT Request: {json.dumps(data, indent=2)}", "DEBUG")
        
        # Extraer comando del formato CodeGPT
        comando_raw = data.get("command", "")
        contexto = data.get("context", {})
        
        # Parsear el comando para determinar la acción
        accion_data = parsear_comando_codegpt(comando_raw, contexto)
        
        # Log del resultado del parseo
        log(f"Acción parseada: {json.dumps(accion_data, indent=2)}", "DEBUG")
        
        # Si hay un error en el parseo
        if "error" in accion_data:
            return jsonify({
                "success": False,
                "output": f"❌ Error: {accion_data['error']}",
                "metadata": {
                    "ejecutado_en": datetime.now().isoformat()
                }
            }), 400
        
        # Determinar cómo procesar la acción
        resultado = None
        
        try:
            # Si tiene un agente específico, procesarlo con ese agente
            if "agente" in accion_data and accion_data["agente"] != "default":
                agente = accion_data["agente"]
                accion = accion_data.get("accion")
                parametros = accion_data.get("parametros", {})
                
                log(f"Procesando con agente: {agente}, acción: {accion}", "DEBUG")
                
                # Procesar según el agente
                if agente == "dynamodb_creator":
                    resultado = procesar_dynamodb(accion, parametros)
                elif agente == "function_registrar":
                    resultado = procesar_funciones(accion, parametros)
                elif agente == "code_generator":
                    resultado = procesar_generacion_codigo(accion, parametros)
                elif agente == "file_manager":
                    resultado = procesar_archivos(accion, parametros)
                elif agente == "serverless_deployer":
                    resultado = procesar_serverless(accion, parametros)
                else:
                    resultado = {
                        "status": "error",
                        "error": f"Agente '{agente}' no reconocido"
                    }
            else:
                # Si no tiene agente, usar el procesador general
                resultado = procesar_accion_simbolica(accion_data)
            
            # Determinar si fue exitoso
            if resultado is not None:
                success = resultado.get("status") == "success" or resultado.get("estado") == "ok"
            else:
                success = False
            
            # Formatear respuesta para CodeGPT
            return jsonify({
                "success": success,
                "output": formatear_salida_codegpt(resultado),
                "metadata": {
                    "ejecutado_en": datetime.now().isoformat(),
                    "accion": accion_data.get("accion"),
                    "agente": accion_data.get("agente", "default")
                }
            })
            
        except Exception as e:
            log(f"Error procesando acción: {str(e)}", "ERROR")
            # Si hay un error en el procesamiento, devolver error formateado
            return jsonify({
                "success": False,
                "output": f"❌ Error al procesar: {str(e)}",
                "metadata": {
                    "ejecutado_en": datetime.now().isoformat(),
                    "accion": accion_data.get("accion"),
                    "agente": accion_data.get("agente", "default"),
                    "error_type": type(e).__name__
                }
            }), 500
        
    except Exception as e:
        log(f"Error en CodeGPT execute: {str(e)}", "ERROR")
        import traceback
        log(f"Traceback: {traceback.format_exc()}", "ERROR")
        return jsonify({
            "success": False,
            "error": str(e),
            "output": f"❌ Error general: {str(e)}"
        }), 500

def parsear_comando_codegpt(comando, contexto):
    """Parsea comandos desde CodeGPT con formatos [EXECUTE_*] y formato directo"""
    
    # Detectar formato [EXECUTE_COMMAND]
    if "[EXECUTE_COMMAND]" in comando and "[/EXECUTE_COMMAND]" in comando:
        inicio = comando.find("[EXECUTE_COMMAND]") + len("[EXECUTE_COMMAND]")
        fin = comando.find("[/EXECUTE_COMMAND]")
        comando_exec = comando[inicio:fin].strip()
        
        log(f"Parser: Detectado EXECUTE_COMMAND: {comando_exec}", "DEBUG")
        
        return {
            "accion": "ejecutar comando",
            "comando": comando_exec,
            "contexto": {
                "directorio_trabajo": contexto.get("workspace", os.getcwd()),
                "capturar_salida": True,
                "timeout": 30
            }
        }
    
    # Detectar formato [EXECUTE_SIMBOLICO]
    elif "[EXECUTE_SIMBOLICO]" in comando and "[/EXECUTE_SIMBOLICO]" in comando:
        inicio = comando.find("[EXECUTE_SIMBOLICO]") + len("[EXECUTE_SIMBOLICO]")
        fin = comando.find("[/EXECUTE_SIMBOLICO]")
        json_str = comando[inicio:fin].strip()
        
        log(f"Parser: Detectado EXECUTE_SIMBOLICO", "DEBUG")
        
        try:
            data = json.loads(json_str)

            # Normalizar si viene con 'command' en vez de 'comando'
            if "command" in data and "comando" not in data:
                data["comando"] = data.pop("command")

            # Inyectar acción si no viene definida
            if "accion" not in data and "comando" in data:
                data["accion"] = "ejecutar comando"

            # Inyectar contexto mínimo si no está presente
            if "contexto" not in data:
                data["contexto"] = {
                    "directorio_trabajo": os.getcwd(),
                    "capturar_salida": True,
                    "timeout": 30
                }

            return data

        except json.JSONDecodeError as e:
            log(f"Error parseando JSON en EXECUTE_SIMBOLICO: {e}", "ERROR")
            return {"error": "JSON inválido en EXECUTE_SIMBOLICO", "status": "error"}
    
    # Detectar formato [EXECUTE_FILE]
    elif "[EXECUTE_FILE]" in comando and "[/EXECUTE_FILE]" in comando:
        inicio = comando.find("[EXECUTE_FILE]") + len("[EXECUTE_FILE]")
        fin = comando.find("[/EXECUTE_FILE]")
        contenido = comando[inicio:fin].strip()
        
        log(f"Parser: Detectado EXECUTE_FILE", "DEBUG")
        
        # Extraer ruta y contenido
        lineas = contenido.split("\n")
        ruta = ""
        contenido_archivo = []
        en_contenido = False
        
        for linea in lineas:
            if linea.startswith("RUTA:"):
                ruta = linea.replace("RUTA:", "").strip()
            elif linea.startswith("CONTENIDO:"):
                en_contenido = True
            elif en_contenido:
                contenido_archivo.append(linea)
        
        return {
            "accion": "crear archivo",
            "ruta": ruta,
            "contenido": "\n".join(contenido_archivo),
            "metadatos": {"origen": "codegpt", "formato": "EXECUTE_FILE"}
        }
    
    # PARSER MEJORADO PARA FORMATO DIRECTO
    else:
        log(f"Parser: Sin formato EXECUTE_*, usando parser mejorado", "DEBUG")
        comando_lower = comando.lower()
        
        # Detectar comando directo con formato "@architect ejecutar: comando"
        if comando.startswith("@architect"):
            comando_sin_prefix = comando.replace("@architect", "").strip()
            
            # Buscar patrones como "ejecutar:" o "run:"
            if comando_sin_prefix.startswith("ejecutar:"):
                comando_exec = comando_sin_prefix.replace("ejecutar:", "").strip()
                log(f"Parser: Detectado comando directo con 'ejecutar:' -> {comando_exec}", "DEBUG")
                return {
                    "accion": "ejecutar comando",
                    "comando": comando_exec,
                    "contexto": {
                        "directorio_trabajo": contexto.get("workspace", os.getcwd()),
                        "capturar_salida": True,
                        "timeout": 30
                    }
                }
            elif comando_sin_prefix.startswith("run:"):
                comando_exec = comando_sin_prefix.replace("run:", "").strip()
                log(f"Parser: Detectado comando directo con 'run:' -> {comando_exec}", "DEBUG")
                return {
                    "accion": "ejecutar comando",
                    "comando": comando_exec,
                    "contexto": {
                        "directorio_trabajo": contexto.get("workspace", os.getcwd()),
                        "capturar_salida": True,
                        "timeout": 30
                    }
                }
        
        # Detectar tipo de comando con el formato antiguo (CORREGIDO)
        if "crear archivo" in comando_lower or "create file" in comando_lower:
            # Extraer nombre de archivo y contenido
            partes = comando.split("```")
            if len(partes) >= 2:
                # Buscar el nombre del archivo
                lineas = comando.split("\n")
                ruta = ""
                for linea in lineas:
                    if "archivo:" in linea or "file:" in linea:
                        ruta = linea.split(":")[-1].strip()
                        break
                
                contenido = partes[1].strip()
                if contenido.startswith("python") or contenido.startswith("javascript"):
                    contenido = "\n".join(contenido.split("\n")[1:])
                    
                return {
                    "accion": "crear archivo",
                    "ruta": ruta or "nuevo_archivo.txt",
                    "contenido": contenido,
                    "metadatos": {"origen": "codegpt"}
                }
        
        elif "ejecutar" in comando_lower or "run" in comando_lower:
            # Extraer comando a ejecutar
            comando_exec = ""
            
            if "```" in comando:
                comando_exec = comando.split("```")[1].strip()
                if comando_exec.startswith("bash") or comando_exec.startswith("shell"):
                    comando_exec = "\n".join(comando_exec.split("\n")[1:])
            else:
                # Buscar patrones como "ejecutar: comando" o "run: comando"
                if "ejecutar:" in comando_lower:
                    idx = comando_lower.find("ejecutar:")
                    comando_exec = comando[idx + len("ejecutar:"):].strip()
                elif "run:" in comando_lower:
                    idx = comando_lower.find("run:")
                    comando_exec = comando[idx + len("run:"):].strip()
                else:
                    # Si contiene "ejecutar" pero sin ":", tomar todo después de "ejecutar"
                    if "ejecutar" in comando_lower:
                        idx = comando_lower.find("ejecutar")
                        comando_exec = comando[idx + len("ejecutar"):].strip()
                    else:
                        comando_exec = comando
            
            log(f"Parser: Comando extraído -> {comando_exec}", "DEBUG")
            
            return {
                "accion": "ejecutar comando",
                "comando": comando_exec,
                "contexto": {
                    "directorio_trabajo": contexto.get("workspace", os.getcwd()),
                    "capturar_salida": True,
                    "timeout": 30
                }
            }
        
        elif "deploy" in comando_lower:
            return {
                "agente": "serverless_deployer",
                "accion": "deploy",
                "parametros": {
                    "stage": "dev",
                    "region": "us-east-1"
                }
            }
        
        elif "generar" in comando_lower and ("handler" in comando_lower or "función" in comando_lower):
            # Extraer detalles de generación
            return {
                "agente": "code_generator",
                "accion": "crear_handler",
                "parametros": {
                    "archivo": extraer_parametro(comando, "archivo:", "src/handlers/nuevo.js"),
                    "funciones": extraer_funciones(comando),
                    "tipo": "rest"
                }
            }
        
        # Default: intentar ejecutar como comando directo
        log(f"Parser: No se detectó formato específico, ejecutando como comando directo", "DEBUG")
        return {
            "accion": "ejecutar comando",
            "comando": comando,
            "contexto": contexto
        }
    
def formatear_salida_codegpt(resultado):
    """Formatea la salida para que sea legible en CodeGPT"""
    # Manejar diferentes formatos de resultado
    if resultado.get("status") == "success" or resultado.get("estado") == "ok":
        # Para archivos
        if "archivo" in resultado:
            return f"✅ Archivo {resultado['archivo']} creado/actualizado exitosamente"
        
        # Para comandos ejecutados
        elif "salida" in resultado:
            salida = resultado['salida']
            if isinstance(salida, str) and salida.strip():
                return f"📟 Salida del comando:\n{salida}"
            else:
                return "✅ Comando ejecutado exitosamente"
        
        # Para listado de archivos
        elif "archivos" in resultado:
            archivos = resultado['archivos']
            if archivos:
                output = f"📁 Encontrados {len(archivos)} archivos:\n"
                for archivo in archivos[:10]:  # Mostrar máximo 10
                    output += f"  - {archivo['nombre']} ({archivo['tamaño']} bytes)\n"
                if len(archivos) > 10:
                    output += f"  ... y {len(archivos) - 10} más"
                return output
            else:
                return "📁 No se encontraron archivos con ese patrón"
        
        # Para mensajes genéricos
        elif "mensaje" in resultado:
            return f"✅ {resultado['mensaje']}"
        
        # Para otros casos exitosos
        else:
            # Intentar crear un resumen del resultado
            if isinstance(resultado, dict):
                detalles = resultado.get("detalle", resultado)
                if isinstance(detalles, dict):
                    return f"✅ Operación completada:\n{json.dumps(detalles, indent=2, ensure_ascii=False)}"
                else:
                    return f"✅ {detalles}"
            else:
                return "✅ Operación completada exitosamente"
    else:
        # Para errores
        error_msg = resultado.get('error', resultado.get('detalle', 'Error desconocido'))
        return f"❌ Error: {error_msg}"

def extraer_parametro(texto, clave, default):
    """Extrae un parámetro del texto del comando"""
    if clave in texto:
        inicio = texto.find(clave) + len(clave)
        fin = texto.find("\n", inicio)
        if fin == -1:
            fin = len(texto)
        return texto[inicio:fin].strip()
    return default

def extraer_funciones(texto):
    """Extrae nombres de funciones del comando"""
    funciones = []
    lineas = texto.split("\n")
    for linea in lineas:
        if "función:" in linea or "function:" in linea:
            nombre = linea.split(":")[-1].strip()
            funciones.append({"nombre": nombre})
    return funciones if funciones else [{"nombre": "handler"}]



@app.route("/simbolo", methods=["POST"])
def procesar_accion():
    """Endpoint principal para procesar acciones de agentes"""
    try:
        data = request.get_json()
        log(f"Solicitud recibida: {data.get('agente', 'default')} - {data.get('accion', 'N/A')}")
        
        agente = data.get("agente", "default")
        accion = data.get("accion")
        parametros = data.get("parametros", {})
        
        # Validar agente
        if agente not in AGENTES and agente != "default":
            return jsonify({
                "estado": "error",
                "detalle": f"Agente '{agente}' no reconocido",
                "agentes_disponibles": list(AGENTES.keys())
            }), 400
        
        # Procesar según el agente
        resultado = None
        if agente == "dynamodb_creator":
            resultado = procesar_dynamodb(accion, parametros)
        elif agente == "function_registrar":
            resultado = procesar_funciones(accion, parametros)
        elif agente == "code_generator":
            resultado = procesar_generacion_codigo(accion, parametros)
        elif agente == "file_manager":
            resultado = procesar_archivos(accion, parametros)
        elif agente == "serverless_deployer":
            resultado = procesar_serverless(accion, parametros)
        else:
            resultado = procesar_accion_simbolica(data)
        
        log(f"Acción completada exitosamente", "SUCCESS")
        return jsonify({"estado": "ok", "detalle": resultado})
        
    except Exception as e:
        log(f"Error: {str(e)}", "ERROR")
        return jsonify({"estado": "error", "detalle": str(e)}), 500

@app.route("/agentes", methods=["GET"])
def listar_agentes():
    """Lista todos los agentes disponibles y sus capacidades"""
    return jsonify({
        "agentes": AGENTES,
        "total": len(AGENTES),
        "servidor": "Servidor Simbólico v2.0"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Verifica el estado del servidor"""
    return jsonify({
        "status": "healthy",
        "mensaje": "Servidor simbólico funcionando correctamente",
        "version": "2.0",
        "agentes_disponibles": list(AGENTES.keys()),
        "backend_path": str(BACKEND_DIR),
        "timestamp": datetime.now().isoformat()
    })

# ===================== AGENTE: DYNAMODB CREATOR =====================

def procesar_dynamodb(accion, parametros):
    """Procesa acciones relacionadas con DynamoDB"""
    if accion == "crear_tabla":
        return crear_tabla_dynamodb(parametros)
    elif accion == "agregar_indices":
        return agregar_indices_tabla(parametros)
    elif accion == "configurar_iam":
        return configurar_iam_dynamodb(parametros)
    else:
        raise ValueError(f"Acción '{accion}' no soportada por dynamodb_creator")

def crear_tabla_dynamodb(params):
    """Crea una nueva tabla DynamoDB en serverless.yml"""
    tabla_nombre = params.get("tabla")
    indices = params.get("indices", [])
    archivo = BACKEND_DIR / params.get("archivo", "serverless.yml")
    
    if not tabla_nombre:
        raise ValueError("Nombre de tabla requerido")
    
    # Leer serverless.yml
    with open(archivo, 'r') as f:
        serverless_config = yaml.safe_load(f)
    
    # Asegurar que existe la sección resources
    if 'resources' not in serverless_config:
        serverless_config['resources'] = {'Resources': {}}
    if 'Resources' not in serverless_config['resources']:
        serverless_config['resources']['Resources'] = {}
    
    # Definir la tabla
    tabla_definition = {
        'Type': 'AWS::DynamoDB::Table',
        'Properties': {
            'TableName': f"${{self:service}}-${{self:provider.stage}}-{tabla_nombre.lower()}",
            'AttributeDefinitions': [
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            'KeySchema': [
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    }
    
    # Agregar índices si se especificaron
    if indices:
        tabla_definition['Properties']['GlobalSecondaryIndexes'] = []
        for indice in indices:
            tabla_definition['Properties']['AttributeDefinitions'].append({
                'AttributeName': indice,
                'AttributeType': 'S'
            })
            tabla_definition['Properties']['GlobalSecondaryIndexes'].append({
                'IndexName': f"{indice}Index",
                'KeySchema': [{'AttributeName': indice, 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            })
    
    # Agregar la tabla a resources
    serverless_config['resources']['Resources'][tabla_nombre] = tabla_definition
    
    # Agregar variable de entorno
    if 'environment' not in serverless_config['provider']:
        serverless_config['provider']['environment'] = {}
    
    env_var_name = f"DYNAMODB_TABLE_{tabla_nombre.upper()}"
    serverless_config['provider']['environment'][env_var_name] = \
        f"${{self:service}}-${{self:provider.stage}}-{tabla_nombre.lower()}"
    
    # Guardar cambios
    with open(archivo, 'w') as f:
        yaml.dump(serverless_config, f, default_flow_style=False, sort_keys=False)
    
    return {
        "mensaje": f"Tabla {tabla_nombre} creada exitosamente",
        "archivo_modificado": str(archivo),
        "variable_entorno": env_var_name,
        "indices_creados": indices
    }

def agregar_indices_tabla(params):
    """Agrega índices secundarios a una tabla existente"""
    # Implementación similar a crear_tabla pero modificando tabla existente
    pass

def configurar_iam_dynamodb(params):
    """Configura permisos IAM para las tablas DynamoDB"""
    archivo = BACKEND_DIR / params.get("archivo", "serverless.yml")
    
    with open(archivo, 'r') as f:
        serverless_config = yaml.safe_load(f)
    
    # Asegurar estructura IAM
    if 'iam' not in serverless_config['provider']:
        serverless_config['provider']['iam'] = {'role': {'statements': []}}
    
    # Agregar permisos DynamoDB
    dynamodb_permissions = {
        'Effect': 'Allow',
        'Action': [
            'dynamodb:Query',
            'dynamodb:Scan',
            'dynamodb:GetItem',
            'dynamodb:PutItem',
            'dynamodb:UpdateItem',
            'dynamodb:DeleteItem'
        ],
        'Resource': [
            "arn:aws:dynamodb:${self:provider.region}:*:table/${self:service}-${self:provider.stage}-*",
            "arn:aws:dynamodb:${self:provider.region}:*:table/${self:service}-${self:provider.stage}-*/index/*"
        ]
    }
    
    serverless_config['provider']['iam']['role']['statements'].append(dynamodb_permissions)
    
    with open(archivo, 'w') as f:
        yaml.dump(serverless_config, f, default_flow_style=False, sort_keys=False)
    
    return {
        "mensaje": "Permisos IAM configurados para DynamoDB",
        "permisos_agregados": dynamodb_permissions['Action']
    }

# ===================== AGENTE: FUNCTION REGISTRAR =====================

def procesar_funciones(accion, parametros):
    """Procesa acciones relacionadas con funciones Lambda"""
    if accion == "registrar_funcion":
        return registrar_funcion_lambda(parametros)
    elif accion == "registrar_multiples":
        return registrar_multiples_funciones(parametros)
    elif accion == "eliminar_funcion":
        return eliminar_funcion_lambda(parametros)
    else:
        raise ValueError(f"Acción '{accion}' no soportada por function_registrar")

def registrar_funcion_lambda(params):
    """Registra una función Lambda en serverless.yml"""
    funcion = params.get("funcion")
    handler = params.get("handler")
    metodo = params.get("metodo", "get")
    path = params.get("path")
    autorizacion = params.get("autorizacion", False)
    archivo = BACKEND_DIR / params.get("archivo", "serverless.yml")
    
    if not all([funcion, handler, path]):
        raise ValueError("Faltan parámetros requeridos: funcion, handler, path")
    
    with open(archivo, 'r') as f:
        serverless_config = yaml.safe_load(f)
    
    if 'functions' not in serverless_config:
        serverless_config['functions'] = {}
    
    # Configurar la función
    funcion_config = {
        'handler': handler,
        'events': [{
            'http': {
                'path': path,
                'method': metodo,
                'cors': True
            }
        }]
    }
    
    # Agregar autorización si es necesaria
    if autorizacion:
        funcion_config['events'][0]['http']['authorizer'] = {
            'name': 'authorizerFunc',
            'resultTtlInSeconds': 0
        }
    
    serverless_config['functions'][funcion] = funcion_config
    
    with open(archivo, 'w') as f:
        yaml.dump(serverless_config, f, default_flow_style=False, sort_keys=False)
    
    return {
        "mensaje": f"Función {funcion} registrada exitosamente",
        "handler": handler,
        "endpoint": f"{metodo.upper()} /{path}",
        "autorizacion": autorizacion
    }

def registrar_multiples_funciones(params):
    """Registra múltiples funciones de una vez"""
    funciones = params.get("funciones", [])
    resultados = []
    
    for funcion_data in funciones:
        try:
            resultado = registrar_funcion_lambda(funcion_data)
            resultados.append({"funcion": funcion_data['funcion'], "estado": "ok", "detalle": resultado})
        except Exception as e:
            resultados.append({"funcion": funcion_data.get('funcion', 'unknown'), "estado": "error", "detalle": str(e)})
    
    return {
        "mensaje": f"Procesadas {len(funciones)} funciones",
        "resultados": resultados
    }

def eliminar_funcion_lambda(params):
    """Elimina una función Lambda de serverless.yml"""
    funcion = params.get("funcion")
    archivo = BACKEND_DIR / params.get("archivo", "serverless.yml")
    
    if not funcion:
        raise ValueError("Nombre de función requerido")
    
    with open(archivo, 'r') as f:
        serverless_config = yaml.safe_load(f)
    
    if 'functions' in serverless_config and funcion in serverless_config['functions']:
        del serverless_config['functions'][funcion]
        
        with open(archivo, 'w') as f:
            yaml.dump(serverless_config, f, default_flow_style=False, sort_keys=False)
        
        return {
            "mensaje": f"Función {funcion} eliminada exitosamente",
            "archivo": str(archivo)
        }
    else:
        return {
            "mensaje": f"Función {funcion} no encontrada",
            "estado": "warning"
        }

# ===================== AGENTE: CODE GENERATOR =====================

def procesar_generacion_codigo(accion, parametros):
    """Procesa acciones de generación de código"""
    if accion == "crear_handler":
        return crear_handler(parametros)
    elif accion == "crear_util":
        return crear_utilidad(parametros)
    elif accion == "fix_sintaxis":
        return corregir_sintaxis(parametros)
    elif accion == "generar_test":
        return generar_test(parametros)
    else:
        raise ValueError(f"Acción '{accion}' no soportada por code_generator")

def crear_handler(params):
    """Genera un handler Lambda con estructura estándar"""
    nombre_archivo = params.get("archivo")
    funciones = params.get("funciones", [])
    tipo = params.get("tipo", "rest")  # rest o graphql
    
    if not nombre_archivo:
        raise ValueError("Nombre de archivo requerido")
    
    archivo_path = BACKEND_DIR / nombre_archivo
    archivo_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Template base para handlers
    if tipo == "rest":
        template = """const AWS = require('aws-sdk');
const { createResponse, createError } = require('../utils/response');
const { validate{Funcion} } = require('../utils/validators');

const dynamodb = new AWS.DynamoDB.DocumentClient();

"""
        
        for funcion in funciones:
            funcion_name = funcion.get('nombre', funcion)
            template += f"""
exports.{funcion_name} = async (event) => {{
  try {{
    // TODO: Implementar lógica de {funcion_name}
    const body = JSON.parse(event.body || '{{}}');
    
    // Validación
    const {{ error }} = validate{funcion_name.capitalize()}(body);
    if (error) {{
      return createError(400, error.details[0].message);
    }}
    
    // Lógica de negocio aquí
    
    return createResponse(200, {{
      message: '{funcion_name} ejecutado exitosamente',
      data: {{}}
    }});
  }} catch (error) {{
    console.error('Error en {funcion_name}:', error);
    return createError(500, 'Error interno del servidor');
  }}
}};
"""
    
    with open(archivo_path, 'w') as f:
        f.write(template)
    
    return {
        "mensaje": f"Handler creado: {nombre_archivo}",
        "funciones_generadas": funciones,
        "ruta": str(archivo_path)
    }

def crear_utilidad(params):
    """Crea archivos de utilidades"""
    nombre = params.get("nombre")
    tipo = params.get("tipo", "general")  # general, validators, response
    
    archivo_path = BACKEND_DIR / "src" / "utils" / f"{nombre}.js"
    archivo_path.parent.mkdir(parents=True, exist_ok=True)
    
    templates = {
        "response": """// Utilidades para respuestas HTTP

exports.createResponse = (statusCode, body) => ({
  statusCode,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': process.env.CORS_ORIGIN || '*',
    'Access-Control-Allow-Credentials': true,
  },
  body: JSON.stringify(body)
});

exports.createError = (statusCode, message, details = null) => {
  const errorBody = {
    error: true,
    message,
    timestamp: new Date().toISOString()
  };
  
  if (details) {
    errorBody.details = details;
  }
  
  return exports.createResponse(statusCode, errorBody);
};
""",
        "validators": """const Joi = require('joi');

// Esquemas de validación
const schemas = {
  // TODO: Agregar esquemas específicos
};

// Función genérica de validación
exports.validate = (data, schemaName) => {
  const schema = schemas[schemaName];
  if (!schema) {
    throw new Error(`Schema '${schemaName}' no encontrado`);
  }
  return schema.validate(data, { abortEarly: false });
};
"""
    }
    
    template = templates.get(tipo, "// Utilidad personalizada\n")
    
    with open(archivo_path, 'w') as f:
        f.write(template)
    
    return {
        "mensaje": f"Utilidad creada: {nombre}.js",
        "tipo": tipo,
        "ruta": str(archivo_path)
    }

def corregir_sintaxis(params):
    """Intenta corregir errores de sintaxis comunes"""
    archivo = params.get("archivo")
    if not archivo:
        raise ValueError("Archivo requerido")
    
    archivo_path = BACKEND_DIR / archivo
    
    with open(archivo_path, 'r') as f:
        contenido = f.read()
    
    # Correcciones comunes
    correcciones = {
        r'}\s*;': '}',  # Quitar punto y coma después de llaves
        r'{\s*,': '{',  # Quitar comas después de llaves
        r',\s*}': '}',  # Quitar comas antes de llaves de cierre
        r'const\s+{\s*password:\s*_,\s*\.\.\.(\w+)\s*}\s*=': r'const { password, ...$1 } =',  # Fix destructuring
    }
    
    for patron, reemplazo in correcciones.items():
        contenido = re.sub(patron, reemplazo, contenido)
    
    # Backup del archivo original
    backup_path = str(archivo_path) + '.backup'
    with open(backup_path, 'w') as f:
        f.write(open(archivo_path, 'r').read())
    
    # Guardar archivo corregido
    with open(archivo_path, 'w') as f:
        f.write(contenido)
    
    return {
        "mensaje": f"Sintaxis corregida en {archivo}",
        "backup": backup_path,
        "correcciones_aplicadas": len(correcciones)
    }

def generar_test(params):
    """Genera archivos de test para handlers"""
    handler = params.get("handler")
    funciones = params.get("funciones", [])
    tipo = params.get("tipo", "jest")  # jest o mocha
    
    if not handler:
        raise ValueError("Handler requerido")
    
    # Extraer nombre del archivo de test
    handler_path = handler.replace('.', '/')
    test_file = f"tests/{handler_path}.test.js"
    test_path = BACKEND_DIR / test_file
    test_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Template para Jest
    template = f"""const {{ {', '.join(funciones)} }} = require('../{handler_path}');

describe('{handler} tests', () => {{
"""
    
    for funcion in funciones:
        template += f"""
  describe('{funcion}', () => {{
    it('should return 200 on success', async () => {{
      const event = {{
        body: JSON.stringify({{
          // TODO: Add test data
        }})
      }};
      
      const result = await {funcion}(event);
      
      expect(result.statusCode).toBe(200);
      expect(JSON.parse(result.body)).toHaveProperty('message');
    }});
    
    it('should return 400 on invalid input', async () => {{
      const event = {{
        body: JSON.stringify({{}})
      }};
      
      const result = await {funcion}(event);
      
      expect(result.statusCode).toBe(400);
    }});
  }});
"""
    
    template += "});\n"
    
    with open(test_path, 'w') as f:
        f.write(template)
    
    return {
        "mensaje": f"Tests generados para {handler}",
        "archivo": str(test_path),
        "funciones_testeadas": funciones
    }

# ===================== AGENTE: FILE MANAGER =====================

def procesar_archivos(accion, parametros):
    """Procesa acciones relacionadas con archivos"""
    if accion == "leer_archivo":
        return leer_archivo(parametros)
    elif accion == "escribir_archivo":
        return escribir_archivo(parametros)
    elif accion == "crear_directorio":
        return crear_directorio(parametros)
    elif accion == "listar_archivos":
        return listar_archivos(parametros)
    else:
        raise ValueError(f"Acción '{accion}' no soportada por file_manager")

def leer_archivo(params):
    """Lee el contenido de un archivo"""
    archivo = params.get("archivo")
    if not archivo:
        raise ValueError("Archivo requerido")
    
    archivo_path = BASE_DIR / archivo
    
    with open(archivo_path, 'r') as f:
        contenido = f.read()
    
    return {
        "archivo": archivo,
        "contenido": contenido,
        "lineas": len(contenido.splitlines()),
        "tamaño": os.path.getsize(archivo_path)
    }

def escribir_archivo(params):
    """Escribe contenido a un archivo"""
    archivo = params.get("archivo")
    contenido = params.get("contenido")
    crear_backup = params.get("backup", True)
    
    if not archivo or contenido is None:
        raise ValueError("Archivo y contenido requeridos")
    
    archivo_path = BASE_DIR / archivo
    
    # Crear backup si existe
    if crear_backup and archivo_path.exists():
        backup_path = str(archivo_path) + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(backup_path, 'w') as f:
            f.write(open(archivo_path, 'r').read())
    
    # Escribir nuevo contenido
    archivo_path.parent.mkdir(parents=True, exist_ok=True)
    with open(archivo_path, 'w') as f:
        f.write(contenido)
    
    return {
        "mensaje": f"Archivo escrito: {archivo}",
        "tamaño": len(contenido),
        "backup": backup_path if crear_backup and 'backup_path' in locals() else None
    }

def crear_directorio(params):
    """Crea un directorio en el proyecto"""
    directorio = params.get("directorio")
    
    if not directorio:
        raise ValueError("Directorio requerido")
    
    dir_path = BASE_DIR / directorio
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Crear .gitkeep si está vacío
        gitkeep = dir_path / '.gitkeep'
        gitkeep.touch()
        
        return {
            "mensaje": f"Directorio creado: {directorio}",
            "ruta_absoluta": str(dir_path),
            "gitkeep_creado": True
        }
    except Exception as e:
        return {
            "mensaje": f"Error creando directorio: {str(e)}",
            "estado": "error"
        }

def listar_archivos(params):
    """Lista archivos en un directorio"""
    directorio = params.get("directorio", ".")
    patron = params.get("patron", "*")
    recursivo = params.get("recursivo", False)
    
    dir_path = BASE_DIR / directorio
    
    # AGREGAR ESTE LOG
    log(f"Intentando listar archivos en: {dir_path.absolute()}", "DEBUG")
    
    if not dir_path.exists():
        raise ValueError(f"Directorio no existe: {directorio}")
    
    archivos = []
    
    if recursivo:
        for archivo in dir_path.rglob(patron):
            if archivo.is_file():
                archivos.append({
                    "nombre": archivo.name,
                    "ruta": str(archivo.relative_to(BASE_DIR)),
                    "tamaño": archivo.stat().st_size,
                    "modificado": datetime.fromtimestamp(archivo.stat().st_mtime).isoformat()
                })
    else:
        for archivo in dir_path.glob(patron):
            if archivo.is_file():
                archivos.append({
                    "nombre": archivo.name,
                    "ruta": str(archivo.relative_to(BASE_DIR)),
                    "tamaño": archivo.stat().st_size,
                    "modificado": datetime.fromtimestamp(archivo.stat().st_mtime).isoformat()
                })
    
    return {
        "directorio": directorio,
        "patron": patron,
        "total_archivos": len(archivos),
        "archivos": archivos
    }


# ===================== AGENTE: SERVERLESS DEPLOYER =====================

def procesar_serverless(accion, parametros):
    """Procesa acciones de Serverless Framework"""
    if accion == "deploy":
        return deploy_serverless(parametros)
    elif accion == "remove":
        return remove_serverless(parametros)
    elif accion == "logs":
        return obtener_logs(parametros)
    elif accion == "info":
        return obtener_info(parametros)
    else:
        raise ValueError(f"Acción '{accion}' no soportada por serverless_deployer")

def deploy_serverless(params):
    """Ejecuta serverless deploy"""
    stage = params.get("stage", "dev")
    region = params.get("region", "us-east-1")
    
    comando = f"cd {BACKEND_DIR} && npx serverless deploy --stage {stage} --region {region}"
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        return {
            "mensaje": "Deploy completado",
            "stage": stage,
            "region": region,
            "output": resultado.stdout,
            "exitcode": resultado.returncode
        }
    except Exception as e:
        return {
            "mensaje": "Error en deploy",
            "error": str(e)
        }
    
def remove_serverless(params):
    """Ejecuta serverless remove para eliminar el stack"""
    stage = params.get("stage", "dev")
    region = params.get("region", "us-east-1")
    
    comando = f"cd {BACKEND_DIR} && npx serverless remove --stage {stage} --region {region}"
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        return {
            "mensaje": "Stack removido" if resultado.returncode == 0 else "Error removiendo stack",
            "stage": stage,
            "region": region,
            "output": resultado.stdout,
            "error": resultado.stderr if resultado.returncode != 0 else None,
            "exitcode": resultado.returncode
        }
    except Exception as e:
        return {
            "mensaje": "Error ejecutando remove",
            "error": str(e)
        }

def obtener_logs(params):
    """Obtiene logs de una función Lambda"""
    funcion = params.get("funcion")
    stage = params.get("stage", "dev")
    tail = params.get("tail", False)
    start_time = params.get("start_time", "10m")  # últimos 10 minutos por defecto
    
    if not funcion:
        raise ValueError("Función requerida")
    
    comando = f"cd {BACKEND_DIR} && npx serverless logs -f {funcion} --stage {stage}"
    
    if tail:
        comando += " --tail"
    else:
        comando += f" --startTime {start_time}"
    
    try:
        if tail:
            # Para tail, necesitamos un proceso diferente
            proceso = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Leer algunas líneas
            logs = []
            for i in range(50):  # Leer máximo 50 líneas
                line = proceso.stdout.readline() # type: ignore
                if line:
                    logs.append(line.strip())
                else:
                    break
            
            proceso.terminate()
            
            return {
                "mensaje": "Logs obtenidos (tail mode)",
                "funcion": funcion,
                "stage": stage,
                "logs": logs
            }
        else:
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
            
            return {
                "mensaje": "Logs obtenidos",
                "funcion": funcion,
                "stage": stage,
                "start_time": start_time,
                "logs": resultado.stdout.splitlines(),
                "exitcode": resultado.returncode
            }
    except Exception as e:
        return {
            "mensaje": "Error obteniendo logs",
            "error": str(e)
        }
    

def obtener_info(params):
    """Obtiene información del stack desplegado"""
    stage = params.get("stage", "dev")
    
    comando = f"cd {BACKEND_DIR} && npx serverless info --stage {stage}"
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        # Parsear output para extraer endpoints
        endpoints = []
        for line in resultado.stdout.splitlines():
            if "endpoint:" in line or "GET -" in line or "POST -" in line:
                endpoints.append(line.strip())
        
        return {
            "mensaje": "Información obtenida",
            "stage": stage,
            "endpoints": endpoints,
            "output": resultado.stdout
        }
    except Exception as e:
        return {
            "mensaje": "Error obteniendo info",
            "error": str(e)
        }

# ===================== INICIALIZACIÓN =====================

if __name__ == "__main__":
    log("Iniciando Servidor Simbólico v2.0", "INFO")
    log(f"Directorio base: {BASE_DIR}", "INFO")
    log(f"Directorio backend: {BACKEND_DIR}", "INFO")
    log(f"Agentes disponibles: {list(AGENTES.keys())}", "INFO")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)