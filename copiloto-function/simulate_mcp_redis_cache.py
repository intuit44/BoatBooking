# =======================================================================
# SIMULADOR DEL ENTORNO MCP CON CACHE REDIS
# =======================================================================
# Este script simula el comportamiento del servidor MCP usando directamente
# el redis_buffer_service para demostrar el cache hit/miss

import os
import sys
import time
import logging
from typing import Dict, Any

# Configurar el path para importar los servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# Importar servicios
try:
    from services.redis_buffer_service import redis_buffer
    from openai import AzureOpenAI
    print("✅ Servicios importados correctamente")
except ImportError as e:
    print(f"❌ Error importando servicios: {e}")
    sys.exit(1)

# Configuración
DEFAULT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
TEST_AGENT_ID = "MCP_Test_Agent"
TEST_SESSION_ID = "mcp_simulation_session"


def get_openai_client():
    """Obtener cliente OpenAI configurado"""
    try:
        azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
        azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

        if not azure_openai_key or not azure_openai_endpoint:
            raise ValueError(
                "AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT deben estar configurados")

        return AzureOpenAI(
            api_key=azure_openai_key,
            api_version="2024-02-01",
            azure_endpoint=azure_openai_endpoint,
        )
    except Exception as e:
        logging.error(f"❌ Error configurando OpenAI client: {e}")
        return None


def simulate_mcp_redis_cache(mensaje: str, agent_id: str = TEST_AGENT_ID, session_id: str = TEST_SESSION_ID, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Simula el comportamiento del MCP con cache Redis directo"""

    logging.info("=" * 80)
    logging.info(f"🚀 SIMULANDO MCP REQUEST")
    logging.info("=" * 80)

    start = time.perf_counter()
    cache_hit = False
    origen = "model"
    cache_source = "miss"
    respuesta_texto = None

    # Generar hash del mensaje para logging
    msg_hash = redis_buffer.stable_hash(mensaje)
    logging.info(f"📥 Request: agent={agent_id}, session={session_id}")
    logging.info(f"📝 Message: {mensaje}")
    logging.info(f"🔢 Message hash: {msg_hash}")
    logging.info(f"🤖 Model: {model}")
    logging.info("")

    # Verificar estado de Redis
    logging.info(f"🔍 Redis Status: enabled={redis_buffer.is_enabled}")
    if not redis_buffer.is_enabled:
        logging.warning("⚠️ Redis está deshabilitado!")
        return {"ok": False, "error": "Redis cache deshabilitado"}

    # Construir claves para logging detallado
    session_key = redis_buffer.build_llm_session_key(
        agent_id, session_id, mensaje, model)
    global_key = redis_buffer.build_llm_global_key(agent_id, mensaje, model)

    logging.info(f"🔑 Session key: {session_key}")
    logging.info(f"🌐 Global key:  {global_key}")
    logging.info("")

    # Intentar obtener desde cache Redis
    logging.info("🔍 Buscando en Redis cache...")

    cached, cache_source = redis_buffer.get_llm_cached_response(
        agent_id=agent_id,
        session_id=session_id,
        message=mensaje,
        model=model,
        use_global_cache=True,
    )

    if cached:
        cache_hit = True
        origen = f"redis_{cache_source}"
        respuesta_texto = cached.get(
            "respuesta") if isinstance(cached, dict) else cached
        logging.info(f"✅ CACHE HIT! Source: {cache_source}")
        logging.info(
            f"📤 Cached response preview: {str(respuesta_texto)[:100]}...")
        logging.info("")
    else:
        logging.info(f"❌ CACHE MISS - calling OpenAI model")
        logging.info("")

        # Cache miss: llamar al modelo
        try:
            logging.info(f"🤖 Calling OpenAI model: {model}")
            openai_client = get_openai_client()
            if not openai_client:
                return {"ok": False, "error": "No se pudo configurar OpenAI client"}

            completion = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": mensaje}],
            )
            respuesta_texto = completion.choices[0].message.content
            logging.info(
                f"✅ Model response received: {len(respuesta_texto)} chars")
            logging.info(f"📤 Response preview: {respuesta_texto[:100]}...")
            logging.info("")

            # Guardar en cache
            try:
                logging.info("💾 Saving to Redis cache...")
                redis_buffer.cache_llm_response(
                    agent_id=agent_id,
                    session_id=session_id,
                    message=mensaje,
                    model=model,
                    response_data={
                        "respuesta": respuesta_texto,
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "model": model,
                        "timestamp": time.time()
                    },
                    use_global_cache=True,
                )
                logging.info("✅ Response cached successfully")
                logging.info("")
            except Exception as cache_err:
                logging.error(f"❌ Cache write error: {cache_err}")

        except Exception as e:
            logging.error(f"❌ OpenAI model error: {e}")
            return {"ok": False, "error": f"Error llamando al modelo: {e}"}

    dur_ms = (time.perf_counter() - start) * 1000

    # Resumen final
    logging.info("📊 SUMMARY:")
    logging.info(f"   Cache Hit: {cache_hit}")
    logging.info(f"   Source: {cache_source}")
    logging.info(f"   Duration: {dur_ms:.0f}ms")
    logging.info(f"   Response Length: {len(str(respuesta_texto))} chars")

    return {
        "ok": True,
        "respuesta": respuesta_texto,
        "cache_hit": cache_hit,
        "origen": origen,
        "duration_ms": round(dur_ms, 2),
        "session_id": session_id,
        "agent_id": agent_id,
        "model": model,
        "cache_source": cache_source,
        "redis_enabled": redis_buffer.is_enabled,
        "msg_hash": msg_hash[:16],
        "session_key": session_key,
        "global_key": global_key
    }


def run_cache_test():
    """Ejecutar prueba completa de cache hit/miss"""

    print("\n🎯 SIMULADOR MCP - PRUEBA DE CACHE REDIS")
    print("=" * 60)
    print()

    # Mensaje de prueba
    test_message = "¿Cómo funciona el motor fuera de borda de una lancha pequeña?"

    print(f"📝 Mensaje de prueba: {test_message}")
    print()

    # Primera llamada (debería ser cache miss)
    print("🔄 PRIMERA LLAMADA (esperamos CACHE MISS)")
    print("-" * 50)
    result1 = simulate_mcp_redis_cache(test_message)

    if not result1["ok"]:
        print(f"❌ Error en primera llamada: {result1['error']}")
        return

    print(f"✅ Primera llamada completada:")
    print(f"   Cache Hit: {result1['cache_hit']}")
    print(f"   Duration: {result1['duration_ms']}ms")
    print(f"   Source: {result1['cache_source']}")
    print()

    # Esperar un momento
    print("⏳ Esperando 2 segundos...")
    time.sleep(2)
    print()

    # Segunda llamada (debería ser cache hit)
    print("🔄 SEGUNDA LLAMADA (esperamos CACHE HIT)")
    print("-" * 50)
    result2 = simulate_mcp_redis_cache(test_message)

    if not result2["ok"]:
        print(f"❌ Error en segunda llamada: {result2['error']}")
        return

    print(f"✅ Segunda llamada completada:")
    print(f"   Cache Hit: {result2['cache_hit']}")
    print(f"   Duration: {result2['duration_ms']}ms")
    print(f"   Source: {result2['cache_source']}")
    print()

    # Verificar que la segunda fue cache hit
    if result2['cache_hit']:
        print("🎉 ¡ÉXITO! Cache funcionando correctamente:")
        print(f"   ✅ Primera llamada: MISS ({result1['duration_ms']}ms)")
        print(f"   ✅ Segunda llamada: HIT ({result2['duration_ms']}ms)")
        print(
            f"   🚀 Speedup: {result1['duration_ms']/result2['duration_ms']:.1f}x más rápido")
    else:
        print("⚠️ PROBLEMA: Segunda llamada no fue cache hit")
        print("   Posibles causas:")
        print("   • TTL muy corto")
        print("   • Error en cache write")
        print("   • Hash diferente")

    print()
    print("🔍 CLAVES GENERADAS:")
    print(f"   Session: {result1['session_key']}")
    print(f"   Global:  {result1['global_key']}")
    print(f"   Hash:    {result1['msg_hash']}")


def test_multiple_messages():
    """Probar con múltiples mensajes diferentes"""

    print("\n🧪 PRUEBA CON MÚLTIPLES MENSAJES")
    print("=" * 60)

    test_messages = [
        "¿Qué es un barco?",
        "Explica los tipos de embarcaciones",
        "¿Cómo funciona un motor de lancha?",
        "¿Qué es un barco?"  # Repetido para cache hit
    ]

    results = []

    for i, msg in enumerate(test_messages, 1):
        print(f"\n📝 Mensaje {i}: {msg}")
        print("-" * 40)

        result = simulate_mcp_redis_cache(
            msg, agent_id=f"TestAgent_{i%2}", session_id=f"session_{i%2}")
        results.append(result)

        if result["ok"]:
            status = "HIT" if result["cache_hit"] else "MISS"
            print(
                f"   {status} - {result['duration_ms']}ms - {result['cache_source']}")
        else:
            print(f"   ERROR: {result['error']}")

        time.sleep(1)

    print(f"\n📊 RESUMEN DE {len(results)} LLAMADAS:")
    hits = sum(1 for r in results if r.get("cache_hit", False))
    misses = len(results) - hits
    print(f"   Cache Hits: {hits}")
    print(f"   Cache Misses: {misses}")
    print(f"   Hit Ratio: {hits/len(results)*100:.1f}%")


if __name__ == "__main__":
    try:
        print("🚀 Iniciando simulador MCP con Redis cache...")
        print()

        # Verificar configuración
        print("🔧 Verificando configuración...")
        print(f"   Redis enabled: {redis_buffer.is_enabled}")
        print(
            f"   OpenAI endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'Not configured')}")
        print(f"   Model: {DEFAULT_MODEL}")
        print()

        if not redis_buffer.is_enabled:
            print("❌ Redis no está habilitado. Verifica la configuración.")
            sys.exit(1)

        # Ejecutar pruebas
        run_cache_test()
        test_multiple_messages()

        print("\n🎯 Simulación completada exitosamente!")

    except KeyboardInterrupt:
        print("\n\n👋 Simulación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error en simulación: {e}")
        logging.exception("Error completo:")
