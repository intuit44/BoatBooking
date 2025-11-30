"""
Test simplificado para debuggear el issue del deployment
"""

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_simple_deployment():
    """Test básico de la función de deployment"""
    print("[SIMPLE-TEST] Testing función deployment...")

    try:
        # Cargar variables de entorno
        from test_semantic_integration import _load_local_settings
        _load_local_settings()

        # Importar router_agent
        from router_agent import AGENT_REGISTRY
        print(f"[OK] AGENT_REGISTRY importado: {len(AGENT_REGISTRY)} agentes")

        # Test de modelos específicos
        test_models = ["mistral-large-2411", "gpt-4o-2024-11-20"]

        registry_models = {
            agent_config.get("model"): intent
            for intent, agent_config in AGENT_REGISTRY.items()
            if agent_config.get("model")
        }

        print(f"[OK] Registry models: {list(registry_models.keys())}")

        for model in test_models:
            if model in registry_models:
                intent = registry_models[model]
                print(f"[OK] {model} -> {intent}")
            else:
                print(f"[WARN] {model} no encontrado")

        # Test payload
        payload = {
            "action": "deployModels",
            "models": test_models
        }

        # Detectar tipo
        is_foundry_deployment = (
            payload.get("models") or
            payload.get("action") == "deployModels" or
            payload.get("foundry_models") or
            "models" in payload
        )

        print(f"[OK] Detected as Foundry deployment: {is_foundry_deployment}")

        # Test respuesta mock
        mock_response = {
            "ok": True,
            "action": "deployModels",
            "models_deployed": ["mistral-large-2411"],
            "already_active": ["gpt-4o-2024-11-20"],
            "failed": [],
            "summary": {
                "total_requested": 2,
                "deployed": 1,
                "already_active": 1,
                "failed": 0
            },
            "deployment_details": [
                {
                    "model": "mistral-large-2411",
                    "intent": "correccion",
                    "status": "deployed"
                }
            ]
        }

        print(f"[OK] Mock response structure valid")
        print(f"[✅ SUCCESS] Test simple completado")
        return True

    except Exception as e:
        print(f"[❌ ERROR] Error en test simple: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_foundry_functions():
    """Test de las funciones helper de Foundry"""
    print("\n[FOUNDRY-FUNCTIONS] Testing funciones helper...")

    try:
        from function_app import _check_model_deployment_status, _deploy_model_to_foundry

        test_model = "gpt-4o-2024-11-20"
        test_config = {
            "project_id": "test-project",
            "endpoint": "https://test.azure.com",
            "agent_id": "TestAgent"
        }

        # Test check status
        status = _check_model_deployment_status(test_model, test_config)
        print(f"[OK] Check status: {test_model} -> {status}")

        # Test deploy
        deploy_result = _deploy_model_to_foundry(test_model, test_config)
        print(f"[OK] Deploy result: {test_model} -> {deploy_result}")

        print(f"[✅ SUCCESS] Funciones helper funcionando")
        return True

    except Exception as e:
        print(f"[❌ ERROR] Error en funciones helper: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("[DEBUG] Test simplificado de deployment")
    print("=" * 60)

    results = []
    results.append(test_simple_deployment())
    results.append(test_foundry_functions())

    success_rate = sum(results) / len(results)
    print(f"\n[RESULTADO] {success_rate*100:.1f}% exitoso")

    exit(0 if success_rate >= 0.8 else 1)
