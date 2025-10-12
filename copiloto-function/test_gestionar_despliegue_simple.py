#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_endpoint():
    """Test simple del endpoint gestionar-despliegue"""
    
    base_url = "http://localhost:7071"
    endpoint = f"{base_url}/api/gestionar-despliegue"
    
    print("INICIANDO PRUEBAS DEL SISTEMA ROBUSTO DE GESTION DE DESPLIEGUES")
    print(f"Endpoint: {endpoint}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {"name": "Payload vacio", "payload": {}},
        {"name": "Accion detectar", "payload": {"accion": "detectar"}},
        {"name": "Alias ingles", "payload": {"action": "detect"}},
        {"name": "Rollback valido", "payload": {"accion": "rollback", "tag_anterior": "v1.2.2"}},
        {"name": "Campo preparar", "payload": {"preparar": True}},
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nPrueba {i}/{len(test_cases)}")
        print(f"Probando: {test_case['name']}")
        print(f"Payload: {test_case['payload']}")
        
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
                    
                    if exito:
                        print(f"EXITO: Accion ejecutada: {accion_ejecutada}")
                        results.append(True)
                    else:
                        print(f"FALLO: exito=False, accion: {accion_ejecutada}")
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
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    exitosas = sum(results)
    total = len(results)
    tasa_exito = (exitosas / total) * 100 if total > 0 else 0
    
    print(f"Pruebas exitosas: {exitosas}/{total}")
    print(f"Tasa de exito: {tasa_exito:.1f}%")
    
    if tasa_exito >= 80:
        print("CONCLUSION: Sistema funciona correctamente")
        return True
    else:
        print("CONCLUSION: Sistema necesita mejoras")
        return False

if __name__ == "__main__":
    try:
        success = test_endpoint()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Error critico: {str(e)}")
        exit(1)