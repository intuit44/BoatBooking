#!/usr/bin/env python3
"""
Test directo del endpoint Redis para verificar conectividad
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)


def test_redis_endpoint():
    """Test directo al endpoint ejecutar-cli"""
    base_url = 'http://localhost:7071/api/ejecutar-cli'

    print('🔍 Probando endpoint Redis directamente...')

    # Test 1: PING
    try:
        data = {'comando': 'PING'}
        response = requests.post(base_url, json=data, timeout=30)
        result = response.json()

        print(f'Status: {response.status_code}')
        print(f'PING result: {json.dumps(result, indent=2)}')

        if not result.get('exito'):
            print('❌ PING falló')
            return False

        # Test 2: KEYS thread:*
        print('\n🔍 Probando comando KEYS thread:*...')
        data2 = {'comando': 'KEYS thread:*'}
        response2 = requests.post(base_url, json=data2, timeout=30)
        result2 = response2.json()

        print(f'KEYS result: {json.dumps(result2, indent=2)}')

        if result2.get('exito'):
            claves = result2.get('salida', [])
            if isinstance(claves, list):
                print(f'✅ Encontradas {len(claves)} claves thread:*')
                for i, clave in enumerate(claves[:5], 1):  # Primeras 5
                    print(f'  {i}. {clave}')
                return len(claves) > 0
            else:
                print(f'⚠️ Resultado inesperado para KEYS: {type(claves)}')
        else:
            print('❌ KEYS thread:* falló')

        return True

    except Exception as e:
        print(f'❌ Error en test: {e}')
        return False


if __name__ == "__main__":
    success = test_redis_endpoint()
    print(f'\n🎯 Test {"exitoso" if success else "falló"}')
