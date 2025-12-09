from utils_helpers import get_run_id
from function_app import app
import azure.functions as func
import json
import ast
import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
import os
import sys

# Importar el app principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class ProjectExplorer:
    """Explorador inteligente de estructura de proyectos"""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.cache = {}

    def get_structure(self, max_depth: int = 3, filters: Optional[Dict] = None) -> Dict:
        """Obtener estructura del proyecto con filtros"""
        filters = filters or {}

        structure = {
            "root": str(self.root),
            "timestamp": datetime.now().isoformat(),
            "tree": self._build_tree(self.root, max_depth, filters),
            "summary": self._generate_summary()
        }

        return structure

    def _build_tree(self, path: Path, depth: int, filters: Dict, current_depth: int = 0) -> Dict:
        """Construir árbol de archivos"""
        if current_depth >= depth:
            return {"truncated": True}

        # Inicializar claves con tipos coherentes para evitar errores de tipado
        tree = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "path": str(path.relative_to(self.root)) if path != self.root else ".",
            "children": [],
            "count": 0
        }

        if path.is_file():
            tree.update(self._get_file_info(path))
            return tree

        ignore_dirs = {"node_modules", ".git", "__pycache__",
                       ".venv", "venv", "dist", "build", ".next", "coverage"}

        if path.name in ignore_dirs:
            return {"name": path.name, "type": "ignored"}

        children = []
        try:
            for item in sorted(path.iterdir()):
                if self._should_include(item, filters):
                    child = self._build_tree(
                        item, depth, filters, current_depth + 1)
                    if child:
                        children.append(child)
        except PermissionError:
            tree["error"] = "permission_denied"

        tree["children"] = children
        tree["count"] = len(children)

        return tree

    def _get_file_info(self, path: Path) -> Dict:
        """Información detallada del archivo"""
        stat = path.stat()

        info = {
            "size": stat.st_size,
            "extension": path.suffix,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        if path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx"]:
            info["language"] = self._detect_language(path.suffix)
            info["analyzable"] = True
        elif path.suffix in [".json", ".yaml", ".yml", ".toml"]:
            info["type"] = "config"
        elif path.suffix in [".md", ".txt"]:
            info["type"] = "documentation"

        return info

    def _should_include(self, path: Path, filters: Dict) -> bool:
        """Verificar si el archivo cumple los filtros"""
        if not filters:
            return True

        if "extensions" in filters:
            if path.is_file() and path.suffix not in filters["extensions"]:
                return False

        if "max_size" in filters:
            if path.is_file() and path.stat().st_size > filters["max_size"]:
                return False

        if "pattern" in filters:
            if not re.search(filters["pattern"], path.name, re.IGNORECASE):
                return False

        return True

    def _detect_language(self, ext: str) -> str:
        """Detectar lenguaje por extensión"""
        lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
                    ".tsx": "typescript-react", ".jsx": "javascript-react"}
        return lang_map.get(ext, "unknown")

    def _generate_summary(self) -> Dict:
        """Generar resumen del proyecto"""
        summary = {"total_files": 0, "total_dirs": 0,
                   "by_language": {}, "by_type": {}}

        for item in self.root.rglob("*"):
            if item.is_file():
                summary["total_files"] += 1
                if item.suffix in [".py", ".js", ".ts", ".tsx", ".jsx"]:
                    lang = self._detect_language(item.suffix)
                    summary["by_language"][lang] = summary["by_language"].get(
                        lang, 0) + 1
                if item.suffix in [".json", ".yaml", ".yml"]:
                    summary["by_type"]["config"] = summary["by_type"].get(
                        "config", 0) + 1
                elif item.suffix in [".md", ".txt"]:
                    summary["by_type"]["docs"] = summary["by_type"].get(
                        "docs", 0) + 1
            elif item.is_dir():
                summary["total_dirs"] += 1

        return summary


class SemanticAnalyzer:
    """Analizador semántico para código Python"""

    def __init__(self, content: str, file_path: str = ""):
        self.content = content
        self.file_path = file_path
        self.lines = content.split('\n')
        self.tree = None
        self.parse_errors = []

        try:
            self.tree = ast.parse(content)
        except SyntaxError as e:
            self.parse_errors.append({
                "type": "syntax_error",
                "line": e.lineno,
                "message": str(e),
                "text": e.text
            })

    def find_classes(self, pattern: Optional[str] = None) -> List[Dict]:
        """Detectar clases con patrón opcional"""
        classes = []
        if not self.tree:
            return classes

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    "bases": [self._get_name(base) for base in node.bases],
                    "decorators": [self._get_name(dec) for dec in node.decorator_list]
                }

                if pattern is None or re.search(pattern, node.name, re.IGNORECASE):
                    classes.append(class_info)

        return classes

    def find_functions(self, pattern: Optional[str] = None) -> List[Dict]:
        """Detectar funciones con patrón opcional"""
        functions = []
        if not self.tree:
            return functions

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [self._get_name(dec) for dec in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node)
                }

                if pattern is None or re.search(pattern, node.name, re.IGNORECASE):
                    functions.append(func_info)

        return functions

    def find_imports(self) -> Dict[str, List]:
        """Detectar imports y analizar conflictos"""
        imports = {"regular": [], "from_imports": [], "conflicts": []}
        if not self.tree:
            return imports

        imported_names = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in imported_names:
                        imports["conflicts"].append({
                            "name": name,
                            "line": node.lineno,
                            "type": "duplicate_import"
                        })
                    imported_names.add(name)
                    imports["regular"].append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in imported_names:
                        imports["conflicts"].append({
                            "name": name,
                            "line": node.lineno,
                            "type": "duplicate_import"
                        })
                    imported_names.add(name)
                    imports["from_imports"].append({
                        "module": node.module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })

        return imports

    def find_duplicates(self) -> Dict[str, List]:
        """Detectar funciones y clases duplicadas"""
        duplicates = {"functions": [], "classes": []}
        if not self.tree:
            return duplicates

        func_names = {}
        class_names = {}

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in func_names:
                    duplicates["functions"].append({
                        "name": node.name,
                        "lines": [func_names[node.name], node.lineno],
                        "type": "duplicate_function"
                    })
                else:
                    func_names[node.name] = node.lineno

            elif isinstance(node, ast.ClassDef):
                if node.name in class_names:
                    duplicates["classes"].append({
                        "name": node.name,
                        "lines": [class_names[node.name], node.lineno],
                        "type": "duplicate_class"
                    })
                else:
                    class_names[node.name] = node.lineno

        return duplicates

    def find_indentation_issues(self) -> List[Dict]:
        """Detectar problemas de indentación"""
        issues = []
        expected_indent = 0

        for i, line in enumerate(self.lines, 1):
            if line.strip():  # Ignorar líneas vacías
                current_indent = len(line) - len(line.lstrip())

                # Detectar indentación inconsistente
                if current_indent % 4 != 0 and current_indent > 0:
                    issues.append({
                        "line": i,
                        "type": "inconsistent_indentation",
                        "message": f"Indentación no múltiplo de 4: {current_indent} espacios",
                        "content": line.strip()
                    })

                # Detectar mezcla de tabs y espacios
                if '\t' in line and ' ' in line[:current_indent]:
                    issues.append({
                        "line": i,
                        "type": "mixed_indentation",
                        "message": "Mezcla de tabs y espacios",
                        "content": line.strip()
                    })

        return issues

    def find_logical_errors(self) -> List[Dict]:
        """Detectar errores lógicos comunes"""
        errors = []
        if not self.tree:
            return errors

        for node in ast.walk(self.tree):
            # Variables no utilizadas
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Simplificado: detectar asignaciones que parecen no usadas
                        var_name = target.id
                        if var_name.startswith('_') and len(var_name) > 1:
                            errors.append({
                                "line": node.lineno,
                                "type": "unused_variable",
                                "message": f"Variable posiblemente no utilizada: {var_name}",
                                "variable": var_name
                            })

            # Comparaciones peligrosas
            elif isinstance(node, ast.Compare):
                if len(node.ops) == 1 and isinstance(node.ops[0], ast.Is):
                    if isinstance(node.comparators[0], (ast.Constant, ast.Num, ast.Str)):
                        errors.append({
                            "line": node.lineno,
                            "type": "dangerous_comparison",
                            "message": "Uso de 'is' con literal, usar '==' en su lugar"
                        })

        return errors

    def _get_name(self, node) -> str:
        """Obtener nombre de un nodo AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node)


def extend_msearch_with_explorer(body: Dict) -> Dict:
    """Extender msearch con capacidades de exploración"""

    root = body.get("root_path") or body.get("path") or os.getcwd()
    max_depth = body.get("max_depth", 3)
    filters = body.get("filters", {})

    if not os.path.exists(root):
        return {"exito": False, "error": f"Ruta no encontrada: {root}", "source": "local_filesystem"}

    explorer = ProjectExplorer(root)
    structure = explorer.get_structure(max_depth, filters)

    return {
        "exito": True,
        "mode": "explore",
        "structure": structure,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
    }


def is_local_path(path: str) -> bool:
    """Detectar si es ruta local de Windows/Unix"""
    if not path:
        return False
    # Rutas Windows: C:/, D:/, etc.
    if re.match(r'^[A-Za-z]:[/\\]', path):
        return True
    # Rutas absolutas Unix: /home, /usr, etc.
    if path.startswith('/'):
        return True
    # Rutas relativas con ./ o ../
    if path.startswith(('./')) or path.startswith('../'):
        return True
    # Wildcards con rutas locales
    if '*' in path and (':' in path or '/' in path or '\\' in path):
        return True
    return False


def process_msearch_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """Procesar solicitud de búsqueda semántica"""

    # Extraer parámetros de forma dinámica
    file_path = body.get("file_path") or body.get("ruta") or body.get("path")
    content = body.get("content") or body.get("contenido")
    search_type = body.get("search_type") or body.get("tipo") or "all"
    pattern = body.get("pattern") or body.get("patron")

    if not file_path and not content:
        return {
            "exito": False,
            "error": "Se requiere 'file_path' o 'content'",
            "campos_aceptados": ["file_path", "ruta", "path", "content", "contenido", "search_type", "tipo", "pattern", "patron"]
        }

    # 🔍 DETECCIÓN AUTOMÁTICA: Ruta local vs Azure Blob
    if file_path and is_local_path(file_path):
        logging.info(f"🔍 Ruta local detectada: {file_path}")

        # Si tiene wildcard, buscar archivos con glob recursivo
        if '*' in file_path:
            import glob

            # Convertir patrón a recursivo si no lo es
            patron_recursivo = file_path
            if '**' not in file_path:
                # Insertar ** antes del patrón de archivo
                partes = file_path.rsplit('/', 1)
                if len(partes) == 2:
                    patron_recursivo = f"{partes[0]}/**/{partes[1]}"
                else:
                    patron_recursivo = f"**/{file_path}"

            archivos_encontrados = glob.glob(patron_recursivo, recursive=True)
            logging.info(
                f"📁 Patrón {patron_recursivo} → {len(archivos_encontrados)} archivos")

            if archivos_encontrados:
                return {
                    "exito": True,
                    "mode": "file_search",
                    "patron": file_path,
                    "patron_usado": patron_recursivo,
                    "archivos_encontrados": [str(Path(f).name) for f in archivos_encontrados[:100]],
                    "total": len(archivos_encontrados),
                    "rutas_completas": archivos_encontrados[:100],
                    "mensaje": f"Encontrados {len(archivos_encontrados)} archivos que coinciden con '{file_path}'"
                }
            else:
                return {
                    "exito": False,
                    "error": f"No se encontraron archivos con el patrón: {file_path}",
                    "patron": file_path,
                    "patron_usado": patron_recursivo,
                    "sugerencia": "Verifica que la ruta y el patrón sean correctos. Usa C:/ruta/**/*_test.py para búsqueda recursiva."
                }

        # Si es archivo específico, leer localmente
        if os.path.exists(file_path):
            try:
                content = Path(file_path).read_text(encoding='utf-8')
                logging.info(f"✅ Archivo local leído: {file_path}")
            except Exception as e:
                return {"exito": False, "error": f"Error leyendo archivo local: {str(e)}"}
        else:
            return {"exito": False, "error": f"Archivo local no encontrado: {file_path}"}

    # Manejar búsqueda en todos los archivos (Azure Blob)
    elif file_path == "*":
        return search_all_files(search_type, pattern)

    # Leer archivo si se proporciona ruta
    if file_path and not content:
        # FALLBACK LOCAL: Si existe localmente, delegar a ejecutar-cli
        if os.path.exists(file_path):
            logging.info(
                f"msearch: ruta local detectada, delegando a ejecutar-cli")
            try:
                cmd = f'findstr "{pattern or ""}" "{file_path}"' if pattern else f'type "{file_path}"'

                # Invocar ejecutar-cli internamente
                from endpoints.ejecutar_cli import ejecutar_cli_http
                mock_req = func.HttpRequest(
                    method="POST",
                    url="http://localhost/api/ejecutar-cli",
                    body=json.dumps({"comando": cmd}).encode(),
                    headers={"Content-Type": "application/json"}
                )
                response = ejecutar_cli_http(mock_req)
                return json.loads(response.get_body().decode())
            except Exception as e:
                logging.error(f"Error delegando a ejecutar-cli: {e}")

        # Si no existe localmente, intentar Azure Blob
        try:
            from utils_helpers import get_blob_client, PROJECT_ROOT, IS_AZURE, CONTAINER_NAME

            if IS_AZURE:
                client = get_blob_client()
                if client:
                    container_client = client.get_container_client(
                        CONTAINER_NAME)
                    blob_client = container_client.get_blob_client(file_path)
                    content = blob_client.download_blob().readall().decode('utf-8')
            else:
                # Leer local
                full_path = PROJECT_ROOT / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                else:
                    return {"exito": False, "error": f"Archivo no encontrado: {file_path}"}

        except Exception as e:
            return {"exito": False, "error": f"Error leyendo archivo: {str(e)}"}

    if not content:
        return {"exito": False, "error": "No se pudo obtener contenido del archivo"}

    # Realizar análisis semántico
    analyzer = SemanticAnalyzer(content, file_path or "")

    results = {
        "exito": True,
        "file_path": file_path,
        "analysis_type": search_type,
        "pattern": pattern,
        "results": {}
    }

    # Ejecutar análisis según tipo solicitado
    if search_type in ["all", "classes"]:
        results["results"]["classes"] = analyzer.find_classes(pattern)

    if search_type in ["all", "functions"]:
        results["results"]["functions"] = analyzer.find_functions(pattern)

    if search_type in ["all", "imports"]:
        results["results"]["imports"] = analyzer.find_imports()

    if search_type in ["all", "duplicates"]:
        results["results"]["duplicates"] = analyzer.find_duplicates()

    if search_type in ["all", "indentation"]:
        results["results"]["indentation_issues"] = analyzer.find_indentation_issues()

    if search_type in ["all", "logical_errors"]:
        results["results"]["logical_errors"] = analyzer.find_logical_errors()

    if search_type in ["all", "syntax_errors"]:
        results["results"]["syntax_errors"] = analyzer.parse_errors

    # Agregar estadísticas
    results["statistics"] = {
        "total_lines": len(analyzer.lines),
        "classes_found": len(results["results"].get("classes", [])),
        "functions_found": len(results["results"].get("functions", [])),
        "imports_found": len(results["results"].get("imports", {}).get("regular", [])) + len(results["results"].get("imports", {}).get("from_imports", [])),
        "issues_found": len(results["results"].get("indentation_issues", [])) + len(results["results"].get("logical_errors", [])) + len(results["results"].get("syntax_errors", []))
    }

    return results


def search_all_files(search_type: str, pattern: Optional[str] = None) -> Dict[str, Any]:
    """Buscar patrón en todos los archivos del proyecto"""
    from utils_helpers import get_blob_client, PROJECT_ROOT, IS_AZURE, CONTAINER_NAME

    all_results = {
        "exito": True,
        "search_type": search_type,
        "pattern": pattern,
        "files_analyzed": [],
        "matches": [],
        "total_files": 0,
        "files_with_matches": 0
    }

    try:
        if IS_AZURE:
            client = get_blob_client()
            if not client:
                return {"exito": False, "error": "No se pudo conectar a Azure Blob Storage"}

            container_client = client.get_container_client(CONTAINER_NAME)
            blobs = container_client.list_blobs()

            for blob in blobs:
                if blob.name.endswith(('.py', '.js', '.ts', '.json', '.md', '.txt')):
                    all_results["total_files"] += 1
                    try:
                        blob_client = container_client.get_blob_client(
                            blob.name)
                        content = blob_client.download_blob().readall().decode('utf-8')

                        # Buscar patrón en contenido
                        if pattern and re.search(pattern, content, re.IGNORECASE):
                            matches = find_pattern_matches(
                                content, pattern, blob.name)
                            if matches:
                                all_results["matches"].extend(matches)
                                all_results["files_with_matches"] += 1

                        all_results["files_analyzed"].append(blob.name)

                    except Exception as e:
                        logging.warning(
                            f"Error procesando {blob.name}: {str(e)}")
        else:
            # Búsqueda local
            for file_path in PROJECT_ROOT.rglob('*'):
                if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.json', '.md', '.txt']:
                    all_results["total_files"] += 1
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        relative_path = str(
                            file_path.relative_to(PROJECT_ROOT))

                        # Buscar patrón en contenido
                        if pattern and re.search(pattern, content, re.IGNORECASE):
                            matches = find_pattern_matches(
                                content, pattern, relative_path)
                            if matches:
                                all_results["matches"].extend(matches)
                                all_results["files_with_matches"] += 1

                        all_results["files_analyzed"].append(relative_path)

                    except Exception as e:
                        logging.warning(
                            f"Error procesando {file_path}: {str(e)}")

    except Exception as e:
        return {"exito": False, "error": f"Error en búsqueda global: {str(e)}"}

    return all_results


def find_pattern_matches(content: str, pattern: str, file_path: str) -> List[Dict]:
    """Encontrar coincidencias de patrón en contenido"""
    matches = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        if re.search(pattern, line, re.IGNORECASE):
            matches.append({
                "file": file_path,
                "line": line_num,
                "content": line.strip(),
                "match": pattern
            })

    return matches


@app.function_name(name="msearch")
@app.route(route="msearch", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def msearch_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint de búsqueda semántica avanzada para análisis de código"""

    run_id = get_run_id()

    try:
        # Validar JSON de entrada
        try:
            body = req.get_json()
            if body is None:
                body = {}
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "JSON inválido en el cuerpo de la solicitud",
                    "run_id": run_id
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        # Si se solicita modo "explore", delegar al explorador
        if body.get("mode") == "explore":
            explorer_resp = extend_msearch_with_explorer(body)
            # Si la función ya devuelve HttpResponse, retornarla directamente
            if isinstance(explorer_resp, func.HttpResponse):
                return explorer_resp
            # Si devuelve un dict o lista, serializar a HttpResponse JSON
            if isinstance(explorer_resp, (dict, list)):
                return func.HttpResponse(
                    json.dumps(explorer_resp, ensure_ascii=False, indent=2),
                    mimetype="application/json",
                    status_code=200
                )
            # Si devuelve una cadena, devolverla tal cual (asumiendo JSON o texto)
            if isinstance(explorer_resp, str):
                return func.HttpResponse(
                    explorer_resp,
                    mimetype="application/json",
                    status_code=200
                )
            # Fallback: convertir el resultado a JSON dentro de un objeto
            return func.HttpResponse(
                json.dumps({"exito": True, "result": explorer_resp},
                           ensure_ascii=False, indent=2),
                mimetype="application/json",
                status_code=200
            )

        # Procesar solicitud
        result = process_msearch_request(body)
        result["run_id"] = run_id
        result["timestamp"] = datetime.now().isoformat()

        # Determinar código de estado (siempre 200 para evitar errores en agente)
        status_code = 200

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=status_code
        )

    except Exception as e:
        logging.exception(f"[{run_id}] Error en msearch: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Error interno: {str(e)}",
                "error_type": type(e).__name__,
                "run_id": run_id,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
