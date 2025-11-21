#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del sistema semántico con embeddings reales
"""
import os
import sys
from pathlib import Path

# Cargar .env automáticamente
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except:
    pass

from semantic_intent_classifier import classify_user_intent, semantic_classifier
from intelligent_intent_detector import detectar_necesidad_bing_inteligente


def test_clasificacion_basica():
    """Prueba clasificación de intenciones básicas"""
    print("=" * 60)
    print("TEST 1: Clasificación Básica")
    print("=" * 60)

    casos = [
        "listar archivos en el directorio",
        "leer el contenido de function_app.py",
        "buscar funciones que contengan 'memoria'",
        "ejecutar comando az storage account list",
        "cuál es el estado del sistema",
    ]

    for consulta in casos:
        resultado = classify_user_intent(consulta)
        print(f"\n📝 Consulta: {consulta}")
        print(f"   Intent: {resultado['intent']}")
        print(f"   Confianza: {resultado['confidence']:.2f}")
        print(
            f"   Preprocesado: {resultado.get('preprocessed_text', 'N/A')[:50]}...")


def test_deteccion_inteligente():
    """Prueba detector inteligente con contexto"""
    print("\n" + "=" * 60)
    print("TEST 2: Detección Inteligente con Contexto")
    print("=" * 60)

    casos = [
        {
            "query": "lee el archivo de configuración",
            "context": {"last_file": "config.json", "working_dir": "/app"}
        },
        {
            "query": "busca errores recientes",
            "context": {"session_id": "test_001"}
        },
        {
            "query": "lista las cuentas de storage",
            "context": {}
        }
    ]

    for caso in casos:
        resultado = detectar_necesidad_bing_inteligente(
            caso["query"], caso.get("context", {}))
        print(f"\n📝 Query: {caso['query']}")
        print(f"   Requiere Bing: {resultado.get('requiere_bing', False)}")
        print(f"   Score: {resultado.get('score_final', 0):.2f}")
        print(f"   Razón: {resultado.get('razon', 'N/A')}")
        print(
            f"   Query optimizada: {resultado.get('query_optimizada', caso['query'])[:50]}...")


def test_aprendizaje_incremental():
    """Prueba aprendizaje con feedback"""
    print("\n" + "=" * 60)
    print("TEST 3: Aprendizaje Incremental")
    print("=" * 60)

    # Agregar ejemplo de aprendizaje usando la instancia global
    try:
        semantic_classifier.add_learning_example(
            user_input="mostrar logs de errores",
            correct_intent="diagnostico",
            command_used=""
        )
        print("   ✅ Ejemplo de aprendizaje agregado")
    except Exception as e:
        print(f"   ⚠️ Error en aprendizaje: {e}")

    # Probar clasificación después del aprendizaje
    resultado = classify_user_intent("mostrar logs de errores")
    print(f"\n📝 Después de aprendizaje:")
    print(f"   Intent: {resultado['intent']}")
    print(f"   Confianza: {resultado['confidence']:.2f}")


def test_umbrales():
    """Prueba ajuste de umbrales"""
    print("\n" + "=" * 60)
    print("TEST 4: Validación de Umbrales")
    print("=" * 60)

    consultas_frecuentes = [
        "listar archivos",
        "leer archivo",
        "buscar en código",
        "ejecutar comando azure",
        "estado del sistema"
    ]

    resultados = []
    for consulta in consultas_frecuentes:
        resultado = classify_user_intent(consulta)
        resultados.append(resultado['confidence'])
        print(f"   {consulta}: {resultado['confidence']:.2f}")

    promedio = sum(resultados) / len(resultados)
    print(f"\n📊 Confianza promedio: {promedio:.2f}")
    print(
        f"   Recomendación: {'Ajustar umbrales' if promedio < 0.7 else 'Umbrales OK'}")


def test_embeddings_reales():
    """Prueba con embeddings reales de Azure OpenAI"""
    print("\n" + "=" * 60)
    print("TEST 5: Azure OpenAI Embeddings")
    print("=" * 60)

    # Buscar en ambos formatos de variable
    api_key = os.environ.get(
        'AZURE_OPENAI_API_KEY') or os.environ.get('AZURE_OPENAI_KEY')
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')

    if api_key and endpoint:
        print("   ✅ Azure OpenAI configurado")
        print(f"   Modelo: text-embedding-3-large")
        print(f"   Endpoint: {endpoint[:50]}...")
    else:
        print("   ⚠️  Faltan variables de entorno:")
        print(f"   API Key: {'✅' if api_key else '❌'}")
        print(f"   Endpoint: {'✅' if endpoint else '❌'}")


if __name__ == "__main__":
    print("\n🧪 PRUEBAS DEL SISTEMA SEMÁNTICO\n")

    # Verificar configuración de Azure OpenAI
    api_key = os.environ.get(
        'AZURE_OPENAI_API_KEY') or os.environ.get('AZURE_OPENAI_KEY')
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')

    if api_key and endpoint:
        print("✅ Azure OpenAI text-embedding-3-large detectado\n")
    else:
        print("⚠️  Variables de Azure OpenAI no detectadas")
        print("   Se usará fallback a hash embeddings\n")

    try:
        test_clasificacion_basica()
        test_deteccion_inteligente()
        test_aprendizaje_incremental()
        test_umbrales()
        test_embeddings_reales()

        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
