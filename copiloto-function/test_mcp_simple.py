#!/usr/bin/env python3
"""
Test simplificado del servidor MCP Redis usando STDIO
"""
import json
import subprocess
import os
import threading
import time
from queue import Queue


def read_output(process, output_queue):
    """Lee la salida del proceso en un hilo separado"""
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_queue.put(line.strip())
    except:
        pass


def test_mcp_simple():
    """Test MCP simplificado con timeout"""
    print("🧪 Testing MCP Redis Server - Versión Simplificada")
    print("=" * 70)

    # Configurar environment
    env = os.environ.copy()
    env['MCP_TRANSPORT'] = 'stdio'

    try:
        # Iniciar proceso
        print("🚀 Iniciando servidor MCP...")
        process = subprocess.Popen(
            ['python', 'mcp_redis_wrapper_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=0  # Sin buffer
        )

        # Queue para capturar salida
        output_queue = Queue()
        reader_thread = threading.Thread(
            target=read_output, args=(process, output_queue))
        reader_thread.daemon = True
        reader_thread.start()

        # 1. Inicializar
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        print("📤 Enviando inicialización...")
        process.stdin.write(json.dumps(init_msg) + '\n')
        process.stdin.flush()

        # Esperar respuesta con timeout
        start_time = time.time()
        init_response = None
        while time.time() - start_time < 5:
            try:
                response = output_queue.get(timeout=1)
                if response and response.startswith('{"jsonrpc"'):
                    init_response = json.loads(response)
                    break
            except:
                continue

        if init_response:
            print(
                f"✅ Servidor inicializado: {init_response['result']['serverInfo']['name']}")
        else:
            print("❌ No se recibió respuesta de inicialización")
            return

        # 2. Test de herramienta
        print(f"\n🔄 Probando herramienta redis_cached_chat...")

        tool_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "redis_cached_chat",
                "arguments": {
                    "mensaje": "¿Qué es un barco?",
                    "session_id": "test_session",
                    "agent_id": "TestAgent"
                }
            }
        }

        print("📤 Enviando llamada a herramienta...")
        process.stdin.write(json.dumps(tool_msg) + '\n')
        process.stdin.flush()

        # Esperar respuesta de herramienta con timeout más largo
        start_time = time.time()
        tool_response = None
        print("⏳ Esperando respuesta (max 30 segundos)...")

        while time.time() - start_time < 30:
            try:
                response = output_queue.get(timeout=2)
                if response and '"id":2' in response:
                    tool_response = json.loads(response)
                    break
                elif response:
                    print(f"📝 Log intermedio: {response[:100]}...")
            except:
                print(".", end="", flush=True)
                continue

        if tool_response:
            duration = (time.time() - start_time) * 1000
            if "result" in tool_response:
                content = tool_response["result"]["content"][0]["text"]
                print(f"\n✅ Herramienta ejecutada ({duration:.0f}ms)")
                print(f"📝 Respuesta: {content[:100]}...")

                # Buscar info de cache
                if "[cache_hit=" in content:
                    cache_info = content.split("[")[-1].rstrip("]")
                    print(f"🔍 Cache info: {cache_info}")

                print(f"\n🎯 Test exitoso - Cache Redis integrado correctamente!")
            else:
                print(
                    f"❌ Error en herramienta: {tool_response.get('error', 'Unknown')}")
        else:
            print(f"\n❌ No se recibió respuesta de herramienta (timeout 30s)")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            process.kill()
        print(f"\n🔚 Proceso terminado")


if __name__ == "__main__":
    test_mcp_simple()
