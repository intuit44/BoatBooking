"""
Script de validación local para historial_interacciones
Simula la consulta del agente y valida la respuesta enriquecida
"""

import json
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Simular memoria previa (como la que viene de Cosmos)
memoria_previa = {
    "tiene_historial": True,
    "total_interacciones": 50,
    "resumen_conversacion": "Sesión estable: 5 interacciones. Última acción: unknown (✅)",
    "interacciones_recientes": [
        {
            "numero": 1,
            "timestamp": "2025-10-27T23:10:25.341900",
            "endpoint": "hybrid",
            "consulta": "",
            "exito": True,
            "texto_semantico": "Interacción en 'hybrid' ejecutada por unknown_agent. Éxito: ✅. Endpoint: hybrid."
        },
        {
            "numero": 2,
            "timestamp": "2025-10-27T23:10:24.504483",
            "endpoint": "verificar_app_insights",
            "consulta": "",
            "exito": True,
            "texto_semantico": "Interacción en 'verificar-app-insights' ejecutada por unknown_agent. Éxito: ✅."
        },
        {
            "numero": 3,
            "timestamp": "2025-10-27T23:10:23.723968",
            "endpoint": "verificar_sistema",
            "consulta": "",
            "exito": True,
            "texto_semantico": "Interacción en 'verificar-sistema' ejecutada por unknown_agent. Éxito: ✅."
        }
    ],
    "contexto_inteligente": {
        "resumen": "Sesión estable: 5 interacciones. Última acción: unknown (✅)",
        "tiene_memoria": True,
        "total_interacciones": 50
    }
}

def test_detect_query_intent():
    """Probar detección de intención"""
    print("\n🧪 TEST 1: Detección de intención")
    print("=" * 60)
    
    try:
        from semantic_response_enhancer import detect_query_intent
        
        queries = [
            "¿de qué estábamos hablando?",
            "¿qué hicimos antes?",
            "¿en qué quedamos?",
            "dame el contexto",
            "continuar"
        ]
        
        for query in queries:
            intent = detect_query_intent(query)
            print(f"Query: '{query}' → Intent: {intent}")
        
        print("✅ TEST 1 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        return False

def test_generate_historical_response():
    """Probar generación de respuesta histórica"""
    print("\n🧪 TEST 2: Generación de respuesta histórica")
    print("=" * 60)
    
    try:
        from semantic_response_enhancer import generate_historical_response
        
        respuesta = generate_historical_response(
            interacciones=memoria_previa["interacciones_recientes"],
            interpretacion="Patrón: diagnostico en api | Intención: diagnosticar_sistema (87%)",
            contexto_inteligente=memoria_previa["contexto_inteligente"]
        )
        
        print("\n📊 RESPUESTA GENERADA:")
        print("-" * 60)
        print(respuesta)
        print("-" * 60)
        
        # Validar que contiene elementos clave
        assert "ANÁLISIS CONTEXTUAL" in respuesta or "Patrón" in respuesta
        assert "interacciones" in respuesta.lower()
        
        print("\n✅ TEST 2 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhance_response():
    """Probar mejora completa de respuesta"""
    print("\n🧪 TEST 3: Mejora completa de respuesta")
    print("=" * 60)
    
    try:
        from semantic_response_enhancer import enhance_response_with_semantic_context
        
        user_query = "¿de qué estábamos hablando?"
        original_response = "Se encontraron 5 interacciones..."
        
        respuesta_enriquecida = enhance_response_with_semantic_context(
            original_response=original_response,
            memoria_contexto=memoria_previa,
            user_query=user_query
        )
        
        print("\n📊 RESPUESTA ENRIQUECIDA:")
        print("-" * 60)
        print(respuesta_enriquecida)
        print("-" * 60)
        
        # Validar que es diferente y más rica
        assert len(respuesta_enriquecida) > len(original_response)
        assert respuesta_enriquecida != original_response
        
        print("\n✅ TEST 3 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_response_structure():
    """Probar estructura completa de respuesta"""
    print("\n🧪 TEST 4: Estructura de respuesta final")
    print("=" * 60)
    
    try:
        from semantic_response_enhancer import enhance_response_with_semantic_context, detect_query_intent
        
        user_query = "¿de qué estábamos hablando?"
        
        # Simular el flujo completo
        query_intent = detect_query_intent(user_query)
        respuesta_enriquecida = enhance_response_with_semantic_context(
            original_response="",
            memoria_contexto=memoria_previa,
            user_query=user_query
        )
        
        # Construir response_data como lo haría el endpoint
        response_data = {
            "exito": True,
            "respuesta_usuario": respuesta_enriquecida,
            "intencion_detectada": query_intent,
            "tipo": "respuesta_enriquecida_semantica",
            "interacciones": memoria_previa["interacciones_recientes"],
            "total": memoria_previa["total_interacciones"],
            "mensaje": f"🧠 RESUMEN DE ACTIVIDAD ANTERIOR\n\n{respuesta_enriquecida}\n\n---\n💡 Contexto disponible"
        }
        
        print("\n📦 ESTRUCTURA FINAL:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False)[:1000] + "...")
        
        # Validaciones críticas
        assert response_data["respuesta_usuario"] != ""
        assert response_data["intencion_detectada"] != "general"
        assert "respuesta_usuario" in response_data
        assert len(response_data["respuesta_usuario"]) > 100
        
        print("\n✅ TEST 4 PASSED")
        print(f"\n🎯 CAMPO PRINCIPAL: respuesta_usuario ({len(response_data['respuesta_usuario'])} chars)")
        print(f"🎯 INTENCIÓN: {response_data['intencion_detectada']}")
        
        return True
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "=" * 60)
    print("VALIDACION LOCAL DE HISTORIAL_INTERACCIONES")
    print("=" * 60)
    
    results = []
    results.append(test_detect_query_intent())
    results.append(test_generate_historical_response())
    results.append(test_enhance_response())
    results.append(test_full_response_structure())
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ TODOS LOS TESTS PASARON - El flujo está correcto")
        print("🚀 Puedes hacer 'func start' con confianza")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - Revisar implementación")
        sys.exit(1)
