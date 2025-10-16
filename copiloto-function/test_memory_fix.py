#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar que la memoria funciona correctamente
"""

import requests
import json
import time

def test_memory_system():
    """Prueba el sistema de memoria con session_id consistente"""
    
    base_url = "http://localhost:7071"
    session_id = "test_session_fix_123"
    agent_id = "TestAgent"
    
    headers = {
        "Content-Type": "application/json",
        "Session-ID": session_id,
        "Agent-ID": agent_id
    }
    
    print(f"Probando sistema de memoria con Session-ID: {session_id}")
    
    # 1. Hacer una llamada al endpoint copiloto
    print("\n1. Llamando a /api/copiloto...")
    response1 = requests.post(
        f"{base_url}/api/copiloto",
        headers=headers,
        json={"comando": "ver estado del sistema"}
    )
    
    print(f"Status: {response1.status_code}")
    if response1.status_code == 200:
        data = response1.json()
        print(f"Respuesta recibida")
        print(f"Session info: {data.get('metadata', {}).get('session_info', {})}")
    else:
        print(f"Error: {response1.text}")
    
    # 2. Esperar un momento
    print("\nEsperando 2 segundos...")
    time.sleep(2)
    
    # 3. Consultar historial con el mismo session_id
    print("\n2. Consultando historial...")
    response2 = requests.get(
        f"{base_url}/api/historial-interacciones",
        headers=headers
    )
    
    print(f"Status: {response2.status_code}")
    if response2.status_code == 200:
        data = response2.json()
        print(f"Historial consultado")
        print(f"Total interacciones: {data.get('total', 0)}")
        print(f"Mensaje: {data.get('mensaje', '')}")
        
        if data.get('total', 0) > 0:
            print("MEMORIA FUNCIONANDO! Se encontraron interacciones")
            for i, interaccion in enumerate(data.get('interacciones', [])[:3]):
                print(f"  {i+1}. {interaccion.get('timestamp', '')} - {interaccion.get('endpoint', '')}")
        else:
            print("No se encontraron interacciones - revisar logs")
    else:
        print(f"Error consultando historial: {response2.text}")
    
    # 4. Hacer otra llamada para verificar continuidad
    print("\n3. Segunda llamada para verificar continuidad...")
    response3 = requests.post(
        f"{base_url}/api/ejecutar",
        headers=headers,
        json={"intencion": "dashboard"}
    )
    
    print(f"Status: {response3.status_code}")
    if response3.status_code == 200:
        print("Segunda llamada exitosa")
    
    # 5. Consultar historial final
    print("\n4. Consulta final de historial...")
    response4 = requests.get(
        f"{base_url}/api/historial-interacciones",
        headers=headers
    )
    
    if response4.status_code == 200:
        data = response4.json()
        print(f"Total final: {data.get('total', 0)} interacciones")
        
        if data.get('total', 0) >= 2:
            print("SISTEMA DE MEMORIA COMPLETAMENTE FUNCIONAL!")
        else:
            print("Memoria parcialmente funcional - revisar configuracion")

if __name__ == "__main__":
    test_memory_system()