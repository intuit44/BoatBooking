#!/usr/bin/env python3
"""
Script para ejecutar tests del pipeline con pytest
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Ejecuta tests usando pytest"""
    # Configurar encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Cambiar al directorio copiloto-function
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Ejecutando tests del pipeline desde: {project_root}")
    print("Ejecutando tests del pipeline con pytest...")
    
    try:
        # Ejecutar pytest en el archivo de tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_pipeline.py", 
            "-v", "--tb=short"
        ], text=True, encoding='utf-8')
        
        return result.returncode
        
    except Exception as e:
        print(f"Error ejecutando pytest: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)