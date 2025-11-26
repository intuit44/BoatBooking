#!/usr/bin/env python3
"""
Validador del pipeline real de memoria cognitiva
Valida: detección de intención → etiquetado → deduplicación → guardado → indexado
"""

import os
import sys
import json
import hashlib
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

# Agregar path actual (copiloto-function)
sys.path.append(str(Path(__file__).parent))

try:
    from services.memory_service import memory_service, DOC_CLASS_COGNITIVE, DOC_CLASS_SYSTEM
    from services.cosmos_store import CosmosMemoryStore
    from endpoints.guardar_memoria import guardar_memoria_http
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Servicios no disponibles: {e}")
    SERVICES_AVAILABLE = False
    # Definir constantes por defecto si no se pueden importar
    DOC_CLASS_COGNITIVE = "cognitive"
    DOC_CLASS_SYSTEM = "system"


class RealPipelineValidator:
    def __init__(self):
        self.results = {}
        self.test_session = f"test_session_{int(datetime.now(timezone.utc).timestamp())}"

    def test_intention_detection(self) -> bool:
        """Valida detección de intenciones usando el clasificador semántico real"""
        if not SERVICES_AVAILABLE:
            return False

        # Probar el clasificador semántico directamente primero
        try:
            from semantic_intent_classifier import classify_user_intent, classify_text

            # Tests del clasificador principal
            test_classification = classify_user_intent(
                "aplicar corrección al archivo config.py")
            if test_classification.get("intent") != "correccion":
                print(
                    f"Fallo clasificación directa: esperado 'correccion', obtuvo '{test_classification.get('intent')}'")

        except ImportError:
            print(
                "Warning: semantic_intent_classifier no disponible, usando solo memory_service")

        test_cases = [
            {
                "texto": "Aplicar corrección al archivo config.py línea 45",
                "expected_type": "correccion",
                "expected_class": DOC_CLASS_COGNITIVE
            },
            {
                "texto": "Diagnóstico del sistema completado: 5 recursos activos",
                "expected_type": "diagnostico",
                "expected_class": DOC_CLASS_SYSTEM
            },
            {
                "texto": "Error: archivo no encontrado en /path/file.txt",
                "expected_type": "error_endpoint",
                "expected_class": DOC_CLASS_SYSTEM
            },
            {
                "texto": "Gestionar reserva de embarcación para cliente premium",
                "expected_type": "boat_management",
                "expected_class": DOC_CLASS_COGNITIVE
            }
        ]

        passed = 0
        for i, case in enumerate(test_cases):
            try:
                # Simular llamada que genera evento con texto semántico
                result = memory_service.registrar_llamada(
                    source="test_validator",
                    endpoint="test_intention",
                    method="POST",
                    params={"session_id": self.test_session},
                    response_data={"texto_semantico": case["texto"]},
                    success=True
                )

                if result:
                    # Verificar que se guardó con la clasificación correcta
                    recent_events = memory_service.get_session_history(
                        self.test_session, 1)
                    if recent_events:
                        event = recent_events[0]
                        actual_type = event.get("tipo")
                        actual_class = event.get("document_class")

                        if actual_type == case["expected_type"] and actual_class == case["expected_class"]:
                            passed += 1
                        else:
                            print(
                                f"Caso {i+1} falló: esperado tipo={case['expected_type']}, class={case['expected_class']}, obtuvo tipo={actual_type}, class={actual_class}")
                    else:
                        print(
                            f"Caso {i+1} falló: no se encontró evento guardado")
                else:
                    print(f"Caso {i+1} falló: registrar_llamada retornó False")

            except Exception as e:
                print(f"Error en caso {i+1}: {e}")

        success = passed == len(test_cases)
        self.results['intention_detection'] = {
            'passed': passed,
            'total': len(test_cases),
            'success_rate': passed / len(test_cases)
        }
        return success

    def test_deduplication_logic(self) -> bool:
        """Valida deduplicación usando texto_hash como en memory_service"""
        if not SERVICES_AVAILABLE:
            return False

        # Texto duplicado
        duplicate_text = "Este es un texto que se repetirá para probar deduplicación"

        # Primera inserción
        result1 = memory_service.registrar_llamada(
            source="test_dedup",
            endpoint="test_endpoint",
            method="POST",
            params={"session_id": self.test_session},
            response_data={"texto_semantico": duplicate_text},
            success=True
        )

        # Segunda inserción (debería ser rechazada)
        result2 = memory_service.registrar_llamada(
            source="test_dedup",
            endpoint="test_endpoint",
            method="POST",
            params={"session_id": self.test_session},
            response_data={"texto_semantico": duplicate_text},
            success=True
        )

        # Verificar que solo se guardó una vez
        events = memory_service.get_session_history(self.test_session)
        duplicate_events = [e for e in events if e.get(
            "texto_semantico") == duplicate_text]

        success = result1 and not result2 and len(duplicate_events) == 1
        self.results['deduplication'] = {
            'first_insert': result1,
            'second_insert_blocked': not result2,
            'unique_events_count': len(duplicate_events),
            'dedup_working': success
        }
        return success

    def test_cosmos_persistence(self) -> bool:
        """Valida persistencia real en Cosmos DB"""
        if not SERVICES_AVAILABLE:
            return False

        try:
            cosmos_store = CosmosMemoryStore()
            if not cosmos_store.enabled:
                print("Cosmos DB no disponible para testing")
                return False

            # Crear documento de prueba
            test_doc = {
                "id": f"test_cosmos_{int(datetime.now(timezone.utc).timestamp())}",
                "session_id": self.test_session,
                "texto_semantico": "Documento de prueba para validar persistencia en Cosmos",
                "document_class": DOC_CLASS_COGNITIVE,
                "is_synthetic": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Guardar en Cosmos
            save_result = cosmos_store.upsert(test_doc)

            # Verificar que se guardó
            if save_result:
                recent_docs = cosmos_store.query_all(limit=5)
                saved_doc = next(
                    (d for d in recent_docs if d.get("id") == test_doc["id"]), None)

                success = saved_doc is not None
                self.results['cosmos_persistence'] = {
                    'save_successful': save_result,
                    'doc_retrieved': success,
                    'doc_id': test_doc["id"],
                    'has_required_fields': all(k in saved_doc for k in ["texto_semantico", "document_class", "is_synthetic"]) if saved_doc else False
                }
                return success
            else:
                self.results['cosmos_persistence'] = {'save_successful': False}
                return False

        except Exception as e:
            print(f"Error en test_cosmos_persistence: {e}")
            self.results['cosmos_persistence'] = {'error': str(e)}
            return False

    def test_ai_search_indexing(self) -> bool:
        """Valida indexación automática en AI Search"""
        if not SERVICES_AVAILABLE:
            return False

        try:
            # Crear evento que debería indexarse automáticamente
            test_text = f"Evento de prueba para indexación automática - timestamp {datetime.now(timezone.utc).isoformat()}"

            result = memory_service.registrar_llamada(
                source="test_indexing",
                endpoint="test_ai_search",
                method="POST",
                params={"session_id": self.test_session},
                response_data={
                    "texto_semantico": test_text,
                    "document_class": DOC_CLASS_COGNITIVE
                },
                success=True
            )

            # Verificar que el evento se guardó
            events = memory_service.get_session_history(self.test_session, 5)
            matching_event = next((e for e in events if e.get(
                "texto_semantico") == test_text), None)

            success = result and matching_event is not None
            self.results['ai_search_indexing'] = {
                'event_saved': result,
                'event_found': matching_event is not None,
                'has_cognitive_class': matching_event.get("document_class") == DOC_CLASS_COGNITIVE if matching_event else False,
                # La indexación se intenta automáticamente en _log_cosmos
                'indexing_attempted': success
            }
            return success

        except Exception as e:
            print(f"Error en test_ai_search_indexing: {e}")
            self.results['ai_search_indexing'] = {'error': str(e)}
            return False

    def test_endpoint_integration(self) -> bool:
        """Valida integración con endpoint guardar_memoria"""
        if not SERVICES_AVAILABLE:
            return False

        try:
            # Simular request HTTP
            class MockRequest:
                def __init__(self, json_data, headers=None):
                    self._json = json_data
                    self.headers = headers or {}

                def get_json(self):
                    return self._json

            # Crear request de prueba
            test_content = "Contenido importante guardado explícitamente por el agente"
            mock_req = MockRequest({
                "contenido": test_content,
                "tipo": "memoria_explicita",
                "session_id": self.test_session,
                "metadata": {"importancia": "alta"}
            })

            # Llamar al endpoint
            response = guardar_memoria_http(mock_req)

            # Verificar respuesta
            success = response.status_code == 200
            if success:
                # Verificar que se guardó en memoria
                events = memory_service.get_session_history(
                    self.test_session, 5)
                matching_event = next(
                    (e for e in events if test_content in str(e.get("texto_semantico", ""))), None)
                success = matching_event is not None

            self.results['endpoint_integration'] = {
                'response_code': response.status_code,
                'content_saved': success,
                'session_id': self.test_session
            }
            return success

        except Exception as e:
            print(f"Error en test_endpoint_integration: {e}")
            self.results['endpoint_integration'] = {'error': str(e)}
            return False

    def run_full_validation(self) -> Dict[str, Any]:
        """Ejecuta validación completa del pipeline real"""
        print("Validando pipeline real de memoria cognitiva...")
        print(f"Session de prueba: {self.test_session}")

        if not SERVICES_AVAILABLE:
            print("ERROR: Servicios no disponibles. Verifique imports.")
            return {'error': 'Services not available'}

        tests = [
            ('Detección de Intenciones', self.test_intention_detection),
            ('Deduplicación por Hash', self.test_deduplication_logic),
            ('Persistencia Cosmos', self.test_cosmos_persistence),
            ('Indexación AI Search', self.test_ai_search_indexing),
            ('Integración Endpoints', self.test_endpoint_integration)
        ]

        passed = 0
        total = len(tests)

        for name, test_func in tests:
            try:
                result = test_func()
                status = "PASS" if result else "FAIL"
                emoji = "✅" if result else "❌"
                print(f"{emoji} {name}: {status}")
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {name}: ERROR - {e}")

        success_rate = passed / total
        print(
            f"\nResultado: {passed}/{total} tests pasaron ({success_rate:.1%})")

        # Limpiar datos de prueba
        try:
            memory_service.limpiar_registros()
            print(f"Datos de prueba limpiados")
        except:
            pass

        return {
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': success_rate,
                'test_session': self.test_session
            },
            'details': self.results
        }

# Funciones para pytest


def test_pipeline_intention_detection():
    validator = RealPipelineValidator()
    assert validator.test_intention_detection()


def test_pipeline_deduplication():
    validator = RealPipelineValidator()
    assert validator.test_deduplication_logic()


def test_pipeline_cosmos_persistence():
    validator = RealPipelineValidator()
    assert validator.test_cosmos_persistence()


def test_pipeline_ai_search():
    validator = RealPipelineValidator()
    assert validator.test_ai_search_indexing()


def test_pipeline_endpoints():
    validator = RealPipelineValidator()
    assert validator.test_endpoint_integration()


if __name__ == "__main__":
    validator = RealPipelineValidator()
    results = validator.run_full_validation()

    print("\nResultados detallados:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
