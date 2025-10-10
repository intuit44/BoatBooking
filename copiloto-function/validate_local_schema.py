#!/usr/bin/env python3
"""
Validar schema OpenAPI local antes del despliegue
"""
import json
import re

def validate_openapi_version(openapi_version):
    """Valida que la version OpenAPI cumpla con el patron de Agent898"""
    pattern = r"^3\.1\.\d+(-.+)?$"
    return re.match(pattern, openapi_version) is not None

def validate_local_schema():
    """Valida el schema local"""
    print("Validando schema OpenAPI local...")
    print("=" * 50)
    
    try:
        # Leer archivo local
        with open("openapi_copiloto_local.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parsear JSON
        schema = json.loads(content)
        
        # Validar version
        openapi_version = schema.get("openapi", "unknown")
        print(f"OpenAPI Version: {openapi_version}")
        
        if validate_openapi_version(openapi_version):
            print("✓ Version VALIDA para Agent898")
        else:
            print("✗ Version INVALIDA para Agent898")
            print(f"  Patron requerido: ^3\\.1\\.\\d+(-.+)?$")
            return False
        
        # Contar endpoints
        paths = schema.get("paths", {})
        print(f"✓ Endpoints disponibles: {len(paths)}")
        
        # Verificar operationIds
        missing_operation_ids = []
        for path, methods in paths.items():
            for method, details in methods.items():
                if "operationId" not in details:
                    missing_operation_ids.append(f"{method.upper()} {path}")
        
        if missing_operation_ids:
            print(f"✗ Endpoints sin operationId:")
            for endpoint in missing_operation_ids[:5]:  # Mostrar solo los primeros 5
                print(f"  - {endpoint}")
            if len(missing_operation_ids) > 5:
                print(f"  ... y {len(missing_operation_ids) - 5} más")
        else:
            print("✓ Todos los endpoints tienen operationId")
        
        # Verificar endpoints clave para Agent898
        key_endpoints = ["/api/status", "/api/health", "/api/ejecutar-cli", "/api/hybrid"]
        print(f"\nVerificando endpoints clave:")
        
        for endpoint in key_endpoints:
            if endpoint in paths:
                methods = list(paths[endpoint].keys())
                operation_ids = []
                for method in methods:
                    op_id = paths[endpoint][method].get("operationId", "MISSING")
                    operation_ids.append(f"{method.upper()}:{op_id}")
                print(f"✓ {endpoint} -> {', '.join(operation_ids)}")
            else:
                print(f"✗ {endpoint} -> NO ENCONTRADO")
        
        print(f"\n{'='*50}")
        if not missing_operation_ids and validate_openapi_version(openapi_version):
            print("🎉 Schema listo para Agent898!")
            print("\nPróximos pasos:")
            print("1. Ejecutar script de despliegue")
            print("2. Verificar que /openapi.yaml esté disponible")
            print("3. Probar conexión de Agent898")
            return True
        else:
            print("⚠️  Schema necesita correcciones antes del despliegue")
            return False
            
    except FileNotFoundError:
        print("✗ Archivo openapi_copiloto_local.yaml no encontrado")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Error parseando JSON: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = validate_local_schema()
    exit(0 if success else 1)