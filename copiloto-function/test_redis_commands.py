#!/usr/bin/env python3
"""
Test script para validar comandos Redis en el endpoint ejecutar-cli.
Prueba conectividad, diagnóstico y operaciones básicas de caché.
"""

import json
import requests
import time

# URL del endpoint local
BASE_URL = "http://localhost:7071"
CLI_ENDPOINT = f"{BASE_URL}/api/ejecutar-cli"


def ejecutar_comando_redis(comando):
    """Ejecuta un comando Redis y retorna la respuesta."""
    payload = {
        "comando": comando
    }

    try:
        response = requests.post(
            CLI_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Session-ID": "redis-test-session",
                "Agent-ID": "redis-test-agent"
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "response": response.text[:500]
            }
    except Exception as e:
        return {
            "error": f"Error de conexión: {str(e)}"
        }


def test_redis_connectivity():
    """Test básico de conectividad Redis."""
    print("🧪 Probando conectividad Redis...")

    resultado = ejecutar_comando_redis("PING")

    print(f"Comando: PING")
    print(f"Status: {'✅ ÉXITO' if resultado.get('exito') else '❌ FALLÓ'}")

    if resultado.get('exito'):
        print(f"Respuesta: {resultado.get('salida', 'Sin salida')}")
        if resultado.get('redis_info'):
            redis_info = resultado['redis_info']
            print(f"Host: {redis_info.get('host')}")
            print(f"Puerto: {redis_info.get('port')}")
            print(f"DB: {redis_info.get('db')}")
            print(f"Habilitado: {redis_info.get('enabled')}")
    else:
        print(f"Error: {resultado.get('error', 'Error desconocido')}")

    return resultado.get('exito', False)


def test_redis_info():
    """Test de información del servidor Redis."""
    print("\n🧪 Probando información del servidor Redis...")

    resultado = ejecutar_comando_redis("INFO")

    print(f"Comando: INFO")
    print(f"Status: {'✅ ÉXITO' if resultado.get('exito') else '❌ FALLÓ'}")

    if resultado.get('exito'):
        salida = resultado.get('salida', '')
        if len(salida) > 200:
            print(f"Salida (primeros 200 chars): {salida[:200]}...")
        else:
            print(f"Salida: {salida}")
    else:
        print(f"Error: {resultado.get('error', 'Error desconocido')}")

    return resultado.get('exito', False)


def test_redis_dbsize():
    """Test para obtener tamaño de la base de datos."""
    print("\n🧪 Probando tamaño de DB Redis...")

    resultado = ejecutar_comando_redis("DBSIZE")

    print(f"Comando: DBSIZE")
    print(f"Status: {'✅ ÉXITO' if resultado.get('exito') else '❌ FALLÓ'}")

    if resultado.get('exito'):
        print(f"Número de claves: {resultado.get('salida', '0')}")
    else:
        print(f"Error: {resultado.get('error', 'Error desconocido')}")

    return resultado.get('exito', False)


def test_redis_keys():
    """Test para listar claves en Redis."""
    print("\n🧪 Probando listado de claves Redis...")

    resultado = ejecutar_comando_redis("KEYS *")

    print(f"Comando: KEYS *")
    print(f"Status: {'✅ ÉXITO' if resultado.get('exito') else '❌ FALLÓ'}")

    if resultado.get('exito'):
        salida = resultado.get('salida', '')
        if not salida.strip():
            print("No se encontraron claves en el cache")
        else:
            claves = salida.split('\n') if '\n' in salida else [salida]
            print(f"Claves encontradas ({len(claves)}):")
            # Mostrar solo las primeras 10
            for i, clave in enumerate(claves[:10]):
                print(f"  {i+1}. {clave}")
            if len(claves) > 10:
                print(f"  ... y {len(claves) - 10} más")
    else:
        print(f"Error: {resultado.get('error', 'Error desconocido')}")

    return resultado.get('exito', False)


def test_redis_buffer_stats():
    """Test del comando personalizado BUFFER_STATS."""
    print("\n🧪 Probando estadísticas del Buffer Service...")

    resultado = ejecutar_comando_redis("BUFFER_STATS")

    print(f"Comando: BUFFER_STATS")
    print(f"Status: {'✅ ÉXITO' if resultado.get('exito') else '❌ FALLÓ'}")

    if resultado.get('exito'):
        try:
            stats = json.loads(resultado.get('salida', '{}'))
            print("Estadísticas del Buffer Service:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except json.JSONDecodeError:
            print(f"Salida: {resultado.get('salida', '')}")
    else:
        print(f"Error: {resultado.get('error', 'Error desconocido')}")

    return resultado.get('exito', False)


def test_redis_operations():
    """Test de operaciones básicas SET/GET."""
    print("\n🧪 Probando operaciones básicas Redis SET/GET...")

    # Test SET
    test_key = f"test_key_{int(time.time())}"
    test_value = "test_value_from_agent"

    resultado_set = ejecutar_comando_redis(f"SET {test_key} {test_value}")
    print(
        f"SET {test_key}: {'✅ ÉXITO' if resultado_set.get('exito') else '❌ FALLÓ'}")

    if resultado_set.get('exito'):
        # Test GET
        resultado_get = ejecutar_comando_redis(f"GET {test_key}")
        print(
            f"GET {test_key}: {'✅ ÉXITO' if resultado_get.get('exito') else '❌ FALLÓ'}")

        if resultado_get.get('exito'):
            valor_obtenido = resultado_get.get('salida', '').strip()
            if valor_obtenido == test_value:
                print(f"✅ Valor correcto obtenido: {valor_obtenido}")
            else:
                print(
                    f"⚠️ Valor diferente: esperado '{test_value}', obtenido '{valor_obtenido}'")

        # Limpiar
        ejecutar_comando_redis(f"DEL {test_key}")
        return resultado_get.get('exito', False)

    return False


def test_cache_patterns():
    """Test para buscar patrones de caché específicos."""
    print("\n🧪 Buscando patrones de caché conocidos...")

    patrones = [
        "memoria:*",
        "thread:*",
        "narrativa:*",
        "response:*",
        "search:*",
        "llm:*",
        "logs_analysis:*"
    ]

    for patron in patrones:
        resultado = ejecutar_comando_redis(f"KEYS {patron}")
        if resultado.get('exito'):
            salida = resultado.get('salida', '').strip()
            count = len(salida.split('\n')) if salida else 0
            print(f"  {patron}: {count} claves encontradas")
        else:
            print(f"  {patron}: Error - {resultado.get('error', 'desconocido')}")


if __name__ == "__main__":
    print("🔧 Test de comandos Redis en endpoint ejecutar-cli")
    print("=" * 60)

    # Tests en secuencia
    tests = [
        ("Conectividad", test_redis_connectivity),
        ("Información", test_redis_info),
        ("Tamaño DB", test_redis_dbsize),
        ("Claves", test_redis_keys),
        ("Buffer Stats", test_redis_buffer_stats),
        ("Operaciones", test_redis_operations),
    ]

    resultados = {}

    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados[nombre] = resultado
        except Exception as e:
            print(f"❌ Error en test {nombre}: {e}")
            resultados[nombre] = False

    # Test adicional para patrones de caché
    test_cache_patterns()

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 Resumen de resultados:")

    exitosos = sum(1 for r in resultados.values() if r)
    total = len(resultados)

    for nombre, resultado in resultados.items():
        print(f"  {nombre}: {'✅ ÉXITO' if resultado else '❌ FALLÓ'}")

    print(f"\nTotal: {exitosos}/{total} tests exitosos")

    if exitosos == total:
        print("🎉 ¡Todos los tests de Redis pasaron!")
    elif exitosos > 0:
        print("⚠️ Redis funciona parcialmente. Revisar configuración.")
    else:
        print("❌ Redis no está funcionando. Verificar servicio y credenciales.")

    print("\n💡 Para diagnosticar caché vacío:")
    print("  - Ejecutar: INFO")
    print("  - Verificar: KEYS *")
    print("  - Stats: BUFFER_STATS")
    print("  - Configuración: CONFIG GET *")
