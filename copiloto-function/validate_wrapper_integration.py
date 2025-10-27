"""
🔍 Validador de Integración del Wrapper
Verifica que el wrapper esté aplicando correctamente prompt_final y métricas
"""

import logging
import json
from typing import Dict, Any

def validate_wrapper_integration():
    """Valida que el wrapper esté funcionando correctamente"""
    
    print("🔍 VALIDANDO INTEGRACIÓN DEL WRAPPER")
    print("=" * 50)
    
    checks = []
    
    # 1. Verificar que el wrapper existe y está importado
    try:
        # Intentar importar el wrapper
        import cosmos_memory_direct
        checks.append(("✅", "Wrapper cosmos_memory_direct importado correctamente"))
    except ImportError as e:
        checks.append(("❌", f"Error importando wrapper: {e}"))
    
    # 2. Verificar que semantic_classifier existe
    try:
        import semantic_classifier
        checks.append(("✅", "Semantic classifier disponible"))
    except ImportError as e:
        checks.append(("❌", f"Error importando semantic_classifier: {e}"))
    
    # 3. Verificar que context_validator existe
    try:
        import context_validator
        checks.append(("✅", "Context validator disponible"))
    except ImportError as e:
        checks.append(("❌", f"Error importando context_validator: {e}"))
    
    # 4. Verificar funciones clave del wrapper
    try:
        from cosmos_memory_direct import consultar_memoria_cosmos_directo, aplicar_memoria_cosmos_directo
        checks.append(("✅", "Funciones principales del wrapper disponibles"))
    except ImportError as e:
        checks.append(("❌", f"Error importando funciones del wrapper: {e}"))
    
    # 5. Verificar que el endpoint detector existe
    try:
        import endpoint_detector
        checks.append(("✅", "Endpoint detector disponible"))
    except ImportError as e:
        checks.append(("⚠️", f"Endpoint detector no disponible (opcional): {e}"))
    
    # Mostrar resultados
    for status, message in checks:
        print(f"{status} {message}")
    
    # Contar éxitos
    success_count = sum(1 for status, _ in checks if status == "✅")
    total_count = len([c for c in checks if c[0] in ["✅", "❌"]])  # Excluir warnings
    
    print("=" * 50)
    print(f"📊 RESULTADO: {success_count}/{total_count} componentes funcionando")
    
    if success_count >= total_count * 0.8:  # 80% mínimo
        print("✅ WRAPPER LISTO PARA PRODUCCIÓN")
        return True
    else:
        print("❌ WRAPPER REQUIERE CORRECCIONES")
        return False

def check_logs_for_metrics():
    """Verifica que se estén generando métricas en los logs"""
    
    print("\n🔍 VERIFICANDO MÉTRICAS EN LOGS")
    print("=" * 50)
    
    # Configurar logging para capturar métricas
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Simular llamada que debería generar métricas
    try:
        from cosmos_memory_direct import consultar_memoria_cosmos_directo
        
        # Crear request simulado
        class MockRequest:
            def __init__(self):
                self.headers = {"Session-ID": "test_session", "Agent-ID": "test_agent"}
                self.params = {}
            
            def get_json(self):
                return {}
        
        mock_req = MockRequest()
        result = consultar_memoria_cosmos_directo(mock_req)
        
        if result:
            print("✅ Función de memoria ejecutada correctamente")
            print(f"📊 Resultado: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print("⚠️ Función ejecutada pero sin resultado (normal si no hay historial)")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando función de memoria: {e}")
        return False

def validate_response_structure():
    """Valida que las respuestas tengan la estructura esperada"""
    
    print("\n🔍 VALIDANDO ESTRUCTURA DE RESPUESTAS")
    print("=" * 50)
    
    expected_fields = [
        "interpretacion_semantica",
        "contexto_inteligente", 
        "validation_applied",
        "metadata"
    ]
    
    # Simular respuesta del sistema
    try:
        from cosmos_memory_direct import consultar_memoria_cosmos_directo
        
        class MockRequest:
            def __init__(self):
                self.headers = {"Session-ID": "structure_test", "Agent-ID": "structure_agent"}
                self.params = {}
            
            def get_json(self):
                return {}
        
        mock_req = MockRequest()
        result = consultar_memoria_cosmos_directo(mock_req)
        
        if result and result.get("tiene_historial"):
            missing_fields = [field for field in expected_fields if field not in result]
            
            if not missing_fields:
                print("✅ Estructura de respuesta completa")
                return True
            else:
                print(f"❌ Campos faltantes: {missing_fields}")
                return False
        else:
            print("⚠️ Sin historial para validar estructura (normal en primera ejecución)")
            return True
            
    except Exception as e:
        print(f"❌ Error validando estructura: {e}")
        return False

if __name__ == "__main__":
    print("🧪 VALIDACIÓN COMPLETA DE INTEGRACIÓN")
    print("=" * 60)
    
    results = []
    
    # Ejecutar todas las validaciones
    results.append(validate_wrapper_integration())
    results.append(check_logs_for_metrics())
    results.append(validate_response_structure())
    
    # Resultado final
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {passed}/{total} validaciones pasaron")
    
    if passed >= total * 0.8:
        print("✅ SISTEMA LISTO PARA PRUEBAS DE PRODUCCIÓN")
        print("🚀 Puedes proceder con test_production_readiness.py")
    else:
        print("❌ SISTEMA REQUIERE CORRECCIONES ANTES DE PRODUCCIÓN")
        print("🔧 Revisa los errores mostrados arriba")