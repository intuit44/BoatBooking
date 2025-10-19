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
from function_app import app
from utils_helpers import get_run_id

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
    
    def find_classes(self, pattern: str = None) -> List[Dict]:
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
    
    def find_functions(self, pattern: str = None) -> List[Dict]:
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
    
    # Leer archivo si se proporciona ruta
    if file_path and not content:
        try:
            # Intentar leer desde Azure Blob o local
            from utils_helpers import get_blob_client, PROJECT_ROOT, IS_AZURE, CONTAINER_NAME
            
            if IS_AZURE:
                client = get_blob_client()
                if client:
                    container_client = client.get_container_client(CONTAINER_NAME)
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
        
        # Procesar solicitud
        result = process_msearch_request(body)
        result["run_id"] = run_id
        result["timestamp"] = datetime.now().isoformat()
        
        # Determinar código de estado
        status_code = 200 if result.get("exito") else 400
        
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