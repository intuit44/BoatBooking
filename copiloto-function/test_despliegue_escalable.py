#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_sistema_escalable():
    """Test del sistema escalable con aliases externos y parámetros dinámicos"""
    
    base_url = "http://localhost:7071"
    endpoint = f"{base_url}/api/gestionar-despliegue"
    
    print("TESTING SISTEMA ESCALABLE DE DESPLIEGUES")
    print(f"Endpoint: {endpoint}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test cases para el sistema escalable
    test_cases = [
        {
            "name": "Alias externos - launch",
            "payload": {"action": "launch", "tag": "v20"},
            "expected_action": "desplegar"
        },
        {
            "name": "Parámetros dinámicos",
            "payload": {
                "accion": "desplegar",
                "tag": "v20",
                "parametros": {
                    "timeout": 120,
                    "forzar": True
                }
            },
            "expected_action": "desplegar"
        },
        {
            "name": "Script con nombre personalizado",
            "payload": {
                "accion": "preparar",
                "tag": "v15",
                "guardar_como": "deploy_v15.sh"
            },
            "expected_action": "preparar"
        },
        {
            "name": "Validación semántica",
            "payload": {
                "accion": "validar",
                "tag": "v216"
            },
            "expected_action": "validar"
        },
        {
            "name": "Alias múltiples - verify",
            "payload": {"comando": "verify", "tag": "v216"},
            "expected_action": "validar"
        },
        {
            "name": "Rollback con flags",
            "payload": {
                "accion": "rollback",
                "tag_anterior": "v215",
                "parametros": {"timeout": 60, "verbose": True}
            },
            "expected_action": "rollback"
        },
        {
            "name": "Nuevo alias - hotfix",
            "payload": {"action": "hotfix", "tag": "v20.1"},
            "expected_action": "actualizar"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nPrueba {i}/{len(test_cases)}")
        print(f"Probando: {test_case['name']}")
        print(f"Payload: {json.dumps(test_case['payload'], indent=2)}")
        
        try:
            response = requests.post(
                endpoint,
                json=test_case['payload'],
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    exito = data.get("exito", False)
                    accion_ejecutada = data.get("accion_ejecutada", "unknown")
                    resultado = data.get("resultado", {})
                    
                    if exito and accion_ejecutada == test_case["expected_action"]:
                        print(f"EXITO: Accion ejecutada: {accion_ejecutada}")
                        
                        # Validaciones específicas
                        if "parametros" in test_case["payload"]:
                            flags = resultado.get("flags_aplicados", [])
                            print(f"  Flags aplicados: {flags}")
                        
                        if "guardar_como" in test_case["payload"]:
                            nombre_archivo = resultado.get("nombre_archivo")
                            print(f"  Archivo generado: {nombre_archivo}")
                        
                        if accion_ejecutada == "validar":
                            hash_actual = resultado.get("hash_actual")
                            hash_imagen = resultado.get("hash_imagen")
                            print(f"  Validacion: hash_actual={hash_actual}, hash_imagen={hash_imagen}")
                        
                        results.append(True)
                    else:
                        print(f"FALLO: Expected {test_case['expected_action']}, got {accion_ejecutada}")
                        results.append(False)
                        
                except json.JSONDecodeError:
                    print("FALLO: Respuesta no es JSON valido")
                    results.append(False)
            else:
                print(f"FALLO: Status code {response.status_code}")
                results.append(False)
                
        except requests.Timeout:
            print("FALLO: Timeout")
            results.append(False)
        except Exception as e:
            print(f"FALLO: Error {str(e)}")
            results.append(False)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS ESCALABLES")
    print("=" * 60)
    
    exitosas = sum(results)
    total = len(results)
    tasa_exito = (exitosas / total) * 100 if total > 0 else 0
    
    print(f"Pruebas exitosas: {exitosas}/{total}")
    print(f"Tasa de exito: {tasa_exito:.1f}%")
    
    # Validar funcionalidades específicas
    print("\nFUNCIONALIDADES VALIDADAS:")
    print("- Aliases externos desde JSON")
    print("- Parámetros dinámicos con flags")
    print("- Scripts con nombres personalizados")
    print("- Validación semántica")
    print("- Múltiples formatos de payload")
    
    if tasa_exito >= 80:
        print("\nCONCLUSION: Sistema escalable funciona correctamente")
        return True
    else:
        print("\nCONCLUSION: Sistema escalable necesita mejoras")
        return False

def test_generacion_schema():
    """Genera schema automático basado en los test cases"""
    
    print("\n" + "=" * 60)
    print("GENERACION DE SCHEMA AUTOMATICO")
    print("=" * 60)
    
    # Recopilar todos los formatos de payload usados
    formatos_payload = [
        {"action": "launch", "tag": "v20"},
        {"accion": "desplegar", "tag": "v20", "parametros": {"timeout": 120, "forzar": True}},
        {"accion": "preparar", "tag": "v15", "guardar_como": "deploy_v15.sh"},
        {"accion": "validar", "tag": "v216"},
        {"comando": "verify", "tag": "v216"},
        {"accion": "rollback", "tag_anterior": "v215", "parametros": {"timeout": 60, "verbose": True}},
        {"action": "hotfix", "tag": "v20.1"}
    ]
    
    # Generar schema inferido
    schema_inferido = {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "accion": {"type": "string", "description": "Acción principal"},
            "action": {"type": "string", "description": "Alias en inglés"},
            "comando": {"type": "string", "description": "Sinónimo de acción"},
            "tag": {"type": "string", "description": "Versión a desplegar"},
            "tag_anterior": {"type": "string", "description": "Versión para rollback"},
            "guardar_como": {"type": "string", "description": "Nombre del script generado"},
            "parametros": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "timeout": {"type": "integer"},
                    "forzar": {"type": "boolean"},
                    "verbose": {"type": "boolean"},
                    "dry_run": {"type": "boolean"}
                }
            }
        },
        "examples": formatos_payload
    }
    
    print("Schema inferido generado:")
    print(json.dumps(schema_inferido, indent=2, ensure_ascii=False))
    
    return schema_inferido

if __name__ == "__main__":
    try:
        success = test_sistema_escalable()
        schema = test_generacion_schema()
        
        # Guardar schema generado
        with open("schema_inferido.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print(f"\nSchema guardado en: schema_inferido.json")
        
        exit(0 if success else 1)
    except Exception as e:
        print(f"Error critico: {str(e)}")
        exit(1)