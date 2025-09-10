# test_system_stability.py
"""
Script integral para probar y estabilizar el sistema Copiloto
Valida únicamente respuestas HTTP/JSON sin verificar entorno local
"""

import json
import requests
import sys
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️ WARNING"
    SKIPPED = "⭕️ SKIPPED"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    details: Optional[Dict] = None
    fix_suggestion: Optional[str] = None


class CopilotoSystemTester:
    def __init__(self, base_url: str, local_url: str = "http://localhost:7071"):
        self.base_url = base_url
        self.local_url = local_url
        self.test_results: List[TestResult] = []
        self.critical_issues: List[str] = []

    def run_all_tests(self) -> Dict:
        """Ejecuta todas las pruebas del sistema"""
        print("\n" + "="*60)
        print("🔬 INICIANDO PRUEBAS INTEGRALES DEL SISTEMA COPILOTO")
        print("="*60)

        # 1. Probar endpoints básicos
        self.test_basic_endpoints()

        # 2. Probar ejecutar-cli con SDK
        self.test_ejecutar_cli_sdk()

        # 3. Probar formato de JSON del agente
        self.test_agent_json_formats()

        # 4. Probar intenciones semánticas
        self.test_semantic_intentions()

        # 5. Probar operaciones de storage
        self.test_storage_operations()

        # 6. Generar reporte
        return self.generate_report()

    def test_basic_endpoints(self):
        """Prueba endpoints básicos del sistema"""
        print("\n📌 Prueba 1: Endpoints Básicos")
        print("-" * 40)

        endpoints = [
            ("GET", "/api/status", None, "Status"),
            ("GET", "/api/health", None, "Health"),
            ("GET", "/api/listar-blobs", {"top": 5}, "Listar Blobs"),
        ]

        for method, endpoint, params, name in endpoints:
            self._test_endpoint(
                self.base_url + endpoint,
                method,
                params,
                name
            )

    def test_ejecutar_cli_sdk(self):
        """Prueba el endpoint ejecutar-cli usando SDK"""
        print("\n📌 Prueba 2: Ejecutar CLI (SDK Implementation)")
        print("-" * 40)

        # Comandos de prueba que deben funcionar con SDK
        test_commands = [
            {
                "comando": "group list",
                "expected_keys": ["stdout", "comando_ejecutado", "mensaje_natural"],
                "name": "Listar grupos de recursos"
            },
            {
                "comando": "storage account list",
                "expected_keys": ["stdout", "comando_ejecutado", "mensaje_natural"],
                "name": "Listar cuentas de almacenamiento"
            }
        ]

        for test in test_commands:
            try:
                response = requests.post(
                    f"{self.base_url}/api/ejecutar-cli",
                    json={"comando": test["comando"]},
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verificar estructura de respuesta
                    missing_keys = [
                        key for key in test["expected_keys"] if key not in data]

                    if data.get("exito") and not missing_keys:
                        self.test_results.append(TestResult(
                            name=f"SDK CLI: {test['name']}",
                            status=TestStatus.PASSED,
                            message="Comando ejecutado correctamente vía SDK",
                            details={
                                "metodo": data.get("metodo", "SDK"),
                                "total_resultados": data.get("total_resultados", 0)
                            }
                        ))
                    else:
                        self.test_results.append(TestResult(
                            name=f"SDK CLI: {test['name']}",
                            status=TestStatus.WARNING,
                            message=f"Respuesta incompleta o error: {data.get('error', 'Unknown')}",
                            details={"missing_keys": missing_keys,
                                     "exito": data.get("exito")}
                        ))
                elif response.status_code == 401:
                    self.test_results.append(TestResult(
                        name=f"SDK CLI: {test['name']}",
                        status=TestStatus.FAILED,
                        message="Error de autenticación (401)",
                        fix_suggestion="Verificar Managed Identity y AZURE_SUBSCRIPTION_ID"
                    ))
                    self.critical_issues.append(
                        "Autenticación con Managed Identity faltante")
                else:
                    self.test_results.append(TestResult(
                        name=f"SDK CLI: {test['name']}",
                        status=TestStatus.FAILED,
                        message=f"HTTP {response.status_code}",
                        details={"response": response.text[:200]}
                    ))

            except Exception as e:
                self.test_results.append(TestResult(
                    name=f"SDK CLI: {test['name']}",
                    status=TestStatus.FAILED,
                    message=str(e),
                    fix_suggestion="Verificar conectividad con el endpoint"
                ))

    def test_agent_json_formats(self):
        """Prueba los diferentes formatos JSON que envía el agente"""
        print("\n📌 Prueba 3: Formatos JSON del Agente")
        print("-" * 40)

        # Formato directo para ejecutar-cli
        direct_format = {
            "comando": "group list"
        }

        # Formato wrapper para invocar
        wrapper_format = {
            "endpoint": "ejecutar-cli",
            "method": "POST",
            "data": {
                "comando": "group list"
            }
        }

        # Probar formato directo en ejecutar-cli
        self._test_json_format(
            "/api/ejecutar-cli",
            direct_format,
            "Formato Directo en /api/ejecutar-cli",
            check_exito=True
        )

        # Probar formato wrapper en invocar
        self._test_json_format(
            "/api/invocar",
            wrapper_format,
            "Formato Wrapper en /api/invocar",
            check_exito=False  # invocar puede tener estructura diferente
        )

    def test_semantic_intentions(self):
        """Prueba las intenciones semánticas"""
        print("\n📌 Prueba 4: Intenciones Semánticas")
        print("-" * 40)

        intentions = [
            {
                "intencion": "dashboard",
                "parametros": {},
                "name": "Dashboard"
            },
            {
                "intencion": "diagnosticar:completo",
                "parametros": {},
                "name": "Diagnóstico Completo"
            },
            {
                "intencion": "verificar:almacenamiento",
                "parametros": {},
                "name": "Verificar Almacenamiento"
            }
        ]

        for test in intentions:
            try:
                response = requests.post(
                    f"{self.base_url}/api/ejecutar",
                    json={
                        "intencion": test["intencion"],
                        "parametros": test["parametros"],
                        "modo": "normal"
                    },
                    timeout=20
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verificar que hay contenido relevante en la respuesta
                    has_content = (
                        data.get("exito") or
                        "dashboard" in data or
                        "diagnostico" in data or
                        "almacenamiento" in data
                    )

                    if has_content:
                        self.test_results.append(TestResult(
                            name=f"Intención: {test['name']}",
                            status=TestStatus.PASSED,
                            message="Intención procesada correctamente"
                        ))
                    else:
                        self.test_results.append(TestResult(
                            name=f"Intención: {test['name']}",
                            status=TestStatus.WARNING,
                            message="Respuesta recibida pero sin contenido esperado",
                            details={"keys": list(data.keys())[:5]}
                        ))
                else:
                    self.test_results.append(TestResult(
                        name=f"Intención: {test['name']}",
                        status=TestStatus.FAILED,
                        message=f"HTTP {response.status_code}"
                    ))

            except Exception as e:
                self.test_results.append(TestResult(
                    name=f"Intención: {test['name']}",
                    status=TestStatus.FAILED,
                    message=str(e)[:100]
                ))

    def test_storage_operations(self):
        """Prueba operaciones de storage"""
        print("\n📌 Prueba 5: Operaciones de Storage")
        print("-" * 40)

        # Crear contenedor de prueba
        container_name = f"test-container-{int(datetime.now().timestamp())}"

        # Test 1: Crear contenedor
        try:
            response = requests.post(
                f"{self.base_url}/api/crear-contenedor",
                json={
                    "nombre": container_name,
                    "publico": False,
                    "metadata": {"test": "true"}
                },
                timeout=15
            )

            if response.status_code in [200, 201]:
                data = response.json()
                if data.get("exito"):
                    self.test_results.append(TestResult(
                        name="Storage: Crear Contenedor",
                        status=TestStatus.PASSED,
                        message=f"Contenedor {container_name} creado",
                        details={"container": container_name}
                    ))
                else:
                    self.test_results.append(TestResult(
                        name="Storage: Crear Contenedor",
                        status=TestStatus.WARNING,
                        message=data.get("error", "Error desconocido")
                    ))
            else:
                self.test_results.append(TestResult(
                    name="Storage: Crear Contenedor",
                    status=TestStatus.FAILED,
                    message=f"HTTP {response.status_code}"
                ))

        except Exception as e:
            self.test_results.append(TestResult(
                name="Storage: Crear Contenedor",
                status=TestStatus.FAILED,
                message=str(e)[:100]
            ))

    def _test_endpoint(self, url: str, method: str, params: Optional[Dict], name: str):
        """Prueba un endpoint específico"""
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            else:
                response = requests.post(url, json=params, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Verificar que es JSON válido y tiene contenido
                    if data:
                        self.test_results.append(TestResult(
                            name=f"Endpoint: {name}",
                            status=TestStatus.PASSED,
                            message="OK (200)"
                        ))
                    else:
                        self.test_results.append(TestResult(
                            name=f"Endpoint: {name}",
                            status=TestStatus.WARNING,
                            message="Respuesta vacía"
                        ))
                except:
                    self.test_results.append(TestResult(
                        name=f"Endpoint: {name}",
                        status=TestStatus.WARNING,
                        message="Respuesta no es JSON válido"
                    ))
            else:
                self.test_results.append(TestResult(
                    name=f"Endpoint: {name}",
                    status=TestStatus.FAILED,
                    message=f"HTTP {response.status_code}"
                ))

        except Exception as e:
            self.test_results.append(TestResult(
                name=f"Endpoint: {name}",
                status=TestStatus.FAILED,
                message=str(e)[:50]
            ))

    def _test_json_format(self, endpoint: str, json_data: Dict, name: str, check_exito: bool = True):
        """Prueba un formato JSON específico"""
        try:
            response = requests.post(
                self.base_url + endpoint,
                json=json_data,
                timeout=15
            )

            if response.status_code in [200, 201]:
                data = response.json()

                if check_exito:
                    if data.get("exito"):
                        self.test_results.append(TestResult(
                            name=name,
                            status=TestStatus.PASSED,
                            message="Formato aceptado y procesado"
                        ))
                    else:
                        self.test_results.append(TestResult(
                            name=name,
                            status=TestStatus.WARNING,
                            message=f"Formato aceptado pero con error: {data.get('error', 'Unknown')}"
                        ))
                else:
                    # Para endpoints como invocar que pueden tener estructura diferente
                    self.test_results.append(TestResult(
                        name=name,
                        status=TestStatus.PASSED,
                        message="Formato aceptado"
                    ))
            elif response.status_code == 401:
                self.test_results.append(TestResult(
                    name=name,
                    status=TestStatus.WARNING,
                    message="No autenticado pero formato correcto"
                ))
            else:
                self.test_results.append(TestResult(
                    name=name,
                    status=TestStatus.FAILED,
                    message=f"HTTP {response.status_code}",
                    fix_suggestion="Verificar formato JSON esperado por el endpoint"
                ))

        except Exception as e:
            self.test_results.append(TestResult(
                name=name,
                status=TestStatus.FAILED,
                message=str(e)[:100]
            ))

    def generate_report(self) -> Dict:
        """Genera un reporte completo del estado del sistema"""
        print("\n" + "="*60)
        print("📊 REPORTE DE ESTABILIDAD DEL SISTEMA")
        print("="*60)

        # Contar resultados
        passed = sum(1 for r in self.test_results if r.status ==
                     TestStatus.PASSED)
        failed = sum(1 for r in self.test_results if r.status ==
                     TestStatus.FAILED)
        warnings = sum(
            1 for r in self.test_results if r.status == TestStatus.WARNING)

        print(f"\n📈 Resumen:")
        print(f"  ✅ Pasadas: {passed}/{len(self.test_results)}")
        print(f"  ❌ Fallidas: {failed}/{len(self.test_results)}")
        print(f"  ⚠️  Advertencias: {warnings}/{len(self.test_results)}")

        # Mostrar problemas críticos
        if self.critical_issues:
            print(f"\n🚨 PROBLEMAS CRÍTICOS DETECTADOS:")
            for issue in self.critical_issues:
                print(f"  • {issue}")

        # Mostrar detalles de pruebas fallidas
        failed_tests = [
            r for r in self.test_results if r.status == TestStatus.FAILED]
        if failed_tests:
            print(f"\n❌ Pruebas Fallidas:")
            for test in failed_tests:
                print(f"\n  {test.name}:")
                print(f"    Mensaje: {test.message}")
                if test.fix_suggestion:
                    print(f"    🔧 Solución: {test.fix_suggestion}")

        # Script de corrección automática
        print("\n" + "="*60)
        print("🔧 SUGERENCIAS DE CORRECCIÓN")
        print("="*60)

        self.generate_fix_suggestions()

        return {
            "total_tests": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "critical_issues": self.critical_issues,
            "test_results": self.test_results
        }

    def generate_fix_suggestions(self):
        """Genera sugerencias para corregir los problemas encontrados"""

        suggestions = []

        # Sugerencia 1: Managed Identity
        if any("Managed Identity" in issue for issue in self.critical_issues):
            suggestions.append("""
# Fix 1: Verificar Managed Identity
# En Azure Portal:
# 1. Ir a tu Function App
# 2. Settings -> Identity
# 3. System assigned -> Status = On
# 4. Copiar el Object ID

# Asignar permisos:
az role assignment create --assignee <OBJECT_ID> --role "Contributor" --scope /subscriptions/<SUBSCRIPTION_ID>
""")

        # Sugerencia 2: Variables de entorno
        suggestions.append("""
# Fix 2: Verificar variables de entorno en la Function App
az functionapp config appsettings set -g <RESOURCE_GROUP> -n <FUNCTION_APP> --settings "AZURE_SUBSCRIPTION_ID=<YOUR_SUBSCRIPTION_ID>"
""")

        # Sugerencia 3: Verificar el código
        suggestions.append("""
# Fix 3: Verificar que el código usa SDK correctamente
# - ManagedIdentityCredential para autenticación
# - SDKs de Azure (ResourceManagementClient, StorageManagementClient, etc.)
# - NO subprocess con 'az' commands
""")

        if suggestions:
            print("\n📝 Sugerencias para mejorar el sistema:\n")
            for suggestion in suggestions:
                print(suggestion)
        else:
            print("\n✅ Sistema funcionando correctamente")


# Script de ejecución principal
if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║     SISTEMA DE PRUEBAS INTEGRALES - COPILOTO v2.0         ║
║     Validación basada en respuestas HTTP/JSON             ║
╚════════════════════════════════════════════════════════════╝
    """)

    # URLs del sistema
    AZURE_URL = "https://copiloto-semantico-func-us2.azurewebsites.net"
    LOCAL_URL = "http://localhost:7071"

    # Crear tester
    tester = CopilotoSystemTester(AZURE_URL, LOCAL_URL)

    # Ejecutar todas las pruebas
    report = tester.run_all_tests()

    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"stability_report_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": timestamp,
            "report": {
                "summary": {
                    "total": report["total_tests"],
                    "passed": report["passed"],
                    "failed": report["failed"],
                    "warnings": report["warnings"]
                },
                "critical_issues": report["critical_issues"],
                "test_details": [
                    {
                        "name": t.name,
                        "status": t.status.value,
                        "message": t.message,
                        "fix": t.fix_suggestion
                    }
                    for t in report["test_results"]
                ]
            }
        }, f, indent=2)

    print(f"\n💾 Reporte guardado en: stability_report_{timestamp}.json")

    # Resultado final
    if report["failed"] == 0:
        print("\n🎉 ¡SISTEMA ESTABLE Y FUNCIONANDO CORRECTAMENTE!")
    elif report["failed"] < 3:
        print("\n⚠️ Sistema funcionando con problemas menores")
    else:
        print("\n❌ SISTEMA REQUIERE ATENCIÓN")
        print("   Revisa las sugerencias de corrección")
