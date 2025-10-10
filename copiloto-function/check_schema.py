#!/usr/bin/env python3
"""
Validar schema OpenAPI local - version simple
"""
import json
import re

def validate_openapi_version(openapi_version):
    pattern = r"^3\.1\.\d+(-.+)?$"
    return re.match(pattern, openapi_version) is not None

def main():
    print("Validando schema OpenAPI local...")
    print("=" * 50)
    
    try:
        with open("openapi_copiloto_local.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        
        schema = json.loads(content)
        
        # Validar version
        openapi_version = schema.get("openapi", "unknown")
        print(f"OpenAPI Version: {openapi_version}")
        
        if validate_openapi_version(openapi_version):
            print("OK - Version VALIDA para Agent898")
        else:
            print("ERROR - Version INVALIDA para Agent898")
            return False
        
        # Contar endpoints
        paths = schema.get("paths", {})
        print(f"OK - Endpoints disponibles: {len(paths)}")
        
        # Verificar operationIds clave
        key_endpoints = {
            "/api/status": "getStatus",
            "/api/health": "healthCheck", 
            "/api/ejecutar-cli": "ejecutarCli",
            "/api/hybrid": "processHybrid"
        }
        
        print("\nVerificando endpoints clave:")
        all_good = True
        
        for endpoint, expected_op_id in key_endpoints.items():
            if endpoint in paths:
                methods = paths[endpoint]
                found_op_id = None
                for method, details in methods.items():
                    found_op_id = details.get("operationId", "MISSING")
                    break
                
                if found_op_id and found_op_id != "MISSING":
                    print(f"OK - {endpoint} -> {found_op_id}")
                else:
                    print(f"ERROR - {endpoint} -> SIN operationId")
                    all_good = False
            else:
                print(f"ERROR - {endpoint} -> NO ENCONTRADO")
                all_good = False
        
        print(f"\n{'='*50}")
        if all_good:
            print("RESULTADO: Schema listo para Agent898!")
            print("\nProximos pasos:")
            print("1. Ejecutar script de despliegue")
            print("2. Verificar /openapi.yaml disponible")
            return True
        else:
            print("RESULTADO: Schema necesita correcciones")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)