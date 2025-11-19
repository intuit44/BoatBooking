"""
Endpoint: /api/leer-archivo
Lectura inteligente de archivos con soporte para Blob Storage y sugerencias.
"""
import base64
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import azure.functions as func

import function_app as fa
from file_summarizer import generar_resumen_archivo
from utils_helpers import get_run_id

app = fa.app

FILE_CACHE: Dict[str, Dict[str, Any]] = {}


@app.function_name(name="leer_archivo_http")
@app.route(route="leer-archivo", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def leer_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint mejorado para lectura de archivos con búsqueda inteligente
    y respuestas optimizadas para agentes AI
    """

    memoria_previa = getattr(req, '_memoria_contexto', {})
    if memoria_previa and memoria_previa.get("tiene_historial"):
        logging.info(
            f"🔁 Leer-archivo: {memoria_previa['total_interacciones']} interacciones encontradas")
        logging.info(
            f"🧠 Historial: {memoria_previa.get('resumen_conversacion', '')[:100]}...")

    endpoint = "/api/leer-archivo"
    method = "GET"
    run_id = get_run_id(req)

    try:
        params = extract_parameters(req)

        if not params["ruta_raw"]:
            res_dict = {
                "ok": False,
                "error_code": "MISSING_PARAMETER",
                "message": "Se requiere el parámetro 'ruta' para leer un archivo",
                "suggestions": generate_parameter_suggestions(),
                "metadata": {
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": "/api/leer-archivo"
                }
            }
            return func.HttpResponse(
                json.dumps(res_dict, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        request_type = detect_request_type(params["ruta_raw"])

        if request_type == "api_function":
            res_dict = handle_api_function_request_dict(
                params["ruta_raw"], run_id)
        elif request_type == "special_path":
            res_dict = handle_special_path_request_dict(
                params["ruta_raw"], run_id)
        else:
            res_dict = handle_file_request_dict(params, run_id)

        return func.HttpResponse(
            json.dumps(res_dict, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception(f"[{run_id}] Error en leer_archivo_http")
        res_dict = {
            "ok": False,
            "error_code": "INTERNAL_ERROR",
            "message": f"Error procesando solicitud: {str(e)}",
            "suggestions": ["Verificar formato de la solicitud", "Revisar logs del servidor"],
            "metadata": {
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "endpoint": "/api/leer-archivo"
            }
        }
        return func.HttpResponse(
            json.dumps(res_dict, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )


def extract_parameters(req: func.HttpRequest) -> Dict[str, Any]:
    """Extrae y normaliza parámetros de la request"""
    from function_app import CONTAINER_NAME  # Import diferido para evitar ciclos

    ruta_raw = (req.params.get("ruta") or
                req.params.get("path") or
                req.params.get("archivo") or
                req.params.get("blob") or "").strip()

    container = (req.params.get("container") or
                 req.params.get("contenedor") or
                 CONTAINER_NAME).strip()

    params = {
        "ruta_raw": ruta_raw,
        "container": container,
        "force_refresh": req.params.get("force_refresh", "false").lower() == "true",
        "include_preview": req.params.get("include_preview", "true").lower() == "true",
        "semantic_analysis": req.params.get("semantic_analysis", "false").lower() == "true"
    }

    # Normalizar: asegurar prefijo "threads/" si se proporcionó una ruta y no lo tiene
    if params["ruta_raw"] and not params["ruta_raw"].startswith("threads/"):
        params["ruta_raw"] = "threads/" + params["ruta_raw"]

    return params


def detect_request_type(path: str) -> str:
    """Detecta si la solicitud es para una función API, ruta especial o archivo normal"""

    if path.startswith("api/") or path.startswith("/api/"):
        return "api_function"

    special_patterns = [
        "function_app.py",
        "__init__.py",
        "host.json",
        "requirements.txt",
        "local.settings.json"
    ]

    if any(pattern in path.lower() for pattern in special_patterns):
        return "special_path"

    return "file"


def handle_api_function_request_dict(path: str, run_id: str) -> dict:
    """Versión que devuelve diccionario para integración de memoria con soporte para Blob Storage"""

    blob_result = None
    if fa.IS_AZURE:
        blob_result = fa.leer_archivo_blob("function_app.py")
        if blob_result["exito"]:
            contenido = blob_result["contenido"]
            resumen = f"He leído el archivo function_app.py ({len(contenido)} caracteres). Contiene {contenido.count('def ')} funciones Python y {contenido.count('@app.route')} endpoints HTTP."
            return {
                "exito": True,
                "contenido": contenido,
                "tipo": "python",
                "ruta": blob_result["ruta"],
                "fuente": blob_result["fuente"],
                "mensaje": f"Código de función API desde Blob: {path}",
                "texto_semantico": resumen,
                "run_id": run_id,
                "metadata": blob_result.get("metadata", {})
            }

    try:
        with open("function_app.py", "r", encoding="utf-8") as f:
            contenido = f.read()
        resumen = f"He leído el archivo function_app.py ({len(contenido)} caracteres). Contiene {contenido.count('def ')} funciones Python y {contenido.count('@app.route')} endpoints HTTP."
        return {
            "exito": True,
            "contenido": contenido,
            "tipo": "python",
            "ruta": "function_app.py",
            "fuente": "Sistema Local",
            "mensaje": f"Código de función API: {path}",
            "texto_semantico": resumen,
            "run_id": run_id
        }
    except Exception as e:
        error_msg = f"No se pudo leer función API: {path}"
        if fa.IS_AZURE and blob_result:
            blob_error = blob_result.get("error", "Error en Blob")
            error_msg += f" (Blob: {blob_error}, Local: {str(e)})"

        return {
            "exito": False,
            "error": error_msg,
            "mensaje": error_msg,
            "run_id": run_id
        }


def handle_special_path_request_dict(path: str, run_id: str) -> dict:
    """Versión que devuelve diccionario para integración de memoria con soporte para Blob Storage"""

    blob_result = None
    if fa.IS_AZURE:
        blob_result = fa.leer_archivo_blob(path)
        if blob_result["exito"]:
            return {
                "exito": True,
                "contenido": blob_result["contenido"],
                "tipo": "text",
                "ruta": blob_result["ruta"],
                "fuente": blob_result["fuente"],
                "mensaje": f"Archivo especial leído desde Blob: {path}",
                "run_id": run_id,
                "metadata": blob_result.get("metadata", {})
            }

    try:
        with open(path, "r", encoding="utf-8") as f:
            contenido = f.read()
        return {
            "exito": True,
            "contenido": contenido,
            "tipo": "text",
            "ruta": path,
            "fuente": "Sistema Local",
            "mensaje": f"Archivo especial leído: {path}",
            "run_id": run_id
        }
    except Exception as e:
        error_msg = f"No se pudo leer archivo especial: {path}"
        if fa.IS_AZURE and blob_result:
            blob_error = blob_result.get("error", "Error en Blob")
            error_msg += f" (Blob: {blob_error}, Local: {str(e)})"

        return {
            "exito": False,
            "error": error_msg,
            "mensaje": error_msg,
            "run_id": run_id
        }


def handle_file_request_dict(params: dict, run_id: str) -> dict:
    """Versión que devuelve diccionario para integración de memoria con soporte para Blob Storage"""
    ruta = params["ruta_raw"]

    blob_result = None
    if fa.IS_AZURE:
        blob_result = fa.leer_archivo_blob(ruta)
        if blob_result["exito"]:
            contenido = blob_result["contenido"]
            resumen = generar_resumen_archivo(ruta, contenido)
            return {
                "exito": True,
                "contenido": contenido,
                "tipo": "markdown" if ruta.endswith(".md") else "text",
                "ruta": blob_result["ruta"],
                "tamaño": blob_result["tamaño"],
                "fuente": blob_result["fuente"],
                "mensaje": f"Archivo leído desde Blob Storage: {ruta}",
                "texto_semantico": resumen,
                "run_id": run_id,
                "metadata": blob_result.get("metadata", {})
            }
        else:
            logging.info(
                f"Blob Storage falló para {ruta}, intentando local...")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()

        tipo = "markdown" if ruta.endswith(".md") else "text"
        resumen = generar_resumen_archivo(ruta, contenido)

        return {
            "exito": True,
            "contenido": contenido,
            "tipo": tipo,
            "ruta": ruta,
            "tamaño": len(contenido),
            "fuente": "Sistema Local",
            "mensaje": f"Archivo leído exitosamente: {ruta}",
            "texto_semantico": resumen,
            "run_id": run_id
        }
    except Exception as e:
        error_msg = f"No se pudo leer archivo: {ruta}"
        if fa.IS_AZURE and blob_result:
            blob_error = blob_result.get("error", "Error desconocido en Blob")
            error_msg += f" (Blob: {blob_error}, Local: {str(e)})"
        else:
            error_msg += f" (Local: {str(e)})"

        return {
            "exito": False,
            "error": error_msg,
            "mensaje": error_msg,
            "run_id": run_id,
            "intentos": ["blob_storage" if fa.IS_AZURE else None, "local_filesystem"],
            "sugerencias": [
                "Verificar que el archivo existe en Azure Blob Storage",
                "Confirmar la ruta del archivo",
                "Usar /api/listar-blobs para ver archivos disponibles"
            ]
        }


def handle_file_request(params: Dict[str, Any], run_id: str) -> func.HttpResponse:
    """Maneja solicitudes de archivos normales con búsqueda inteligente"""

    ruta_raw = params["ruta_raw"]
    container = params["container"]

    cache_key = f"{container}:{ruta_raw}"
    if not params["force_refresh"] and cache_key in FILE_CACHE:
        cached = FILE_CACHE[cache_key]
        if (datetime.now() - cached["timestamp"]).seconds < 300:
            return cached["response"]

    result = smart_file_search(ruta_raw, container, run_id)

    if result["found"]:
        response = success_response(
            message=f"Archivo encontrado: {result['path']}",
            data={
                "path": result["path"],
                "content": result["content"],
                "source": result["source"],
                "size": len(result["content"]),
                "type": detect_file_type(result["path"])
            },
            run_id=run_id
        )

        FILE_CACHE[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }

        return response

    suggestions = generate_file_suggestions(
        ruta_raw, container, result["attempts"])

    return error_response(
        code="FILE_NOT_FOUND",
        message=f"No se encontró el archivo '{ruta_raw}'",
        suggestions=suggestions["actions"],
        status=404,
        run_id=run_id,
        details={
            "requested_path": ruta_raw,
            "container": container,
            "attempts": result["attempts"],
            "similar_files": suggestions["similar_files"][:10],
            "search_strategy": result.get("strategy", "standard")
        }
    )


def smart_file_search(path: str, container: str, run_id: str) -> Dict[str, Any]:
    """
    Búsqueda inteligente de archivos en múltiples ubicaciones
    """
    attempts = []
    normalized_path = normalize_path(path)
    file_name = Path(path).name

    if fa.IS_AZURE:
        blob_result = search_in_blob_storage(
            container, normalized_path, attempts, run_id)
        if blob_result["found"]:
            return blob_result

    local_search_paths = generate_local_search_paths(
        path, normalized_path, file_name)

    for search_path in local_search_paths:
        attempts.append(f"local:{search_path}")
        if search_path.exists() and search_path.is_file():
            try:
                content = search_path.read_text(
                    encoding="utf-8", errors="replace")
                return {
                    "found": True,
                    "path": str(search_path),
                    "content": content,
                    "source": "local",
                    "attempts": attempts,
                    "strategy": "local_filesystem"
                }
            except Exception as e:
                logging.warning(f"[{run_id}] Error leyendo {search_path}: {e}")

    fuzzy_result = fuzzy_file_search(file_name, path, attempts, run_id)
    if fuzzy_result["found"]:
        return fuzzy_result

    return {
        "found": False,
        "attempts": attempts,
        "strategy": "exhaustive_search"
    }


def generate_local_search_paths(path: str, normalized: str, filename: str) -> List[Path]:
    """Genera una lista priorizada de rutas locales donde buscar"""

    from function_app import PROJECT_ROOT  # Import diferido

    paths: List[Path] = []

    paths.append(PROJECT_ROOT / path)
    paths.append(PROJECT_ROOT / normalized)

    common_dirs = ["scripts", "src", "app", "functions",
                   "api", "docs", "test", "copiloto-function"]
    for dir_name in common_dirs:
        paths.append(PROJECT_ROOT / dir_name / filename)
        paths.append(PROJECT_ROOT / dir_name / normalized)
        if "/" in path:
            paths.append(PROJECT_ROOT / dir_name / path)

    paths.append(PROJECT_ROOT / "copiloto-function" / "scripts" / filename)
    paths.append(PROJECT_ROOT / "boat-rental-app" / path)

    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    return unique_paths


def search_in_blob_storage(container: str, path: str, attempts: List[str], run_id: str) -> Dict[str, Any]:
    """Busca archivo en Azure Blob Storage con múltiples estrategias robustas"""

    try:
        client = fa.get_blob_client()
        if not client:
            attempts.append("blob:no_client")
            return {"found": False}

        cc = client.get_container_client(container)
        if not cc.exists():
            attempts.append(f"blob:container_not_found:{container}")
            return {"found": False}

        clean_path = path
        if path.startswith(f"{container}/"):
            clean_path = path[len(container)+1:]
        elif path.startswith("boat-rental-project/"):
            clean_path = path[len("boat-rental-project")+1:]

        paths_to_try = [
            clean_path,
            clean_path.lstrip('/'),
            path,
            path.lstrip('/'),
        ]

        paths_to_try = list(dict.fromkeys(paths_to_try))

        for try_path in paths_to_try:
            try:
                bc = cc.get_blob_client(try_path)
                attempts.append(f"blob:{container}/{try_path}")

                if bc.exists():
                    content = bc.download_blob().readall()
                    try:
                        text_content = content.decode("utf-8")
                        return {
                            "found": True,
                            "path": f"blob://{container}/{try_path}",
                            "content": text_content,
                            "source": "blob",
                            "attempts": attempts,
                            "strategy": "blob_direct"
                        }
                    except UnicodeDecodeError:
                        return {
                            "found": True,
                            "path": f"blob://{container}/{try_path}",
                            "content": base64.b64encode(content).decode("utf-8"),
                            "source": "blob_binary",
                            "attempts": attempts,
                            "strategy": "blob_binary"
                        }
            except Exception as e:
                logging.debug(f"[{run_id}] Ruta {try_path} no encontrada: {e}")
                continue

    except Exception as e:
        logging.warning(f"[{run_id}] Error en blob storage: {e}")
        attempts.append(f"blob:error:{str(e)[:50]}")

    return {"found": False}


def fuzzy_file_search(filename: str, original_path: str, attempts: List[str], run_id: str) -> Dict[str, Any]:
    """Búsqueda fuzzy para encontrar archivos similares"""

    from function_app import PROJECT_ROOT  # Import diferido

    try:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            for file in files:
                if filename.lower() in file.lower() or file.lower() in filename.lower():
                    file_path = Path(root) / file
                    attempts.append(f"fuzzy:{file_path}")

                    similarity = calculate_similarity(
                        filename.lower(), file.lower())
                    if similarity > 0.8:
                        try:
                            content = file_path.read_text(
                                encoding="utf-8", errors="replace")
                            return {
                                "found": True,
                                "path": str(file_path),
                                "content": content,
                                "source": "fuzzy_match",
                                "attempts": attempts,
                                "strategy": "fuzzy_search",
                                "similarity": similarity
                            }
                        except Exception:
                            pass
    except Exception as e:
        logging.warning(f"[{run_id}] Error en búsqueda fuzzy: {e}")

    return {"found": False}


def generate_file_suggestions(path: str, container: str, attempts: List[str]) -> Dict[str, Any]:
    """Genera sugerencias inteligentes cuando no se encuentra un archivo"""

    suggestions = {
        "actions": [],
        "similar_files": []
    }

    filename = Path(path).name
    extension = Path(path).suffix

    similar_files = find_similar_files(filename, extension)
    suggestions["similar_files"] = similar_files

    if similar_files:
        if len(similar_files) == 1:
            suggestions["actions"].append(
                f"Usar archivo: {similar_files[0]['path']}")
        else:
            suggestions["actions"].append(
                "Seleccionar uno de los archivos similares encontrados")
            for file in similar_files[:3]:
                suggestions["actions"].append(f"Probar con: {file['path']}")

    if "script" in path.lower() or extension in [".py", ".sh", ".ps1"]:
        suggestions["actions"].append(
            "Listar scripts disponibles con: ?path=scripts")
        suggestions["actions"].append("Verificar en la carpeta scripts/")

    if "test" in path.lower():
        suggestions["actions"].append("Buscar en carpeta test/ o tests/")

    suggestions["actions"].extend([
        f"Verificar el nombre exacto del archivo",
        f"Confirmar que el archivo existe en el container '{container}'",
        "Usar el parámetro 'container' si el archivo está en otro contenedor"
    ])

    return suggestions


def find_similar_files(filename: str, extension: str) -> List[Dict[str, str]]:
    """Encuentra archivos similares al solicitado"""

    from function_app import PROJECT_ROOT  # Import diferido

    similar = []
    filename_lower = filename.lower()

    try:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            depth = len(Path(root).relative_to(PROJECT_ROOT).parts)
            if depth > 3:
                continue

            for file in files:
                file_lower = file.lower()

                score = 0
                if file_lower == filename_lower:
                    score = 100
                elif filename_lower in file_lower or file_lower in filename_lower:
                    score = 80
                elif extension and file.endswith(extension):
                    score = 60
                elif any(part in file_lower for part in filename_lower.split('_')):
                    score = 40

                if score > 30:
                    rel_path = Path(root).relative_to(PROJECT_ROOT) / file
                    similar.append({
                        "path": str(rel_path).replace('\\', '/'),
                        "score": score,
                        "type": "local"
                    })

        similar.sort(key=lambda x: x["score"], reverse=True)

    except Exception as e:
        logging.warning(f"Error buscando archivos similares: {e}")

    return similar[:15]


def extract_function_code(content: str, function_name: str) -> Optional[str]:
    """Extrae el código de una función específica del contenido"""

    patterns = [
        f"@app.function_name.*?{function_name}.*?def.*?^(?=@app|def|class|$)",
        f"def {function_name}.*?^(?=def|class|$)",
        f"async def {function_name}.*?^(?=def|async def|class|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(0).strip()

    if function_name in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if function_name in line and ('def' in line or '@app' in line):
                function_lines = []
                indent_level = len(line) - len(line.lstrip())

                for j in range(i, min(i + 100, len(lines))):
                    current_line = lines[j]
                    if j > i and current_line.strip() and not current_line.startswith(' '):
                        break
                    function_lines.append(current_line)

                return '\n'.join(function_lines)

    return None


def find_available_api_functions() -> List[str]:
    """Encuentra todas las funciones API disponibles"""

    from function_app import PROJECT_ROOT  # Import diferido

    functions: List[str] = []

    try:
        function_app_path = PROJECT_ROOT / "function_app.py"
        if function_app_path.exists():
            content = function_app_path.read_text()
            routes = re.findall(r'@app\.route\(route="([^"]+)"', content)
            functions.extend([route.replace('-', '_') for route in routes])

            func_names = re.findall(
                r'@app\.function_name\(name="([^"]+)"', content)
            functions.extend(func_names)

    except Exception as e:
        logging.warning(f"Error buscando funciones API: {e}")

    return list(set(functions))


def generate_api_suggestions(requested: str, similar: List[str]) -> List[str]:
    """Genera sugerencias para funciones API"""

    suggestions = []

    if similar:
        suggestions.append(f"Funciones similares disponibles:")
        for func_name in similar[:5]:
            suggestions.append(f"  - /api/{func_name.replace('_', '-')}")

    suggestions.extend([
        "Verificar el nombre exacto de la función",
        "Usar /api/status para verificar funciones disponibles",
        "Revisar la documentación de la API"
    ])

    return suggestions


def calculate_similarity(str1: str, str2: str) -> float:
    """Calcula similitud entre dos strings (0-1)"""

    if str1 == str2:
        return 1.0

    longer = max(len(str1), len(str2))
    if longer == 0:
        return 0.0

    common = sum(1 for a, b in zip(str1, str2) if a == b)
    return common / longer


def detect_file_type(path: str) -> str:
    """Detecta el tipo de archivo basado en la extensión"""

    ext = Path(path).suffix.lower()

    type_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
        '.sh': 'shell',
        '.ps1': 'powershell',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css'
    }

    return type_map.get(ext, 'unknown')


def normalize_path(path: str) -> str:
    """Normaliza una ruta eliminando caracteres problemáticos"""

    path = path.strip('/')
    path = path.replace('//', '/')
    path = path.replace('..', '')

    return path


def success_response(message: str, data: Dict[str, Any], run_id: str) -> func.HttpResponse:
    """Genera una respuesta exitosa estructurada"""

    response = {
        "ok": True,
        "message": message,
        "data": data,
        "metadata": {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/api/leer-archivo"
        }
    }

    return func.HttpResponse(
        json.dumps(response, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200
    )


def error_response(code: str, message: str, suggestions: List[str], status: int,
                   run_id: str, details: Optional[Dict] = None) -> func.HttpResponse:
    """Genera una respuesta de error estructurada y útil para el agente"""

    response = {
        "ok": False,
        "error_code": code,
        "message": message,
        "suggestions": suggestions,
        "metadata": {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/api/leer-archivo"
        }
    }

    if details:
        response["details"] = details

    response["agent_guidance"] = generate_agent_guidance(code, suggestions)

    return func.HttpResponse(
        json.dumps(response, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=status
    )


def generate_agent_guidance(error_code: str, suggestions: List[str]) -> Dict[str, Any]:
    """Genera guía específica para el agente AI"""

    guidance = {
        "next_action": "ask_user",
        "prompt_suggestions": []
    }

    if error_code == "MISSING_PARAMETER":
        guidance["next_action"] = "request_parameter"
        guidance["prompt_suggestions"] = [
            "Por favor, proporciona la ruta del archivo que deseas leer",
            "¿Qué archivo necesitas consultar?"
        ]

    elif error_code == "FILE_NOT_FOUND":
        guidance["next_action"] = "clarify_path"
        guidance["prompt_suggestions"] = [
            "No encontré ese archivo. ¿Puedes verificar el nombre?",
            "Encontré archivos similares: " +
            ", ".join(
                suggestions[:3]) if suggestions else "No hay archivos similares"
        ]

    elif error_code == "API_FUNCTION_NOT_FOUND":
        guidance["next_action"] = "suggest_alternatives"
        guidance["prompt_suggestions"] = [
            "Esa función no existe. Las funciones disponibles son: " +
            ", ".join(suggestions[:5])
        ]

    return guidance


def generate_parameter_suggestions() -> List[str]:
    """Genera sugerencias cuando faltan parámetros"""

    return [
        "Incluir parámetro 'ruta' con el path del archivo",
        "Ejemplo: ?ruta=scripts/test.py",
        "Ejemplo: ?ruta=README.md",
        "Para archivos en otro contenedor: ?ruta=file.txt&container=mi-contenedor"
    ]
