#!/usr/bin/env python3
"""
Test completo del servidor MCP Redis con protocolo SSE correcto
"""
import json
import requests
import uuid


def parse_sse_response(response_text):
    """Parse Server-Sent Events response"""
    lines = response_text.strip().split('\n')
    data_line = None

    for line in lines:
        if line.startswith('data: '):
            data_line = line[6:]  # Remove 'data: ' prefix
            break

    if data_line:
        try:
            return json.loads(data_line)
        except:
            return None
    return None


def call_mcp_with_session(session_id=None):
    """Llamar MCP con session ID establecido"""
    url = "http://localhost:8000/mcp"

    if not session_id:
        session_id = str(uuid.uuid4())

    # 1. Inicializar sesión
    print(f"🔄 Inicializando sesión MCP: {session_id}")

    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "foundry-test-client",
                "version": "1.0.0"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    try:
        response = requests.post(
            url, json=init_payload, headers=headers, timeout=10)

        if response.status_code == 200:
            init_result = parse_sse_response(response.text)
            print(f"✅ Sesión inicializada: {init_result}")

            # 2. Usar la herramienta con el session ID
            print(f"\n🔄 Llamando redis_cached_chat...")

            tool_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "redis_cached_chat",
                    "arguments": {
                        "mensaje": "¿Cómo funciona el motor fuera de borda de una lancha pequeña?",
                        "session_id": "foundry_session",
                        "agent_id": "FoundryAgent"
                    }
                }
            }

            # Agregar session ID a diferentes lugares posibles
            headers["X-MCP-Session-Id"] = session_id
            headers["Session-Id"] = session_id
            headers["X-Session-Id"] = session_id

            tool_response = requests.post(
                url, json=tool_payload, headers=headers, timeout=30)

            print(f"Status: {tool_response.status_code}")
            print(f"Raw response: {tool_response.text[:200]}...")

            if tool_response.status_code == 200:
                tool_result = parse_sse_response(tool_response.text)
                if tool_result and "result" in tool_result:
                    content = tool_result["result"]["content"][0]["text"]
                    print(f"✅ Herramienta ejecutada exitosamente")
                    print(f"📝 Response preview: {content[:100]}...")
                    return {"success": True, "content": content, "session_id": session_id}
                else:
                    print(f"❌ Respuesta inesperada: {tool_result}")
                    return {"success": False, "error": "Respuesta malformada"}
            else:
                print(
                    f"❌ Error {tool_response.status_code}: {tool_response.text}")
                return {"success": False, "error": f"HTTP {tool_response.status_code}"}

        else:
            print(
                f"❌ Fallo en inicialización: {response.status_code} - {response.text}")
            return {"success": False, "error": "Inicialización fallida"}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_cache_behavior_complete():
    """Test completo de comportamiento de cache"""
    print("=" * 80)
    print("🧪 TEST COMPLETO: MCP REDIS CACHE BEHAVIOR (SSE Protocol)")
    print("=" * 80)

    session_id = str(uuid.uuid4())

    # Primera llamada
    print("\n🔄 PRIMERA LLAMADA (esperamos CACHE MISS)")
    print("-" * 60)

    result1 = call_mcp_with_session(session_id)

    if result1["success"]:
        print(f"✅ Primera llamada exitosa")

        # Esperar un momento
        print("\n⏳ Esperando 2 segundos...")
        import time
        time.sleep(2)

        # Segunda llamada con la misma sesión
        print("\n🔄 SEGUNDA LLAMADA (esperamos CACHE HIT)")
        print("-" * 60)

        result2 = call_mcp_with_session(session_id)

        if result2["success"]:
            print(f"✅ Segunda llamada exitosa")

            # Comparar respuestas
            content1 = result1["content"].split("[")[0].strip()
            content2 = result2["content"].split("[")[0].strip()

            if content1 == content2:
                print(f"✅ Cache funcionando: contenido idéntico")
            else:
                print(f"⚠️  Contenidos diferentes - revisar cache")

            print(f"\n🎯 Test completado exitosamente!")
        else:
            print(f"❌ Segunda llamada falló: {result2['error']}")
    else:
        print(f"❌ Primera llamada falló: {result1['error']}")


if __name__ == "__main__":
    test_cache_behavior_complete()
