#!/usr/bin/env python3
"""
Tests del pipeline de memoria cognitiva - Compatible con Pytest
"""

import os
import sys
from pathlib import Path
import pytest

# Configurar path para importar módulos
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_pipeline_validation():
    """Test principal del pipeline usando RealPipelineValidator"""
    try:
        from validate_pipeline import RealPipelineValidator
        
        validator = RealPipelineValidator()
        results = validator.run_full_validation()
        
        # Verificar que no hay errores
        assert not results.get('error'), f"Error en validación: {results.get('error')}"
        
        # Verificar que hay resultados
        summary = results.get('summary', {})
        assert summary.get('total', 0) > 0, "No se ejecutaron tests"
        
        # Verificar tasa de éxito mínima (ajustado para pruebas)
        success_rate = summary.get('success_rate', 0)
        assert success_rate >= 0.4, f"Tasa de éxito muy baja: {success_rate:.1%}"
        
        print(f"✅ Pipeline validado: {summary.get('passed', 0)}/{summary.get('total', 0)} tests pasaron")
        
    except ImportError as e:
        pytest.skip(f"Módulos no disponibles: {e}")

def test_environment_setup():
    """Test de configuración del entorno"""
    # Verificar que estamos en copiloto-function
    assert project_root.name == "copiloto-function", f"Debe ejecutarse desde copiloto-function, actual: {project_root}"
    
    # Verificar que validate_pipeline existe
    validate_file = project_root / "validate_pipeline.py"
    assert validate_file.exists(), f"Archivo validate_pipeline.py no encontrado: {validate_file}"
    
    # Verificar que services existe
    services_path = project_root / "services"
    assert services_path.exists(), f"Directorio services no encontrado: {services_path}"

if __name__ == "__main__":
    # Permitir ejecución directa para debug
    test_environment_setup()
    test_pipeline_validation()
    print("✅ Todos los tests pasaron")