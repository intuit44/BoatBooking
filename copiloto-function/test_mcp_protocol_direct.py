#!/usr/bin/env python3
"""
Test simple del servidor MCP para entender su protocolo exacto
"""
import json
import requests


def test_mcp_initialize():
    """Probar inicialización del protocolo MCP"""
    url = "http://localhost:8000/mcp"

    # Intentar inicializar la sesión MCP
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    print("🔄 Probando inicialización MCP...")

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Inicialización exitosa")
            return result
        else:
            print("❌ Fallo en inicialización")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_list_tools():
    """Listar herramientas disponibles"""
    url = "http://localhost:8000/mcp"

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    print("\n🔄 Listando herramientas disponibles...")

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧪 Testing MCP Protocol Direct")

    # Intentar inicializar
    init_result = test_mcp_initialize()

    # Intentar listar herramientas
    test_list_tools()
