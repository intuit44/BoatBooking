#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para identificar campos necesarios en buscar-memoria 
para respuestas semánticas coherentes del LLM
"""

import json
import requests
import time
from typing import Dict, Any, List

# Configuración
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/buscar-memoria"


def hacer_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Hacer request al endpoint y manejar respuesta"""
    try:
        print(f"\n🔄 Enviando: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"📊 Status Code: {response.status_code}")

        try:
            result = response.json()
        except:
            result = {"error": "No JSON response", "text": response.text[:500]}

        return {
            "status_code": response.status_code,
            "payload_enviado": payload,
            "response": result,
            "headers": dict(response.headers)
        }

    except Exception as e:
        return {
            "status_code": 0,
            "payload_enviado": payload,
            "response": {"error": f"Request failed: {str(e)}"},
            "headers": {}
        }


def analizar_calidad_respuesta(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analizar qué tan buena es la respuesta para un LLM"""

    if not response_data.get("response", {}).get("exito"):
        return {
            "calidad": "ERROR",
            "puntuacion": 0,
            "problemas": ["Request falló"],
            "campos_utiles": [],
            "narrativa_posible": False,
            "total_documentos": 0,
            "contexto_rico": 0
        }

    resp = response_data["response"]
    problemas = []
    campos_utiles = []
    puntuacion = 0

    # 1. ¿Hay documentos?
    documentos = resp.get("documentos", [])
    if not documentos:
        problemas.append("Sin documentos recuperados")
    else:
        puntuacion += 20
        campos_utiles.append("documentos")

    # 2. ¿Los documentos tienen contexto narrativo?
    contexto_rico = 0
    for doc in documentos[:3]:  # Revisar primeros 3
        if doc.get("texto_semantico") and len(doc.get("texto_semantico", "")) > 10:
            contexto_rico += 1
        if doc.get("contexto_conversacional"):
            contexto_rico += 1
        if doc.get("respuesta_usuario"):
            contexto_rico += 1
        if doc.get("temas_principales"):
            contexto_rico += 1

    if contexto_rico > 0:
        puntuacion += min(30, contexto_rico * 5)
        campos_utiles.extend(
            ["texto_semantico", "contexto_conversacional", "respuesta_usuario"])
    else:
        problemas.append("Documentos sin contexto conversacional rico")

    # 3. ¿Hay metadatos temporales y de sesión?
    metadata = resp.get("metadata", {})
    if metadata.get("session_id") and metadata.get("agent_id"):
        puntuacion += 15
        campos_utiles.extend(["session_id", "agent_id"])
    else:
        problemas.append("Sin identificadores de sesión coherentes")

    # 4. ¿Hay resumen o contexto inteligente?
    if resp.get("contexto_inteligente", {}).get("resumen"):
        puntuacion += 20
        campos_utiles.append("contexto_inteligente")
    elif resp.get("resumen_conversacion"):
        puntuacion += 15
        campos_utiles.append("resumen_conversacion")
    else:
        problemas.append("Sin resumen o contexto inteligente")

    # 5. ¿Hay información de continuidad?
    if resp.get("detalles_operacion", {}).get("total", 0) > 0:
        puntuacion += 10
        campos_utiles.append("detalles_operacion")

    # 6. ¿Los timestamps permiten narrativa temporal?
    timestamps_validos = 0
    for doc in documentos[:5]:
        if doc.get("timestamp"):
            timestamps_validos += 1

    if timestamps_validos > 2:
        puntuacion += 5
        campos_utiles.append("timestamp")

    # Determinar calidad general
    if puntuacion >= 70:
        calidad = "EXCELENTE"
    elif puntuacion >= 50:
        calidad = "BUENA"
    elif puntuacion >= 30:
        calidad = "REGULAR"
    else:
        calidad = "POBRE"

    narrativa_posible = puntuacion >= 40

    return {
        "calidad": calidad,
        "puntuacion": puntuacion,
        "problemas": problemas,
        "campos_utiles": list(set(campos_utiles)),
        "narrativa_posible": narrativa_posible,
        "total_documentos": len(documentos),
        "contexto_rico": contexto_rico
    }


def test_version_foundry_actual():
    """Test de la versión que envía Foundry (query vacía)"""
    print("\n" + "="*60)
    print("🤖 TEST 1: VERSIÓN FOUNDRY ACTUAL (Query Vacía)")
    print("="*60)

    payload = {"query": "", "top": 10}
    resultado = hacer_request(payload)
    analisis = analizar_calidad_respuesta(resultado)

    print(f"\n📈 ANÁLISIS DE CALIDAD:")
    print(f"   Calidad: {analisis['calidad']} ({analisis['puntuacion']}/100)")
    print(f"   ¿Narrativa posible?: {analisis['narrativa_posible']}")
    print(f"   Documentos: {analisis['total_documentos']}")
    print(f"   Contexto rico: {analisis['contexto_rico']}")

    if analisis['problemas']:
        print(f"\n❌ PROBLEMAS:")
        for problema in analisis['problemas']:
            print(f"   • {problema}")

    if analisis['campos_utiles']:
        print(f"\n✅ CAMPOS ÚTILES ENCONTRADOS:")
        for campo in analisis['campos_utiles']:
            print(f"   • {campo}")

    return resultado, analisis


def test_version_mejorada():
    """Test con campos que deberían mejorar la respuesta"""
    print("\n" + "="*60)
    print("🚀 TEST 2: VERSIÓN MEJORADA (Campos Completos)")
    print("="*60)

    payload = {
        "query": "estado del wrapper y correcciones recientes",
        "agent_id": "GlobalAgent",
        "session_id": "temp_test_coherente",
        "tipo": "correccion",  # Filtrar por tipo
        "include_context": True,  # Solicitar contexto
        "include_narrative": True,  # Solicitar narrativa
        "top": 10,
        "format": "conversational"  # Formato conversacional
    }

    resultado = hacer_request(payload)
    analisis = analizar_calidad_respuesta(resultado)

    print(f"\n📈 ANÁLISIS DE CALIDAD:")
    print(f"   Calidad: {analisis['calidad']} ({analisis['puntuacion']}/100)")
    print(f"   ¿Narrativa posible?: {analisis['narrativa_posible']}")
    print(f"   Documentos: {analisis['total_documentos']}")
    print(f"   Contexto rico: {analisis['contexto_rico']}")

    if analisis['problemas']:
        print(f"\n❌ PROBLEMAS:")
        for problema in analisis['problemas']:
            print(f"   • {problema}")

    if analisis['campos_utiles']:
        print(f"\n✅ CAMPOS ÚTILES ENCONTRADOS:")
        for campo in analisis['campos_utiles']:
            print(f"   • {campo}")

    # Mostrar muestra de documentos
    documentos = resultado.get("response", {}).get("documentos", [])
    if documentos:
        print(f"\n📄 MUESTRA DE DOCUMENTOS RECUPERADOS:")
        for i, doc in enumerate(documentos[:3]):
            print(f"\n   📌 Documento {i+1}:")
            print(f"      Texto: {doc.get('texto_semantico', 'N/A')[:80]}...")
            print(
                f"      Contexto: {doc.get('contexto_conversacional', 'N/A')[:60]}...")
            print(f"      Agente: {doc.get('agent_id', 'N/A')}")
            print(f"      Timestamp: {doc.get('timestamp', 'N/A')}")
            print(f"      Tipo: {doc.get('tipo_interaccion', 'N/A')}")

    return resultado, analisis


def generar_respuesta_llm_simulada(documentos: List[Dict], metadata: Dict) -> str:
    """Simular cómo respondería un LLM con estos datos"""

    if not documentos:
        return "❌ No se encontró información relevante en el historial."

    # Agrupar por tipo de interacción
    correcciones = [d for d in documentos if d.get(
        'tipo_interaccion') == 'correccion']
    consultas = [d for d in documentos if d.get(
        'tipo_interaccion') == 'user_input']

    respuesta = []

    # Contexto temporal
    if metadata.get('session_id') and metadata.get('agent_id'):
        respuesta.append(
            f"📊 **Resumen de Actividad ({metadata['agent_id']}):**")

    # Análisis de correcciones
    if correcciones:
        respuesta.append(
            f"\n🔧 **Correcciones Realizadas ({len(correcciones)}):**")
        for i, corr in enumerate(correcciones[:3]):
            texto = corr.get('texto_semantico', '')
            timestamp = corr.get('timestamp', '')[:10] if corr.get(
                'timestamp') else 'Sin fecha'
            respuesta.append(f"   {i+1}. {texto} ({timestamp})")

    # Análisis de consultas recientes
    if consultas:
        respuesta.append(f"\n💬 **Consultas Recientes ({len(consultas)}):**")
        for i, cons in enumerate(consultas[:3]):
            texto = cons.get('texto_semantico', '')
            respuesta.append(f"   • {texto}")

    # Contexto inteligente si existe
    contexto = metadata.get('contexto_inteligente', {})
    if contexto.get('resumen'):
        respuesta.append(f"\n🧠 **Contexto:** {contexto['resumen']}")

    return "\n".join(respuesta) if respuesta else "❌ Datos insuficientes para generar narrativa."


def comparar_versiones():
    """Comparar ambas versiones y generar recomendaciones"""
    print("\n" + "="*80)
    print("📊 COMPARACIÓN Y RECOMENDACIONES")
    print("="*80)

    # Ejecutar tests
    resultado1, analisis1 = test_version_foundry_actual()
    time.sleep(1)  # Evitar rate limiting
    resultado2, analisis2 = test_version_mejorada()

    print(f"\n📈 COMPARACIÓN DE PUNTUACIONES:")
    print(
        f"   Foundry Actual:  {analisis1['puntuacion']}/100 ({analisis1['calidad']})")
    print(
        f"   Versión Mejorada: {analisis2['puntuacion']}/100 ({analisis2['calidad']})")

    mejora = analisis2['puntuacion'] - analisis1['puntuacion']
    print(f"   Mejora: +{mejora} puntos")

    # Simular respuestas LLM
    print(f"\n🤖 SIMULACIÓN RESPUESTA LLM - VERSIÓN ACTUAL:")
    if resultado1['response'].get('documentos'):
        resp1 = generar_respuesta_llm_simulada(
            resultado1['response']['documentos'],
            resultado1['response'].get('metadata', {})
        )
        print(resp1)
    else:
        print("❌ Sin datos para generar respuesta")

    print(f"\n🚀 SIMULACIÓN RESPUESTA LLM - VERSIÓN MEJORADA:")
    if resultado2['response'].get('documentos'):
        resp2 = generar_respuesta_llm_simulada(
            resultado2['response']['documentos'],
            resultado2['response'].get('metadata', {})
        )
        print(resp2)
    else:
        print("❌ Sin datos para generar respuesta")

    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES PARA OPENAPI:")
    print("   1. Hacer 'query' opcional (no requerido)")
    print("   2. Agregar parámetros opcionales:")
    print("      • session_id: string")
    print("      • agent_id: string")
    print("      • tipo: string (enum: user_input, correccion, respuesta)")
    print("      • include_context: boolean")
    print("      • include_narrative: boolean")
    print("      • format: string (enum: raw, conversational)")
    print("   3. ⚠️  CRÍTICO: Endpoint debe responder SIEMPRE 200")
    print("   4. Enriquecer respuesta con campos narrativos")


if __name__ == "__main__":
    print("🧪 TEST DE CAMPOS NECESARIOS PARA RESPUESTA SEMÁNTICA LLM")
    print("Comparando versión actual vs. mejorada")

    try:
        comparar_versiones()

        print(f"\n✅ Test completado. Revisa los resultados para optimizar el endpoint.")

    except KeyboardInterrupt:
        print(f"\n❌ Test interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
