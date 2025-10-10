# test_agent898_simulator.py
import requests
import json
import yaml
import time
from typing import Dict, List, Any
from urllib.parse import urljoin

class Agent898Simulator:
    """Simula exactamente cómo AI Foundry Agent898 interactúa con la Function App"""
    
    def __init__(self, base_url: str = "https://copiloto-func.ngrok.app"):
        self.base_url = base_url
        self.openapi_schema = None
        self.available_operations = {}
        self.test_results = []
        
    def simulate_agent_discovery(self):
        """Simula cómo Agent898 descubre y valida el OpenAPI"""
        print("🤖 SIMULANDO AGENT898 - DESCUBRIMIENTO DE API")
        print("=" * 60)
        
        # 1. Agent898 intenta obtener el schema OpenAPI
        schema_result = self._fetch_openapi_schema()
        if not schema_result['success']:
            return False
            
        # 2. Agent898 valida la versión OpenAPI
        version_result = self._validate_openapi_version()
        if not version_result['success']:
            return False
            
        # 3. Agent898 parsea las operaciones disponibles
        operations_result = self._parse_available_operations()
        if not operations_result['success']:
            return False
            
        print(f"✅ Descubrimiento exitoso: {len(self.available_operations)} operaciones encontradas")
        return True
        
    def _fetch_openapi_schema(self):
        """Simula Agent898 obteniendo el schema OpenAPI"""
        try:
            print("📥 Obteniendo schema OpenAPI...")
            
            # Agent898 siempre busca primero /api/openapi.yaml
            schema_url = f"{self.base_url}/api/openapi.yaml"
            response = requests.get(schema_url, timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"OpenAPI schema not available: HTTP {response.status_code}",
                    'details': response.text[:200]
                }
                
            # Determinar si es JSON o YAML
            try:
                if response.text.strip().startswith('{'):
                    self.openapi_schema = json.loads(response.text)
                else:
                    self.openapi_schema = yaml.safe_load(response.text)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Invalid OpenAPI format: {str(e)}"
                }
                
            print(f"✅ Schema obtenido: {response.headers.get('content-type', 'unknown')} format")
            return {'success': True, 'schema_size': len(response.text)}
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
    
    def _validate_openapi_version(self):
        """Valida que la versión sea 3.1.x (requerimiento Agent898)"""
        try:
            openapi_version = self.openapi_schema.get('openapi')
            
            if not openapi_version:
                return {
                    'success': False,
                    'error': "No 'openapi' field found in schema"
                }
                
            # Agent898 requiere específicamente 3.1.x
            if not openapi_version.startswith('3.1.'):
                return {
                    'success': False,
                    'error': f"Invalid OpenAPI version: {openapi_version}. Agent898 requires 3.1.x",
                    'found_version': openapi_version
                }
                
            print(f"✅ Versión OpenAPI válida: {openapi_version}")
            return {'success': True, 'version': openapi_version}
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Version validation error: {str(e)}"
            }
    
    def _parse_available_operations(self):
        """Parsea las operaciones disponibles desde el schema OpenAPI"""
        try:
            paths = self.openapi_schema.get('paths', {})
            
            for path, methods in paths.items():
                for method, operation in methods.items():
                    if isinstance(operation, dict) and 'operationId' in operation:
                        operation_id = operation['operationId']
                        
                        self.available_operations[operation_id] = {
                            'path': path,
                            'method': method.upper(),
                            'summary': operation.get('summary', ''),
                            'description': operation.get('description', ''),
                            'parameters': operation.get('parameters', []),
                            'requestBody': operation.get('requestBody'),
                            'responses': operation.get('responses', {})
                        }
                        
            print(f"✅ Operaciones parseadas: {len(self.available_operations)}")
            
            # Mostrar operaciones críticas
            critical_ops = [
                'getStatus', 'healthCheck', 'ejecutarCli', 'leerArchivo', 
                'escribirArchivo', 'listarBlobs', 'crearContenedor'
            ]
            
            found_critical = [op for op in critical_ops if op in self.available_operations]
            missing_critical = [op for op in critical_ops if op not in self.available_operations]
            
            if missing_critical:
                print(f"⚠️ Operaciones críticas faltantes: {missing_critical}")
            else:
                print("✅ Todas las operaciones críticas disponibles")
                
            return {
                'success': True,
                'total_operations': len(self.available_operations),
                'critical_found': found_critical,
                'critical_missing': missing_critical
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Operations parsing error: {str(e)}"
            }
    
    def simulate_agent_operations(self):
        """Simula Agent898 ejecutando operaciones típicas"""
        print("\n🔧 SIMULANDO OPERACIONES DE AGENT898")
        print("=" * 60)
        
        operations_to_test = [
            # Operaciones básicas de descubrimiento
            {
                'name': 'Health Check',
                'operation_id': 'healthCheck',
                'expected_status': 200
            },
            {
                'name': 'System Status',
                'operation_id': 'getStatus', 
                'expected_status': 200
            },
            
            # Operaciones de archivos (típicas de Agent898)
            {
                'name': 'Read README',
                'operation_id': 'leerArchivo',
                'params': {'ruta': 'README.md'},
                'expected_status': 200
            },
            {
                'name': 'List Project Files',
                'operation_id': 'listarBlobs',
                'expected_status': 200
            },
            
            # Operaciones de Azure CLI (core functionality)
            {
                'name': 'Azure CLI - List Storage',
                'operation_id': 'ejecutarCli',
                'body': {'comando': 'storage account list --query "[].name"'},
                'expected_status': 200
            },
            {
                'name': 'Azure CLI - Resource Groups',
                'operation_id': 'ejecutarCli',
                'body': {'comando': 'group list --query "[].name"'},
                'expected_status': 200
            },
            
            # Operaciones híbridas (Agent898 específicas)
            {
                'name': 'Hybrid Processing',
                'operation_id': 'processHybrid',
                'body': {'agent_response': 'test from Agent898 simulator'},
                'expected_status': 200
            }
        ]
        
        results = []
        
        for operation in operations_to_test:
            result = self._execute_operation(operation)
            results.append(result)
            
            # Agent898 típicamente espera entre requests
            time.sleep(1)
            
        return results
    
    def _execute_operation(self, operation_config):
        """Ejecuta una operación específica simulando Agent898"""
        operation_id = operation_config['operation_id']
        
        if operation_id not in self.available_operations:
            return {
                'name': operation_config['name'],
                'success': False,
                'error': f"Operation {operation_id} not found in OpenAPI schema"
            }
            
        op_def = self.available_operations[operation_id]
        url = urljoin(self.base_url, op_def['path'])
        method = op_def['method']
        
        try:
            # Preparar request según el método
            if method == 'GET':
                params = operation_config.get('params', {})
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                body = operation_config.get('body', {})
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=body, headers=headers, timeout=30)
            else:
                return {
                    'name': operation_config['name'],
                    'success': False,
                    'error': f"Method {method} not supported in simulator"
                }
                
            success = response.status_code == operation_config['expected_status']
            
            result = {
                'name': operation_config['name'],
                'operation_id': operation_id,
                'success': success,
                'status_code': response.status_code,
                'expected_status': operation_config['expected_status'],
                'response_size': len(response.text),
                'response_preview': response.text[:100] if response.text else None
            }
            
            # Output en tiempo real
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {operation_config['name']}: {response.status_code}")
            
            if not success:
                print(f"   Expected: {operation_config['expected_status']}, Got: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:200]}")
                    
            return result
            
        except Exception as e:
            result = {
                'name': operation_config['name'], 
                'operation_id': operation_id,
                'success': False,
                'error': str(e)
            }
            
            print(f"❌ {operation_config['name']}: Exception - {str(e)}")
            return result
    
    def generate_compatibility_report(self, results):
        """Genera reporte de compatibilidad Agent898"""
        print("\n📊 REPORTE DE COMPATIBILIDAD AGENT898")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        compatibility_score = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Pruebas totales: {total_tests}")
        print(f"Pruebas exitosas: {successful_tests}")
        print(f"Puntuación de compatibilidad: {compatibility_score:.1f}%")
        
        # Clasificar nivel de compatibilidad
        if compatibility_score >= 90:
            compat_level = "🟢 EXCELENTE"
        elif compatibility_score >= 75:
            compat_level = "🟡 BUENA"
        elif compatibility_score >= 50:
            compat_level = "🟠 REGULAR"
        else:
            compat_level = "🔴 CRÍTICA"
            
        print(f"Nivel de compatibilidad: {compat_level}")
        
        # Mostrar fallos críticos
        failed_tests = [r for r in results if not r['success']]
        if failed_tests:
            print("\n❌ Operaciones fallidas:")
            for test in failed_tests:
                print(f"   • {test['name']}: {test.get('error', 'Unknown error')}")
                
        # Recomendaciones
        print(f"\n💡 Recomendaciones:")
        if compatibility_score >= 90:
            print("   ✅ Function App lista para Agent898")
            print("   ✅ Proceder con despliegue usando fix_functionapp_final.ps1")
        elif compatibility_score >= 75:
            print("   ⚠️ Corregir operaciones fallidas antes del despliegue")
            print("   ⚠️ Revisar logs de las operaciones que fallan")
        else:
            print("   🚨 NO desplegar todavía - múltiples problemas críticos")
            print("   🚨 Revisar configuración y endpoints faltantes")
            
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests, 
            'compatibility_score': compatibility_score,
            'compatibility_level': compat_level,
            'failed_tests': failed_tests,
            'ready_for_deployment': compatibility_score >= 75
        }

def main():
    """Ejecuta la simulación completa de Agent898"""
    simulator = Agent898Simulator("https://copiloto-func.ngrok.app")
    
    print("🚀 INICIANDO SIMULACIÓN COMPLETA DE AGENT898")
    print("=" * 60)
    print("Base URL:", simulator.base_url)
    print("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Fase 1: Descubrimiento
    discovery_success = simulator.simulate_agent_discovery()
    if not discovery_success:
        print("\n🚨 FALLO EN DESCUBRIMIENTO - Simulación abortada")
        return False
        
    # Fase 2: Ejecución de operaciones
    results = simulator.simulate_agent_operations()
    
    # Fase 3: Reporte final
    report = simulator.generate_compatibility_report(results)
    
    return report['ready_for_deployment']

if __name__ == "__main__":
    ready = main()
    exit(0 if ready else 1)