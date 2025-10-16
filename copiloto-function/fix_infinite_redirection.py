#!/usr/bin/env python3
"""
Script para corregir el problema de redireccion infinita en /api/revisar-correcciones
"""
import os
import re

def find_function_app_py():
    """Encontrar el archivo function_app.py"""
    current_dir = os.getcwd()
    function_app_path = os.path.join(current_dir, "function_app.py")
    
    if os.path.exists(function_app_path):
        return function_app_path
    else:
        print(f"ERROR: No se encontro function_app.py en {current_dir}")
        return None

def backup_file(file_path):
    """Crear backup del archivo original"""
    backup_path = f"{file_path}.backup"
    with open(file_path, 'r', encoding='utf-8') as original:
        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(original.read())
    print(f"Backup creado: {backup_path}")
    return backup_path

def fix_infinite_redirection(file_path):
    """Aplicar fix para redireccion infinita"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la funcion revisar_correcciones
    pattern = r'(@app\.route\(["\']\/api\/revisar-correcciones["\'].*?\ndef\s+revisar_correcciones.*?)(def\s+\w+|@app\.route|$)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("ERROR: No se encontro la funcion revisar_correcciones")
        return False
    
    function_content = match.group(1)
    
    # Verificar si ya tiene el guard clause
    if "Previniendo redireccion infinita" in function_content:
        print("INFO: El guard clause ya existe")
        return True
    
    # Buscar donde insertar el guard clause
    # Buscar despues de obtener req o al inicio de la funcion
    guard_clause = '''
    # Guard clause para prevenir redireccion infinita
    if req.url.endswith("/api/revisar-correcciones"):
        try:
            # Verificar si hay deteccion de intencion que cause redireccion
            from detectar_intencion import detectar_intencion
            deteccion = detectar_intencion("revisar correcciones", {})
            
            if deteccion.get("redirigir"):
                destino = deteccion.get("endpoint_destino", "")
                if "revisar-correcciones" in destino:
                    logging.warning("🚫 Previniendo redireccion infinita en revisar-correcciones")
                    deteccion["redirigir"] = False
        except Exception as e:
            logging.warning(f"Error en guard clause: {e}")
    '''
    
    # Buscar el punto de insercion (despues de def revisar_correcciones)
    def_pattern = r'(def\s+revisar_correcciones.*?:\s*)'
    def_match = re.search(def_pattern, function_content)
    
    if def_match:
        # Insertar el guard clause despues de la definicion de la funcion
        insertion_point = def_match.end()
        
        new_function = (function_content[:insertion_point] + 
                       guard_clause + 
                       function_content[insertion_point:])
        
        # Reemplazar en el contenido completo
        new_content = content.replace(function_content, new_function)
        
        # Escribir el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("SUCCESS: Guard clause agregado exitosamente")
        return True
    else:
        print("ERROR: No se pudo encontrar el punto de insercion")
        return False

def main():
    """Ejecutar la correccion"""
    print("APLICANDO CORRECCION PARA REDIRECCION INFINITA")
    print("=" * 50)
    
    # Encontrar function_app.py
    file_path = find_function_app_py()
    if not file_path:
        return False
    
    print(f"Archivo encontrado: {file_path}")
    
    # Crear backup
    backup_path = backup_file(file_path)
    
    # Aplicar correccion
    success = fix_infinite_redirection(file_path)
    
    if success:
        print("\nCORRECCION APLICADA EXITOSAMENTE")
        print("=" * 35)
        print("1. Guard clause agregado en revisar_correcciones")
        print("2. Backup creado en:", backup_path)
        print("3. Reinicia el servidor para aplicar cambios")
        print("\nPara revertir: cp function_app.py.backup function_app.py")
    else:
        print("\nERROR AL APLICAR CORRECCION")
        print("Restaurando desde backup...")
        os.rename(backup_path, file_path)
    
    return success

if __name__ == "__main__":
    main()