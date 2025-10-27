"""
🧪 Pruebas Críticas de Preparación para Producción
Valida que todos los componentes del sistema LLM robusto funcionen correctamente
"""

import requests
import json
import time
import logging
from typing import Dict, Any, List

# Configuración
BASE_URL = "http://localhost:7071/api"
HEADERS = {"Content-Type": "application/json"}

class ProductionReadinessTest:
    """Suite de pruebas para validar preparación para producción"""
    
    def __init__(self):
        self.results = []
        self.session_id = f"test_{int(time.time())}"
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Registra resultado de prueba"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_historial_endpoint_basic(self) -> bool:
        """Prueba 1: Endpoint historial-interacciones responde correctamente"""
        try:
            response = requests.post(
                f"{BASE_URL}/historial-interacciones",
                headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": "test_agent"},
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["interpretacion_semantica", "contexto_inteligente", "validation_applied"]
                
                has_all_fields = all(field in data for field in required_fields)
                self.log_test("Historial Endpoint Basic", has_all_fields, 
                            f"Status: {response.status_code}, Fields: {list(data.keys())}")
                return has_all_fields
            else:
                self.log_test("Historial Endpoint Basic", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Historial Endpoint Basic", False, f"Error: {str(e)}")
            return False
    
    def test_semantic_classification(self) -> bool:
        """Prueba 2: Clasificación semántica funciona correctamente"""
        try:
            # Simular interacciones con diferentes patrones
            test_interactions = [
                {"texto_semantico": "Error en ejecución de comando az storage", "endpoint": "ejecutar_cli"},
                {"texto_semantico": "Verificando estado del sistema", "endpoint": "verificar_sistema"},
                {"texto_semantico": "Configurando Azure Function", "endpoint": "configurar_azure"}
            ]
            
            from semantic_classifier import semantic_classifier
            
            classifications = []
            for interaction in test_interactions:
                result = semantic_classifier.classify_interaction(
                    interaction["texto_semantico"], 
                    interaction["endpoint"]
                )
                classifications.append(result)
            
            # Validar que se detecten diferentes intenciones
            intentions = [c["intention"] for c in classifications]
            unique_intentions = len(set(intentions))
            
            success = unique_intentions >= 2  # Al menos 2 intenciones diferentes
            self.log_test("Semantic Classification", success, 
                        f"Intenciones detectadas: {intentions}")
            return success
            
        except Exception as e:
            self.log_test("Semantic Classification", False, f"Error: {str(e)}")
            return False
    
    def test_context_validation(self) -> bool:
        """Prueba 3: Validación de contexto elimina duplicados y optimiza"""
        try:
            from context_validator import context_validator
            
            # Crear contexto con duplicados y ruido
            test_context = {
                "interacciones_recientes": [
                    {"texto_semantico": "Test interaction 1", "endpoint": "test", "timestamp": "2025-01-26T10:00:00"},
                    {"texto_semantico": "Test interaction 1", "endpoint": "test", "timestamp": "2025-01-26T10:01:00"},  # Duplicado
                    {"texto_semantico": "Test interaction 2", "endpoint": "test2", "timestamp": "2025-01-26T10:02:00"},
                ] * 20  # 60 interacciones (muchas duplicadas)
            }
            
            validated = context_validator.validate_and_clean_context(test_context)
            
            # Verificar que se aplicó validación
            validation_applied = validated.get("validation_applied", False)
            stats = validated.get("validation_stats", {})
            final_count = stats.get("final_optimized", 0)
            
            success = validation_applied and final_count < 60  # Debe reducir duplicados
            self.log_test("Context Validation", success, 
                        f"Original: 60, Final: {final_count}, Applied: {validation_applied}")
            return success
            
        except Exception as e:
            self.log_test("Context Validation", False, f"Error: {str(e)}")
            return False
    
    def test_continuity_flow(self) -> bool:
        """Prueba 4: Flujo de continuidad - múltiples interacciones"""
        try:
            # Hacer varias interacciones para crear historial
            interactions = [
                {"endpoint": "verificar-sistema", "action": "diagnóstico"},
                {"endpoint": "ejecutar-cli", "action": "comando fallido"},
                {"endpoint": "historial-interacciones", "action": "consulta contexto"}
            ]
            
            for i, interaction in enumerate(interactions):
                response = requests.post(
                    f"{BASE_URL}/{interaction['endpoint']}",
                    headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": "continuity_test"},
                    json={"test_data": f"interaction_{i}"}
                )
                time.sleep(0.5)  # Pequeña pausa entre interacciones
            
            # Consultar historial final
            final_response = requests.post(
                f"{BASE_URL}/historial-interacciones",
                headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": "continuity_test"},
                json={"query": "¿qué habíamos detectado antes?"}
            )
            
            if final_response.status_code == 200:
                data = final_response.json()
                has_context = data.get("tiene_historial", False)
                interaction_count = data.get("total_interacciones", 0)
                
                success = has_context and interaction_count >= 3
                self.log_test("Continuity Flow", success, 
                            f"Historial: {has_context}, Interacciones: {interaction_count}")
                return success
            else:
                self.log_test("Continuity Flow", False, f"Status: {final_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Continuity Flow", False, f"Error: {str(e)}")
            return False
    
    def test_token_optimization(self) -> bool:
        """Prueba 5: Optimización de tokens funciona"""
        try:
            # Simular muchas interacciones para probar límite de tokens
            large_context = {
                "interacciones_recientes": [
                    {
                        "texto_semantico": f"Interacción muy larga número {i} " + "x" * 200,  # Texto largo
                        "endpoint": f"test_endpoint_{i}",
                        "timestamp": f"2025-01-26T10:{i:02d}:00"
                    }
                    for i in range(50)  # 50 interacciones largas
                ]
            }
            
            from context_validator import context_validator
            optimized = context_validator.validate_and_clean_context(large_context)
            
            stats = optimized.get("validation_stats", {})
            original_count = stats.get("original_count", 0)
            final_count = stats.get("final_optimized", 0)
            
            # Debe reducir significativamente el número de interacciones
            success = final_count < original_count and final_count <= 15
            self.log_test("Token Optimization", success, 
                        f"Reducido de {original_count} a {final_count} interacciones")
            return success
            
        except Exception as e:
            self.log_test("Token Optimization", False, f"Error: {str(e)}")
            return False
    
    def test_cross_agent_memory(self) -> bool:
        """Prueba 6: Memoria cruzada entre agentes"""
        try:
            agent_a_id = "agent_a_test"
            agent_b_id = "agent_b_test"
            
            # Interacción con Agent A
            requests.post(
                f"{BASE_URL}/verificar-sistema",
                headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": agent_a_id},
                json={"test": "agent_a_action"}
            )
            
            time.sleep(0.5)
            
            # Interacción con Agent B
            requests.post(
                f"{BASE_URL}/ejecutar-cli",
                headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": agent_b_id},
                json={"test": "agent_b_action"}
            )
            
            time.sleep(0.5)
            
            # Consultar historial desde Agent A (debe ver acciones de ambos si es memoria universal)
            response = requests.post(
                f"{BASE_URL}/historial-interacciones",
                headers={**HEADERS, "Session-ID": self.session_id, "Agent-ID": agent_a_id},
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                total_interactions = data.get("total_interacciones", 0)
                
                # Si es memoria universal, debe ver interacciones de ambos agentes
                success = total_interactions >= 2
                self.log_test("Cross Agent Memory", success, 
                            f"Interacciones visibles: {total_interactions}")
                return success
            else:
                self.log_test("Cross Agent Memory", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Cross Agent Memory", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todas las pruebas críticas"""
        print("🧪 INICIANDO PRUEBAS CRÍTICAS DE PRODUCCIÓN")
        print("=" * 60)
        
        tests = [
            self.test_historial_endpoint_basic,
            self.test_semantic_classification,
            self.test_context_validation,
            self.test_continuity_flow,
            self.test_token_optimization,
            self.test_cross_agent_memory
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ ERROR en {test_func.__name__}: {str(e)}")
        
        print("=" * 60)
        print(f"📊 RESULTADOS: {passed_tests}/{total_tests} pruebas pasaron")
        
        success_rate = (passed_tests / total_tests) * 100
        ready_for_production = success_rate >= 80  # 80% mínimo para producción
        
        summary = {
            "ready_for_production": ready_for_production,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "detailed_results": self.results,
            "recommendation": "✅ LISTO PARA DESPLIEGUE" if ready_for_production else "❌ REQUIERE CORRECCIONES"
        }
        
        print(f"🎯 RECOMENDACIÓN: {summary['recommendation']}")
        
        return summary

if __name__ == "__main__":
    tester = ProductionReadinessTest()
    results = tester.run_all_tests()
    
    # Guardar resultados detallados
    with open("production_readiness_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Reporte detallado guardado en: production_readiness_report.json")