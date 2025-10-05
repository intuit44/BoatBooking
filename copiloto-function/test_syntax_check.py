#!/usr/bin/env python3
"""
Script para verificar sintaxis y imports antes del build Docker
"""

import ast
import sys
from pathlib import Path

def check_python_syntax(file_path):
    """Verifica la sintaxis de un archivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compilar el código para verificar sintaxis
        ast.parse(content)
        print(f"✅ Sintaxis correcta: {file_path}")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en {file_path}:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error verificando {file_path}: {e}")
        return False

def check_imports():
    """Verifica que los imports críticos estén disponibles"""
    critical_imports = [
        'azure.functions',
        'azure.identity',
        'azure.monitor.query',
        'azure.cosmos',
        'azure.storage.blob',
        'json',
        'datetime',
        'subprocess',
        'os'
    ]
    
    print("\n🔍 Verificando imports críticos:")
    all_good = True
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            all_good = False
        except Exception as e:
            print(f"⚠️  {module}: {e}")
    
    return all_good

def main():
    print("=" * 60)
    print("VERIFICACIÓN PRE-BUILD: SINTAXIS Y DEPENDENCIAS")
    print("=" * 60)
    
    # Verificar sintaxis del archivo principal
    function_app_path = Path("function_app.py")
    
    if not function_app_path.exists():
        print(f"❌ No se encontró function_app.py")
        sys.exit(1)
    
    syntax_ok = check_python_syntax(function_app_path)
    imports_ok = check_imports()
    
    print("\n" + "=" * 60)
    print("RESULTADO:")
    
    if syntax_ok and imports_ok:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("🚀 Listo para docker build")
        sys.exit(0)
    else:
        print("❌ HAY ERRORES QUE CORREGIR")
        print("🛑 NO hacer docker build hasta corregir")
        sys.exit(1)

if __name__ == "__main__":
    main()