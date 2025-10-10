#!/usr/bin/env python3
"""
Script para simular cómo Agent898 valida y usa el schema OpenAPI
"""
import json
import re
import requests
import sys

def validate_openapi_version(openapi_version):
    """Valida que la versión OpenAPI cumpla con el patrón de Agent898"""
    pattern = r"^3\.1\.\d+(-.+)?$"
    return re.match(pattern, openapi_version) is not None

def test_schema_access():
    """Prueba acceso al schema desde ambas rutas"""
    base_url = "https://copiloto-semantico-func-us2.azurewebsites.net"
    
    # Probar ambas rutas
    routes = ["/openapi.yaml", "/api/openapi.yaml"]
    
    for route in routes:
        print(f"\n🔍 Probando ruta: {route}")
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Intentar parsear como JSON (aunque sea YAML)
                try:
                    content = response.text
                    if content.startswith('{'):
                        # Es JSON
                        schema = json.loads(content)
                        openapi_version = schema.get("openapi", "unknown")
                        print(f"   OpenAPI Version: {openapi_version}")
                        
                        # Validar versión
                        if validate_openapi_version(openapi_version):
                            print(f"   ✅ Versión válida para Agent898")
                            
                            # Contar endpoints
                            paths = schema.get("paths", {})
                            print(f"   📊 Endpoints disponibles: {len(paths)}")
                            
                            # Mostrar algunos endpoints
                            print(f"   🔗 Primeros 5 endpoints:")
                            for i, path in enumerate(list(paths.keys())[:5]):
                                methods = list(paths[path].keys())
                                print(f"      {i+1}. {path} ({', '.join(methods)})")
                                
                            return True, schema
                        else:
                            print(f"   ❌ Versión inválida para Agent898")
                            print(f"   📋 Patrón requerido: ^3\\.1\\.\\d+(-.+)?$")
                    else:
                        print(f"   📄 Contenido YAML detectado (primeros 200 chars):")
                        print(f"   {content[:200]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error parseando contenido: {e}")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Error de conexión: {e}")
    
    return False, None

def test_endpoint_call(schema):
    """Prueba llamar a un endpoint usando el schema"""
    if not schema:
        print("\n❌ No hay schema para probar endpoints")
        return
        
    print(f"\n🚀 Probando llamada a endpoint...")
    
    # Buscar un endpoint simple para probar
    paths = schema.get("paths", {})
    
    # Probar /api/status
    if "/api/status" in paths:
        try:
            response = requests.get("https://copiloto-semantico-func-us2.azurewebsites.net/api/status", timeout=10)
            print(f"   /api/status -> {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Respuesta exitosa:")
                print(f"      - Copiloto: {data.get('copiloto', 'unknown')}")
                print(f"      - Ambiente: {data.get('ambiente', 'unknown')}")
                print(f"      - Ready: {data.get('ready', False)}")
                return True
            else:
                print(f"   ❌ Error en endpoint: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Error llamando endpoint: {e}")
    
    return False

def main():
    print("🤖 Simulando validación de Agent898 para OpenAPI Schema")
    print("=" * 60)
    
    # Paso 1: Validar acceso al schema
    success, schema = test_schema_access()
    
    if success:
        print(f"\n✅ Schema accesible y válido para Agent898")
        
        # Paso 2: Probar endpoint
        endpoint_success = test_endpoint_call(schema)
        
        if endpoint_success:
            print(f"\n🎉 ¡Agent898 debería poder conectarse correctamente!")
            print(f"\n📋 Resumen:")
            print(f"   - Schema OpenAPI: ✅ Accesible y válido")
            print(f"   - Versión: ✅ Cumple patrón 3.1.x")
            print(f"   - Endpoints: ✅ Funcionando")
            print(f"   - Conectividad: ✅ OK")
            return 0
        else:
            print(f"\n⚠️ Schema válido pero endpoints con problemas")
            return 1
    else:
        print(f"\n❌ Problemas con el schema OpenAPI")
        print(f"\n🔧 Posibles soluciones:")
        print(f"   1. Verificar que /openapi.yaml esté disponible")
        print(f"   2. Confirmar versión OpenAPI 3.1.x")
        print(f"   3. Validar formato JSON/YAML")
        return 1

if __name__ == "__main__":
    sys.exit(main())