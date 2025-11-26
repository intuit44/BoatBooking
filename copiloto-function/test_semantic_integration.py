#!/usr/bin/env python3
"""
Pruebas rápidas para verificar la integración del clasificador semántico con memory_service.
"""

import json
import os
from pathlib import Path

# Asegurar path del proyecto
PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_DIR))


def _load_local_settings() -> None:
    """Carga variables desde local.settings.json para evitar fallos por endpoints ausentes."""
    settings_path = PROJECT_DIR / "local.settings.json"
    if not settings_path.exists():
        return

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        for key, value in (data.get("Values") or {}).items():
            if key and value and key not in os.environ:
                os.environ[key] = str(value)
    except Exception as exc:
        print(f"[WARN] No se pudieron cargar variables locales: {exc}")


_load_local_settings()


def test_semantic_classifier() -> float:
    """Valida que el clasificador reconozca las intenciones más comunes."""
    print("[SEMANTIC] Testing SemanticIntentClassifier...")
    try:
        from semantic_intent_classifier import classify_user_intent
    except Exception as exc:
        print(f"[ERROR] No se pudo importar el clasificador: {exc}")
        return 0.0

    cases = [
        ("aplicar corrección al archivo config.py línea 45", "correccion"),
        ("diagnosticar el sistema completo", "diagnostico"),
        ("gestionar reserva de embarcación", "boat_management"),
        ("ejecutar az group list", "ejecucion_cli"),
        ("escribir archivo de configuración", "operacion_archivo"),
    ]

    passed = 0
    for text, expected in cases:
        result = classify_user_intent(text)
        intent = result.get("intent")
        confidence = result.get("confidence", 0.0)
        status = "[OK]" if intent == expected else "[FAIL]"
        print(
            f"{status} '{text[:50]}...' -> {intent} (conf: {confidence:.2f}) [esperado: {expected}]")
        if intent == expected:
            passed += 1

    total = len(cases)
    print(
        f"[SEMANTIC] Clasificador directo: {passed}/{total} casos correctos ({passed/total*100:.1f}%)")
    return passed / total


def test_memory_service_integration() -> float:
    """Verifica que memory_service use correctamente la intención detectada."""
    print("[SEMANTIC] Testing integración con memory_service...")
    try:
        from services.memory_service import memory_service
    except Exception as exc:
        print(f"[ERROR] No se pudo importar memory_service: {exc}")
        return 0.0

    cases = [
        {
            "source": "test_semantic",
            "endpoint": "/api/test",
            "method": "POST",
            "params": {"session_id": "test_semantic_123"},
            "response_data": {"respuesta_usuario": "Aplicando corrección al archivo principal"},
            "success": True,
            "expected_type": "correccion",
        },
        {
            "source": "test_semantic",
            "endpoint": "/api/diagnostico",
            "method": "GET",
            "params": {"session_id": "test_semantic_123"},
            "response_data": {"respuesta_usuario": "Diagnóstico completado: sistema saludable"},
            "success": True,
            "expected_type": "diagnostico",
        },
    ]

    passed = 0
    for idx, case in enumerate(cases, 1):
        try:
            memory_service.registrar_llamada(
                source=case["source"],
                endpoint=case["endpoint"],
                method=case["method"],
                params=case["params"],
                response_data=case["response_data"],
                success=case["success"],
            )
            events = memory_service.get_session_history(
                case["params"]["session_id"], 1)
            if events:
                detected = events[0].get("tipo")
                status = "[OK]" if detected == case["expected_type"] else "[FAIL]"
                print(
                    f"{status} Caso {idx}: tipo detectado '{detected}' [esperado: '{case['expected_type']}']")
                if detected == case["expected_type"]:
                    passed += 1
            else:
                print(f"[WARN] Caso {idx}: evento no encontrado")
        except Exception as exc:
            print(f"[ERROR] Caso {idx} falló: {exc}")

    total = len(cases)
    print(
        f"[SEMANTIC] Integración memory_service: {passed}/{total} casos correctos ({passed/total*100:.1f}%)")
    return passed / total


def test_conversacion_humana_persistence():
    """Test de persistencia de conversación humana en memory_service"""
    print("\n[CONVERSATION] Testing persistencia de conversación humana...")

    try:
        from services.memory_service import memory_service

        # Caso representativo de request de Foundry
        test_cases = [
            {
                "name": "Foundry correction request",
                "params": {
                    "session_id": "foundry_session_test",
                    "mensaje_usuario": "Corrige fix_123.py",
                    "thread_id": "assistant-XYZ-789",
                    "instrucciones": "Aplica las correcciones necesarias al archivo"
                },
                "response_data": {
                    "respuesta_usuario": "Corrección aplicada exitosamente al archivo fix_123.py",
                    "contexto_conversacion": {
                        "archivo_objetivo": "fix_123.py",
                        "tipo_fix": "syntax_error"
                    },
                    "instrucciones_humanas": "Revisa el archivo y aplica fixes automáticos"
                },
                "expected_checks": {
                    "mensaje_usuario": "Corrige fix_123.py",
                    "mensaje_asistente": "Corrección aplicada exitosamente al archivo fix_123.py",
                    "thread_id": "assistant-XYZ-789",
                    "es_conversacion_humana": True
                }
            },
            {
                "name": "Foundry diagnostic request",
                "params": {
                    "session_id": "foundry_diagnostic_test",
                    "mensaje": "Diagnostica el sistema completo",
                    "Thread-ID": "thread-diagnostic-456"
                },
                "response_data": {
                    "respuesta_usuario": "Diagnóstico completado: todos los servicios operativos",
                    "contexto_inteligente": {
                        "resumen_inteligente": "Sistema saludable - CPU 15%, Memoria 60%"
                    },
                    "thread_id": "thread-diagnostic-456"
                },
                "expected_checks": {
                    "mensaje_usuario": "Diagnostica el sistema completo",
                    "mensaje_asistente": "Diagnóstico completado: todos los servicios operativos",
                    "thread_id": "thread-diagnostic-456",
                    "es_conversacion_humana": True
                }
            }
        ]

        passed = 0
        for case in test_cases:
            try:
                # Registrar llamada con datos de conversación
                memory_service.registrar_llamada(
                    source="foundry_test",
                    endpoint="/api/test-conversation",
                    method="POST",
                    params=case["params"],
                    response_data=case["response_data"],
                    success=True
                )

                # Recuperar evento guardado
                events = memory_service.get_session_history(
                    case["params"]["session_id"], 1)

                if not events:
                    print(f"[FAIL] {case['name']}: evento no encontrado")
                    continue

                event = events[0]
                conversacion = event.get("conversacion_humana", {})

                # Debug: mostrar estructura completa del evento
                print(
                    f"[DEBUG] {case['name']}: conversacion_humana keys: {list(conversacion.keys())}")
                print(
                    f"[DEBUG] {case['name']}: es_conversacion_humana = {event.get('es_conversacion_humana')}")
                if conversacion:
                    print(
                        f"[DEBUG] {case['name']}: conversacion = {conversacion}")

                # Verificar todos los campos esperados
                all_checks_passed = True
                for field, expected_value in case["expected_checks"].items():
                    if field == "es_conversacion_humana":
                        actual_value = event.get(field)
                    else:
                        actual_value = conversacion.get(field)

                    if actual_value != expected_value:
                        print(
                            f"[FAIL] {case['name']}: {field} = '{actual_value}' [esperado: '{expected_value}']")
                        all_checks_passed = False

                if all_checks_passed:
                    print(
                        f"[OK] {case['name']}: todos los campos de conversación guardados correctamente")
                    passed += 1

            except Exception as e:
                print(f"[ERROR] {case['name']}: {e}")

        print(
            f"\n[CONVERSATION] Persistencia conversación: {passed}/{len(test_cases)} casos correctos ({passed/len(test_cases)*100:.1f}%)")
        return passed / len(test_cases)

    except Exception as e:
        print(f"[ERROR] Error en test de conversación: {e}")
        return 0.0


def main():
    """Ejecutar todos los tests"""
    print("[SEMANTIC] Verificando integración semántica...")

    classifier_score = test_semantic_classifier()
    integration_score = test_memory_service_integration()
    conversation_score = test_conversacion_humana_persistence()

    overall_score = (classifier_score + integration_score +
                     conversation_score) / 3

    print(f"\n[SEMANTIC] RESULTADO FINAL:")
    print(f"   Clasificador semántico: {classifier_score*100:.1f}%")
    print(f"   Integración memory_service: {integration_score*100:.1f}%")
    print(f"   Persistencia conversación: {conversation_score*100:.1f}%")
    print(f"   Puntuación general: {overall_score*100:.1f}%")

    if overall_score >= 0.8:
        print("[OK] Sistema semántico funcionando correctamente")
        return True
    else:
        print("[WARN] Sistema semántico necesita ajustes")
        return False


if __name__ == "__main__":
    exit(0 if main() else 1)
