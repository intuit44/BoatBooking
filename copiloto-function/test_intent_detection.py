#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de detección de intención local
Prueba que la redirección automática funciona correctamente
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_deteccion_intencion():
    """Prueba la detección de intención con casos reales"""
    
    try:
        from services.semantic_intent_parser import detectar_intencion
        
        print("Testing deteccion de intencion automatica...")
        print("=" * 60)
        
        # Casos de prueba que Foundry podría enviar
        test_cases = [
            {
                "input": "cuáles fueron las últimas 5 interacciones",
                "endpoint_actual": "/api/revisar-correcciones",
                "esperado": "historial-interacciones"
            },
            {
                "input": "muéstrame el historial de conversación",
                "endpoint_actual": "/api/revisar-correcciones", 
                "esperado": "historial-interacciones"
            },
            {
                "input": "qué hemos hablado antes",
                "endpoint_actual": "/api/revisar-correcciones",
                "esperado": "historial-interacciones"
            },
            {
                "input": "últimas interacciones del usuario",
                "endpoint_actual": "/api/revisar-correcciones",
                "esperado": "historial-interacciones"
            },
            {
                "input": "qué correcciones se han aplicado",
                "endpoint_actual": "/api/historial-interacciones",
                "esperado": "revisar-correcciones"
            },
            {
                "input": "estado del sistema",
                "endpoint_actual": "/api/revisar-correcciones",
                "esperado": "status"
            }
        ]
        
        resultados = []
        
        for i, caso in enumerate(test_cases, 1):
            print(f"\nTest {i}: '{caso['input']}'")
            print(f"   Endpoint actual: {caso['endpoint_actual']}")
            
            resultado = detectar_intencion(caso['input'], caso['endpoint_actual'])
            
            if resultado.get('redirigir'):
                endpoint_detectado = resultado['endpoint_destino'].replace('/api/', '')
                print(f"   OK Redirigir a: {resultado['endpoint_destino']}")
                print(f"   Razon: {resultado['razon']}")
                print(f"   Confianza: {resultado['confianza']:.2f}")
                
                # Verificar si es correcto
                if endpoint_detectado == caso['esperado']:
                    print(f"   ✅ CORRECTO - Detectó {endpoint_detectado}")
                    resultados.append(True)
                else:
                    print(f"   ❌ ERROR - Esperado {caso['esperado']}, detectó {endpoint_detectado}")
                    resultados.append(False)
            else:
                print(f"   ➡️  No redirigir - {resultado['razon']}")
                if caso['esperado'] == 'no_redirigir':
                    print(f"   ✅ CORRECTO - No debe redirigir")
                    resultados.append(True)
                else:
                    print(f"   ❌ ERROR - Debería redirigir a {caso['esperado']}")
                    resultados.append(False)
        
        # Resumen
        print("\n" + "=" * 60)
        exitosos = sum(resultados)
        total = len(resultados)
        porcentaje = (exitosos / total) * 100
        
        print(f"📊 RESUMEN: {exitosos}/{total} tests exitosos ({porcentaje:.1f}%)")
        
        if porcentaje >= 80:
            print("✅ SISTEMA LISTO PARA DESPLIEGUE")
            return True
        else:
            print("❌ NECESITA AJUSTES ANTES DEL DESPLIEGUE")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_request():
    """Prueba con request mock simulando Foundry"""
    
    try:
        from services.semantic_intent_parser import aplicar_deteccion_intencion
        
        print("\n🧪 Testing con request mock...")
        print("=" * 60)
        
        # Mock request class
        class MockRequest:
            def __init__(self, method="GET", url="/api/revisar-correcciones", params=None, body=None):
                self.method = method
                self.url = url
                self.params = params or {}
                self.headers = {}
                self._body = body
            
            def get_json(self):
                return self._body
        
        # Simular request de Foundry preguntando por historial
        mock_req = MockRequest(
            method="GET",
            url="/api/revisar-correcciones",
            params={"consulta": "últimas interacciones que hice"}
        )
        
        print(f"📥 Request simulada:")
        print(f"   URL: {mock_req.url}")
        print(f"   Params: {mock_req.params}")
        
        fue_redirigido, respuesta = aplicar_deteccion_intencion(mock_req, mock_req.url)
        
        if fue_redirigido:
            print(f"✅ REDIRECCIÓN DETECTADA")
            print(f"   Respuesta tipo: {type(respuesta)}")
            if hasattr(respuesta, 'get_body'):
                try:
                    body = json.loads(respuesta.get_body().decode())
                    print(f"   Datos: {json.dumps(body, indent=2, ensure_ascii=False)[:200]}...")
                except:
                    print(f"   Raw response: {str(respuesta)[:200]}...")
            else:
                print(f"   Respuesta: {str(respuesta)[:200]}...")
            return True
        else:
            print(f"❌ NO SE DETECTÓ REDIRECCIÓN")
            return False
            
    except Exception as e:
        print(f"❌ Error en test mock: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests"""
    
    print("INICIANDO TESTS DE DETECCION DE INTENCION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python: {sys.version}")
    print(f"Working dir: {os.getcwd()}")
    
    # Test 1: Detección básica
    test1_ok = test_deteccion_intencion()
    
    # Test 2: Request mock
    test2_ok = test_mock_request()
    
    # Resultado final
    print("\n" + "=" * 60)
    if test1_ok and test2_ok:
        print("🎉 TODOS LOS TESTS PASARON - LISTO PARA DESPLIEGUE")
        print("\n📋 Próximos pasos:")
        print("   1. Desplegar función actualizada")
        print("   2. Probar con Foundry real")
        print("   3. Monitorear logs de redirección")
        return 0
    else:
        print("⚠️  ALGUNOS TESTS FALLARON - REVISAR ANTES DE DESPLEGAR")
        print("\n🔧 Acciones requeridas:")
        if not test1_ok:
            print("   - Ajustar patrones de detección")
        if not test2_ok:
            print("   - Revisar integración con requests")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)