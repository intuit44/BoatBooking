#!/usr/bin/env python3
"""
Test rápido del router semántico
"""

import requests
import json

def test_quick():
    base_url = "http://localhost:7071"
    
    tests = [
        {"intencion": "verificar:metricas"},
        {"intencion": "diagnosticar:completo"},
        {"intencion": "diagnostico"}
    ]
    
    for test in tests:
        try:
            response = requests.post(
                f"{base_url}/api/ejecutar",
                json=test,
                timeout=30
            )
            
            data = response.json()
            exito = data.get('exito', False)
            
            print(f"{test['intencion']}: {response.status_code} - Exito: {exito}")
            
            if 'diagnostico' in str(data).lower():
                print(f"  [OK] Redirigido a diagnostico")
            else:
                print(f"  [WARN] No redirigido")
                
        except Exception as e:
            print(f"{test['intencion']}: ERROR - {e}")

if __name__ == "__main__":
    test_quick()