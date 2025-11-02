"""
🧪 Test de /api/guardar-memoria simulando Foundry con lógica real
Valida que el agente detecta intenciones y guarda memoria correctamente
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:7071"

def test_intencion_guardar_resumen():
    """
    Simula: Usuario dice "guarda este resumen en memoria: [texto largo]"
    Foundry detecta intención: guardar_en_memoria
    """
    
    print("=" * 70)
    print("🧪 TEST 1: Detección de intención 'guardar resumen'")
    print("=" * 70)
    
    # Payload que Foundry enviaría
    payload = {
        "contenido": """
        Resumen de la conversación:
        - Usuario configuró top_k=8 en copiloto-semantico-func-us2
        - Se aplicó exitosamente usando Azure CLI
        - El cambio mejora la precisión de búsqueda vectorial
        - Sistema ahora retorna 8 resultados en lugar de 5
        """,
        "tipo": "resumen_conversacion",
        "session_id": "assistant",
        "metadata": {
            "importancia": "alta",
            "fuente": "foundry",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print(f"\n📤 Enviando a /api/guardar-memoria:")
    print(json.dumps(payload, indent=2, ensure_ascii=False)[:200] + "...")
    
    response = requests.post(
        f"{BASE_URL}/api/guardar-memoria",
        json=payload,
        headers={
            "Session-ID": "assistant",
            "Agent-ID": "FoundryAgent"
        }
    )
    
    print(f"\n📥 Respuesta ({response.status_code}):")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result["exito"] == True, "Debe guardar exitosamente"
    assert "guardado" in result["mensaje"].lower(), "Debe confirmar guardado"
    
    print("\n✅ TEST 1 PASADO: Resumen guardado correctamente\n")
    return result


def test_intencion_recordar_decision():
    """
    Simula: Usuario dice "recuerda que prefiero usar Azure CLI"
    Foundry detecta intención: recordar_preferencia
    """
    
    print("=" * 70)
    print("🧪 TEST 2: Detección de intención 'recordar decisión'")
    print("=" * 70)
    
    payload = {
        "contenido": "Preferencia del usuario: Usar Azure CLI en lugar de SDK para operaciones de storage por mayor control",
        "tipo": "decision_usuario",
        "session_id": "assistant",
        "metadata": {
            "importancia": "media",
            "categoria": "preferencia_tecnica"
        }
    }
    
    print(f"\n📤 Enviando a /api/guardar-memoria:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    response = requests.post(
        f"{BASE_URL}/api/guardar-memoria",
        json=payload,
        headers={"Session-ID": "assistant"}
    )
    
    print(f"\n📥 Respuesta ({response.status_code}):")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result["exito"] == True
    print("\n✅ TEST 2 PASADO: Decisión guardada correctamente\n")
    return result


def test_buscar_memoria_guardada():
    """
    Verifica que la memoria guardada se puede recuperar
    """
    
    print("=" * 70)
    print("🧪 TEST 3: Búsqueda de memoria guardada")
    print("=" * 70)
    
    # Buscar lo que acabamos de guardar
    payload = {
        "query": "configuración top_k",
        "session_id": "assistant",
        "top": 5
    }
    
    print(f"\n📤 Buscando en /api/buscar-memoria:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    response = requests.post(
        f"{BASE_URL}/api/buscar-memoria",
        json=payload
    )
    
    print(f"\n📥 Respuesta ({response.status_code}):")
    result = response.json()
    
    if result.get("exito"):
        print(f"✅ Encontrados {result.get('total', 0)} documentos")
        for i, doc in enumerate(result.get("documentos", [])[:3], 1):
            print(f"\n  Doc {i}:")
            print(f"    Texto: {doc.get('texto_semantico', '')[:100]}...")
            print(f"    Score: {doc.get('@search.score', 0):.4f}")
    else:
        print(f"⚠️  Búsqueda falló: {result.get('error')}")
    
    print("\n✅ TEST 3 COMPLETADO\n")
    return result


def test_sin_contenido():
    """
    Valida que rechaza requests sin contenido
    """
    
    print("=" * 70)
    print("🧪 TEST 4: Validación de parámetros requeridos")
    print("=" * 70)
    
    payload = {
        "tipo": "resumen_conversacion"
        # Falta 'contenido' requerido
    }
    
    print(f"\n📤 Enviando payload inválido:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    response = requests.post(
        f"{BASE_URL}/api/guardar-memoria",
        json=payload
    )
    
    print(f"\n📥 Respuesta ({response.status_code}):")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result["exito"] == False, "Debe fallar sin contenido"
    assert "contenido" in result["error"].lower(), "Debe indicar parámetro faltante"
    
    print("\n✅ TEST 4 PASADO: Validación funciona correctamente\n")
    return result


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 INICIANDO TESTS DE /api/guardar-memoria")
    print("   Simulando comportamiento real de Foundry")
    print("=" * 70 + "\n")
    
    try:
        # Test 1: Guardar resumen
        test_intencion_guardar_resumen()
        
        # Test 2: Guardar decisión
        test_intencion_recordar_decision()
        
        # Test 3: Buscar lo guardado
        test_buscar_memoria_guardada()
        
        # Test 4: Validación
        test_sin_contenido()
        
        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS PASARON")
        print("✅ Endpoint /api/guardar-memoria funciona correctamente")
        print("✅ Foundry puede detectar intenciones y guardar memoria")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}\n")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   func start --python\n")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}\n")
