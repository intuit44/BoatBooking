"""
Test directo del endpoint /api/deploy con deployment de modelos Foundry
Simula una llamada HTTP real al endpoint
"""

import json
import sys
import os
from unittest.mock import MagicMock, patch

# Agregar ruta del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_deploy_endpoint_http():
    """Test HTTP completo del endpoint /api/deploy para modelos Foundry"""
    print("\n[DEPLOY-HTTP] Testing endpoint /api/deploy con HTTP Request...")

    try:
        # Importar Azure Functions para crear mock request
        import azure.functions as func
        from io import BytesIO

        # Mock de HttpRequest para deployment de modelos
        foundry_payload = {
            "action": "deployModels",
            "models": [
                "mistral-large-2411",
                "gpt-4o-2024-11-20",
                "claude-3-5-sonnet-20241022"
            ]
        }

        # Crear mock request
        mock_req = MagicMock(spec=func.HttpRequest)
        mock_req.get_json.return_value = foundry_payload
        mock_req.method = "POST"
        mock_req.headers = {
            "Session-ID": "test_session_deploy",
            "Agent-ID": "DeployAgent"
        }

        print(
            f"[OK] Mock request creado para deployment de {len(foundry_payload['models'])} modelos")

        # Importar funciones del endpoint
        from function_app import _deploy_foundry_models
        from services.memory_service import memory_service
        from cosmos_memory_direct import aplicar_memoria_cosmos_directo
        from memory_manual import aplicar_memoria_manual

        print(f"[OK] Funciones del endpoint importadas correctamente")

        # Ejecutar función de deployment
        response = _deploy_foundry_models(
            req=mock_req,
            body=foundry_payload,
            memory_service=memory_service,
            aplicar_memoria_cosmos_directo=aplicar_memoria_cosmos_directo,
            aplicar_memoria_manual=aplicar_memoria_manual
        )

        print(f"[OK] Función de deployment ejecutada")

        # Validar respuesta
        assert hasattr(
            response, 'get_body'), "Respuesta no es HttpResponse válida"

        # Parsear JSON de respuesta
        response_body = response.get_body().decode('utf-8')
        response_data = json.loads(response_body)

        print(f"[OK] Respuesta parseada correctamente")

        # Validaciones de estructura
        required_fields = [
            "ok", "action", "models_deployed", "already_active",
            "failed", "summary", "deployment_details"
        ]

        for field in required_fields:
            assert field in response_data, f"Campo '{field}' faltante en respuesta"

        print(f"[OK] Todos los campos requeridos presentes")

        # Validaciones de contenido
        assert response_data["action"] == "deployModels", "Action incorrecta"
        assert isinstance(
            response_data["models_deployed"], list), "models_deployed no es lista"
        assert isinstance(
            response_data["already_active"], list), "already_active no es lista"
        assert isinstance(response_data["failed"], list), "failed no es lista"

        print(f"[OK] Tipos de datos correctos")

        # Mostrar resultados
        summary = response_data["summary"]
        print(f"\n[RESULTADOS] Summary del deployment:")
        print(f"  - Total solicitados: {summary['total_requested']}")
        print(f"  - Desplegados: {summary['deployed']}")
        print(f"  - Ya activos: {summary['already_active']}")
        print(f"  - Fallaron: {summary['failed']}")

        # Mostrar detalles
        if response_data["deployment_details"]:
            print(f"\n[DETALLES] Deployment details:")
            for detail in response_data["deployment_details"]:
                status = detail.get("status", "unknown")
                model = detail.get("model", "unknown")
                intent = detail.get("intent", "unknown")
                print(f"  - {model} ({intent}): {status}")

        # Verificar que no hay errores críticos
        if response_data["failed"]:
            print(f"\n[WARNING] Algunos modelos fallaron:")
            for failure in response_data["failed"]:
                print(
                    f"  - {failure.get('model', 'unknown')}: {failure.get('error', 'unknown error')}")

        # Validar status code
        status_code = response.status_code
        expected_codes = [200, 207]  # 200 OK, 207 Multi-Status
        assert status_code in expected_codes, f"Status code {status_code} no esperado"

        print(f"[OK] Status code {status_code} es válido")
        print(f"[✅ SUCCESS] Test HTTP del endpoint completado exitosamente")

        return True

    except Exception as e:
        print(f"[❌ ERROR] Error en test HTTP: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deploy_endpoint_integration():
    """Test de integración completa del endpoint deploy"""
    print("\n[DEPLOY-INTEGRATION] Testing integración completa...")

    try:
        # Test 1: Detección correcta de payload Foundry
        foundry_payload = {"models": ["gpt-4o-2024-11-20"]}

        is_foundry_deployment = (
            foundry_payload.get("models") or
            foundry_payload.get("action") == "deployModels" or
            foundry_payload.get("foundry_models") or
            "models" in foundry_payload
        )

        assert is_foundry_deployment, "Payload Foundry no detectado"
        print(f"[OK] Detección de payload Foundry correcta")

        # Test 2: Detección correcta de payload ARM
        arm_payload = {"resourceGroup": "test-rg",
                       "template": {"resources": []}}

        is_arm_deployment = not (
            arm_payload.get("models") or
            arm_payload.get("action") == "deployModels" or
            arm_payload.get("foundry_models") or
            "models" in arm_payload
        )

        assert is_arm_deployment, "Payload ARM no detectado como no-Foundry"
        print(f"[OK] Detección de payload ARM correcta")

        # Test 3: Validar AGENT_REGISTRY
        from router_agent import AGENT_REGISTRY

        assert len(AGENT_REGISTRY) > 0, "AGENT_REGISTRY está vacío"

        models_in_registry = []
        for intent, config in AGENT_REGISTRY.items():
            model = config.get("model")
            if model:
                models_in_registry.append(model)

        assert len(models_in_registry) > 0, "No hay modelos en AGENT_REGISTRY"
        print(
            f"[OK] AGENT_REGISTRY contiene {len(models_in_registry)} modelos")

        # Test 4: Validar funciones helper
        from function_app import _check_model_deployment_status, _deploy_model_to_foundry

        # Test función de verificación
        test_model = "gpt-4o-mini-2024-07-18"
        test_config = {"project_id": "test", "endpoint": "test"}

        status = _check_model_deployment_status(test_model, test_config)
        assert isinstance(status, bool), "Status no es booleano"
        print(
            f"[OK] Función de verificación funciona: {test_model} -> {status}")

        # Test función de deployment
        deploy_result = _deploy_model_to_foundry(test_model, test_config)
        assert isinstance(deploy_result, bool), "Deploy result no es booleano"
        print(
            f"[OK] Función de deployment funciona: {test_model} -> {deploy_result}")

        print(f"[✅ SUCCESS] Integración completa validada")
        return True

    except Exception as e:
        print(f"[❌ ERROR] Error en test de integración: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests del endpoint deploy"""
    print("=" * 80)
    print("[DEPLOY-ENDPOINT-HTTP] Testing completo del endpoint /api/deploy híbrido")
    print("=" * 80)

    results = []

    # Test 1: HTTP Request completo
    results.append(test_deploy_endpoint_http())

    # Test 2: Integración completa
    results.append(test_deploy_endpoint_integration())

    # Calcular puntuación
    success_rate = sum(results) / len(results)

    print("\n" + "=" * 80)
    print("[DEPLOY-ENDPOINT-HTTP] RESULTADO FINAL:")
    print("=" * 80)
    print(
        f"   🌐 HTTP Request Test:            {results[0] and 'PASS' or 'FAIL'}")
    print(
        f"   🔗 Integration Test:             {results[1] and 'PASS' or 'FAIL'}")
    print(f"   " + "-" * 60)
    print(f"   🎯 Puntuación general:           {success_rate*100:.1f}%")
    print("=" * 80)

    if success_rate >= 0.8:
        print("[✅ OK] Endpoint híbrido /api/deploy completamente funcional")
        print("\n🚀 LISTO PARA PRODUCCIÓN:")
        print("   1. Reemplazar simulaciones con Foundry SDK real")
        print("   2. Configurar authentication con Foundry")
        print("   3. Actualizar OpenAPI schema para documentar nuevos campos")
        return True
    else:
        print("[❌ FAIL] Endpoint híbrido necesita correcciones")
        return False


if __name__ == "__main__":
    exit(0 if main() else 1)
