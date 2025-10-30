"""
Generador de resúmenes semánticos para archivos leídos
Crea descripciones contextuales que el agente puede usar en futuras sesiones
"""
import re
from pathlib import Path

def generar_resumen_archivo(ruta: str, contenido: str) -> str:
    """
    Genera un resumen semántico inteligente del archivo leído
    
    Args:
        ruta: Ruta del archivo
        contenido: Contenido completo del archivo
    
    Returns:
        Resumen descriptivo para guardar en texto_semantico
    """
    nombre = Path(ruta).name
    extension = Path(ruta).suffix.lower()
    lineas = contenido.count('\n') + 1
    caracteres = len(contenido)
    
    # Resumen base
    resumen = f"He leído el archivo '{nombre}' ({caracteres} caracteres, {lineas} líneas). "
    
    # Análisis específico por tipo de archivo
    if extension == '.py':
        funciones = contenido.count('def ')
        clases = contenido.count('class ')
        imports = len(re.findall(r'^import |^from ', contenido, re.MULTILINE))
        resumen += f"Es un archivo Python con {funciones} funciones, {clases} clases y {imports} imports. "
        
        # Detectar endpoints si es function_app.py
        if 'function_app' in nombre.lower():
            endpoints = len(re.findall(r'@app\.route\(', contenido))
            resumen += f"Define {endpoints} endpoints HTTP. "
    
    elif extension == '.md':
        titulos = len(re.findall(r'^#+\s', contenido, re.MULTILINE))
        resumen += f"Es un archivo Markdown con {titulos} secciones. "
        
        # Extraer título principal si existe
        match = re.search(r'^#\s+(.+)$', contenido, re.MULTILINE)
        if match:
            resumen += f"Título: '{match.group(1)}'. "
    
    elif extension == '.json':
        try:
            import json
            data = json.loads(contenido)
            if isinstance(data, dict):
                claves = len(data.keys())
                resumen += f"Es un archivo JSON con {claves} claves principales. "
            elif isinstance(data, list):
                resumen += f"Es un archivo JSON con un array de {len(data)} elementos. "
        except:
            resumen += "Es un archivo JSON. "
    
    elif extension in ['.js', '.ts', '.tsx']:
        funciones = len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*\(|=>\s*{', contenido))
        imports = len(re.findall(r'^import\s', contenido, re.MULTILINE))
        exports = len(re.findall(r'^export\s', contenido, re.MULTILINE))
        resumen += f"Es un archivo {'TypeScript' if extension in ['.ts', '.tsx'] else 'JavaScript'} con {funciones} funciones, {imports} imports y {exports} exports. "
    
    elif extension == '.yaml' or extension == '.yml':
        resumen += "Es un archivo de configuración YAML. "
    
    elif extension == '.txt':
        palabras = len(contenido.split())
        resumen += f"Es un archivo de texto plano con {palabras} palabras. "
    
    # Detectar contenido especial
    if 'TODO' in contenido or 'FIXME' in contenido:
        resumen += "Contiene tareas pendientes (TODO/FIXME). "
    
    if 'README' in nombre.upper():
        resumen += "Es un archivo README con documentación del proyecto. "
    
    if 'config' in nombre.lower() or 'settings' in nombre.lower():
        resumen += "Es un archivo de configuración. "
    
    # Agregar preview del contenido (primeras líneas no vacías)
    lineas_preview = [l.strip() for l in contenido.split('\n')[:5] if l.strip()]
    if lineas_preview:
        preview = ' '.join(lineas_preview[:2])[:200]
        resumen += f"Contenido inicial: {preview}..."
    
    return resumen.strip()
