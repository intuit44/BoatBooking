#!/usr/bin/env python3
"""
Test del servidor MCP Redis en modo STDIO (como lo haría Foundry realmente)
"""
import json
import subprocess
import os
import time


def test_mcp_stdio():
    """Test usando STDIO mode del servidor MCP"""
    print("🧪 Testing MCP Redis Server en modo STDIO")
    print("=" * 80)

    # Configurar environment variables para STDIO
    env = os.environ.copy()
    env['MCP_TRANSPORT'] = 'stdio'

    # Iniciar el proceso del servidor MCP
    process = subprocess.Popen(
        ['python', 'mcp_redis_wrapper_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    try:
        # 1. Inicializar
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "foundry-test",
                    "version": "1.0"
                }
            }
        }

        print("🔄 Enviando inicialización...")
        process.stdin.write(json.dumps(init_msg) + '\n')
        process.stdin.flush()

        # Leer respuesta de inicialización
        init_response = process.stdout.readline().strip()
        print(
            f"✅ Inicialización exitosa: {json.loads(init_response)['result']['serverInfo']}")

        # 2. Primera llamada a redis_cached_chat (debería ser CACHE MISS)
        print(f"\n🔄 PRIMERA LLAMADA (esperamos CACHE MISS)")
        print("-" * 60)

        start_time = time.time()

        tool_call1 = {
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

        process.stdin.write(json.dumps(tool_call1) + '\n')
        process.stdin.flush()

        # Leer respuesta
        tool_response1 = process.stdout.readline().strip()
        duration1 = (time.time() - start_time) * 1000

        response1_data = json.loads(tool_response1)
        if "result" in response1_data:
            content1 = response1_data["result"]["content"][0]["text"]
            print(
                f"✅ Primera respuesta ({duration1:.1f}ms): {content1[:80]}...")

            # Buscar info de cache en la respuesta
            if "[cache_hit=" in content1:
                cache_info = content1.split("[")[-1].rstrip("]")
                print(f"🔍 Cache info: {cache_info}")

        # 3. Esperar un momento
        print(f"\n⏳ Esperando 2 segundos...")
        time.sleep(2)

        # 4. Segunda llamada (debería ser CACHE HIT)
        print(f"\n🔄 SEGUNDA LLAMADA (esperamos CACHE HIT)")
        print("-" * 60)

        start_time = time.time()

        tool_call2 = {
            "jsonrpc": "2.0",
            "id": 3,
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

        process.stdin.write(json.dumps(tool_call2) + '\n')
        process.stdin.flush()

        # Leer respuesta
        tool_response2 = process.stdout.readline().strip()
        duration2 = (time.time() - start_time) * 1000

        response2_data = json.loads(tool_response2)
        if "result" in response2_data:
            content2 = response2_data["result"]["content"][0]["text"]
            print(
                f"✅ Segunda respuesta ({duration2:.1f}ms): {content2[:80]}...")

            # Buscar info de cache en la respuesta
            if "[cache_hit=" in content2:
                cache_info = content2.split("[")[-1].rstrip("]")
                print(f"🔍 Cache info: {cache_info}")

            # Comparar tiempos
            speedup = duration1 / duration2 if duration2 > 0 else 0
            print(f"\n📊 COMPARACIÓN:")
            print(f"   Primera llamada: {duration1:.1f}ms")
            print(f"   Segunda llamada: {duration2:.1f}ms")
            print(f"   Speedup: {speedup:.1f}x más rápido")

            # Verificar contenido idéntico
            content1_clean = content1.split("[")[0].strip()
            content2_clean = content2.split("[")[0].strip()

            if content1_clean == content2_clean:
                print(f"✅ Cache funcionando correctamente - contenido idéntico")
            else:
                print(f"⚠️  Contenido diferente - revisar cache")

        print(f"\n🎯 Test STDIO completado exitosamente!")

    except Exception as e:
        print(f"❌ Error durante el test: {e}")

    finally:
        # Limpiar proceso
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()


if __name__ == "__main__":
    test_mcp_stdio()
