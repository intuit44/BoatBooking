#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rapido del endpoint ejecutar-comando"""

import requests
import json

def test_quick():
    url = "http://localhost:7071/api/ejecutar-comando"
    
    # Test simple
    test_data = {"comando": "echo 'Test del endpoint generico'"}
    
    try:
        print("[TEST] Probando endpoint ejecutar-comando...")
        response = requests.post(url, json=test_data, timeout=5)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    test_quick()