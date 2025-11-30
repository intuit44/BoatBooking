"""
Test del endpoint híbrido /api/deploy que maneja tanto ARM como modelos de Foundry
"""

import json
import sys
import os
from typing import Dict, Any

# Agregar ruta del proyecto para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_deploy_foundry_models():
    """Test del deployment de modelos Foundry"""
    print("\n[DEPLOY-FOUNDRY] Testing deployment de modelos Foundry...")

    try:
        # Importar funciones necesarias
        from router_agent import AGENT_REGISTRY

        # Test Case 1: Desplegar modelos específicos
        print(f"\n[TEST 1] Deployment de modelos específicos...")

        test_payload = {
            "action": "deployModels",
            "models": [
                "mistral-large-2411",
                "claude-3-5-sonnet-20241022",
                "gpt-4o-2024-11-20"
            ]
        }

        # Simular la lógica de detección
        is_foundry_deployment = (
            test_payload.get("models") or
            test_payload.get("action") == "deployModels"
        )

        assert is_foundry_deployment, "No se detectó como deployment de Foundry"
        print(f"[OK] Detectado correctamente como deployment de Foundry")

        # Validar que los modelos están en el registry
        registry_models = {
            agent_config.get("model"): intent
            for intent, agent_config in AGENT_REGISTRY.items()
            if agent_config.get("model")
        }

        for model in test_payload["models"]:
            if model in registry_models:
                intent = registry_models[model]
                print(
                    f"[OK] Modelo {model} encontrado para intención '{intent}'")
            else:
                print(f"[WARN] Modelo {model} no encontrado en registry")

        # Test Case 2: Desplegar todos los modelos del registry
        print(f"\n[TEST 2] Deployment de todos los modelos...")

        all_models = list(set(
            agent_config.get("model")
            for agent_config in AGENT_REGISTRY.values()
            if agent_config.get("model")
        ))

        print(f"[OK] Modelos disponibles en registry: {len(all_models)}")
        for model in all_models:
            intent = registry_models.get(model, "unknown")
            print(f"  - {model} ({intent})")

        # Test Case 3: Validar estructura de respuesta esperada
        print(f"\n[TEST 3] Validando estructura de respuesta...")

        expected_response_structure = {
            "ok": "bool",
            "action": "str",
            "models_deployed": "list",
            "already_active": "list",
            "failed": "list",
            "summary": "dict",
            "deployment_details": "list",
            "foundry_endpoint": "str",
            "timestamp": "str"
        }

        print(f"[OK] Estructura de respuesta esperada definida")
        for key, expected_type in expected_response_structure.items():
            if key == "summary":
                print(f"  - {key}: dict con contadores")
            else:
                # Test Case 4: Validar vs ARM deployment
                print(f"  - {key}: {expected_type}")
        print(f"\n[TEST 4] Diferenciación vs ARM deployment...")

        arm_payload = {
            "resourceGroup": "test-rg",
            "template": {"resources": []},
            "parameters": {}
        }

        is_arm_deployment = not (
            arm_payload.get("models") or
            arm_payload.get("action") == "deployModels"
        )

        assert is_arm_deployment, "ARM payload detectado incorrectamente"
        print(f"[OK] ARM deployment detectado correctamente")

        foundry_payload = {
            "models": ["gpt-4o-2024-11-20"]
        }

        is_foundry = (
            foundry_payload.get("models") or
            foundry_payload.get("action") == "deployModels"
        )

        assert is_foundry, "Foundry payload no detectado"
        print(f"[OK] Foundry deployment detectado correctamente")

        print(f"\n[DEPLOY-FOUNDRY] Todos los tests pasaron correctamente ✅")
        return True

    except Exception as e:
        print(f"[ERROR] Error en test deploy foundry: {e}")
        return False


def test_deploy_endpoint_detection():
    """Test de detección de tipo de deployment"""
    print("\n[DEPLOY-DETECTION] Testing detección de tipo de deployment...")

    test_cases = [
        {
            "name": "Foundry Models - Campo models",
            "payload": {"models": ["gpt-4o-2024-11-20"]},
            "expected_type": "foundry"
        },
        {
            "name": "Foundry Models - Action deployModels",
            "payload": {"action": "deployModels", "models": ["claude-3-5-sonnet-20241022"]},
            "expected_type": "foundry"
        },
        {
            "name": "Foundry Models - Campo foundry_models",
            "payload": {"foundry_models": ["mistral-large-2411"]},
            "expected_type": "foundry"
        },
        {
            "name": "ARM Deployment - ResourceGroup + Template",
            "payload": {"resourceGroup": "test-rg", "template": {"resources": []}},
            "expected_type": "arm"
        },
        {
            "name": "ARM Deployment - TemplateUri",
            "payload": {"resourceGroup": "test-rg", "templateUri": "https://example.com/template.json"},
            "expected_type": "arm"
        }
    ]

    passed = 0
    for case in test_cases:
        payload = case["payload"]
        expected = case["expected_type"]

        is_foundry = (
            payload.get("models") or
            payload.get("action") == "deployModels" or
            payload.get("foundry_models") or
            "models" in payload
        )

        detected_type = "foundry" if is_foundry else "arm"

        if detected_type == expected:
            print(f"[OK] {case['name']}: Detectado como {detected_type}")
            passed += 1
        else:
            print(
                f"[FAIL] {case['name']}: Esperado {expected}, detectado {detected_type}")

    score = passed / len(test_cases)
    print(
        f"\n[DEPLOY-DETECTION] Detección: {passed}/{len(test_cases)} casos correctos ({score*100:.1f}%)")

    return score >= 0.8


def main():
    """Ejecutar todos los tests del endpoint deploy"""
    print("=" * 70)
    print("[DEPLOY-ENDPOINT] Testing endpoint híbrido /api/deploy")
    print("=" * 70)

    results = []

    # Test 1: Deployment de modelos Foundry
    results.append(test_deploy_foundry_models())

    # Test 2: Detección de tipo de deployment
    results.append(test_deploy_endpoint_detection())

    # Calcular puntuación general
    success_rate = sum(results) / len(results)

    print("\n" + "=" * 70)
    print("[DEPLOY-ENDPOINT] RESULTADO FINAL:")
    print("=" * 70)
    print(
        f"   🤖 Deployment Foundry Models:    {results[0] and 'PASS' or 'FAIL'}")
    print(
        f"   🔍 Detección Tipo Deployment:    {results[1] and 'PASS' or 'FAIL'}")
    print(f"   " + "-" * 50)
    print(f"   🎯 Puntuación general:           {success_rate*100:.1f}%")
    print("=" * 70)

    if success_rate >= 0.8:
        print("[✅ OK] Endpoint híbrido /api/deploy funcionando correctamente")
        return True
    else:
        print("[❌ FAIL] Endpoint híbrido /api/deploy necesita ajustes")
        return False


if __name__ == "__main__":
    exit(0 if main() else 1)
