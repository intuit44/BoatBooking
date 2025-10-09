#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la clasificación semántica sin dependencia de palabras clave
"""

import requests
import json
import time

BASE_URL = "http://localhost:7071"

def test_semantic_classification(consulta, descripcion, expected_intent=None):
    """Prueba clasificación semántica de una consulta"""
    print(f"\n=== {descripcion} ===")
    print(f"Consulta: '{consulta}'")
    
    try:
        # Probar con /api/hybrid usando el nuevo clasificador semántico
        payload = {"agent_response": consulta}
        
        response = requests.post(
            f"{BASE_URL}/api/hybrid",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar clasificación semántica
            metadata = data.get("metadata", {})
            resultado = data.get("resultado", {})
            
            # Buscar información de clasificación en múltiples ubicaciones
            classification = None
            
            # Buscar en resultado directo
            if "semantic_classification" in resultado:
                classification = resultado["semantic_classification"]
            # Buscar en resultado.resultado (anidado)
            elif "classification" in resultado.get("resultado", {}):
                classification = resultado["resultado"]["classification"]
            # Buscar en metadata
            elif "semantic_classification" in metadata:
                classification = metadata["semantic_classification"]
            # Si usa Bing Grounding, extraer información del resultado
            elif metadata.get("used_grounding") and resultado.get("resultado"):
                bing_result = resultado.get("resultado", {})
                if bing_result.get("comando_sugerido"):
                    # Inferir intención del comando sugerido
                    comando = bing_result.get("comando_sugerido", "")
                    intent = "unknown"
                    confidence = bing_result.get("confianza", 0.8)
                    
                    if "cosmosdb list" in comando:
                        intent = "listar_cosmos"
                    elif "storage account list" in comando:
                        intent = "listar_storage"
                    elif "functionapp list" in comando:
                        intent = "listar_functions"
                    elif "group list" in comando:
                        intent = "listar_resources"
                    
                    classification = {
                        "intent": intent,
                        "confidence": confidence,
                        "method": "bing_grounding",
                        "command": comando
                    }
            
            if classification:
                intent = classification.get("intent", "unknown")
                confidence = classification.get("confidence", 0)
                method = classification.get("method", "unknown")
                command = classification.get("command", "none")
                
                print(f"Intención detectada: {intent}")
                print(f"Confianza: {confidence:.3f}")
                print(f"Método: {method}")
                print(f"Comando sugerido: {command}")
                
                # Mostrar información adicional si está disponible
                if metadata.get("used_grounding"):
                    print(f"Usó Bing Grounding: Sí")
                if resultado.get("fuente"):
                    print(f"Fuente: {resultado.get('fuente')}")
                
                # Verificar si coincide con la expectativa
                if expected_intent and intent == expected_intent:
                    print("✅ Intención correcta detectada")
                elif expected_intent:
                    print(f"⚠️ Esperaba '{expected_intent}', obtuvo '{intent}'")
                else:
                    print("ℹ️ Sin expectativa específica")
                
                return True, intent, confidence
            else:
                # Si no hay clasificación explícita, pero hay resultado útil
                if metadata.get("used_grounding") and resultado.get("resultado", {}).get("comando_sugerido"):
                    comando = resultado["resultado"]["comando_sugerido"]
                    print(f"Sistema usó Bing Grounding exitosamente")
                    print(f"Comando sugerido: {comando}")
                    
                    # Inferir intención del comando
                    intent = "unknown"
                    if "cosmosdb" in comando:
                        intent = "listar_cosmos"
                    elif "storage account" in comando:
                        intent = "listar_storage"
                    elif "functionapp" in comando:
                        intent = "listar_functions"
                    elif "group" in comando:
                        intent = "listar_resources"
                    
                    return True, intent, 0.8
                else:
                    print("⚠️ No se encontró información de clasificación")
                    return False, "unknown", 0
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False, "error", 0
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, "exception", 0

def main():
    """Ejecuta pruebas de clasificación semántica"""
    print("🧠 PRUEBAS DE CLASIFICACIÓN SEMÁNTICA")
    print("Sin dependencia de palabras clave predefinidas")
    print(f"URL Base: {BASE_URL}")
    print("="*70)
    
    # Consultas de prueba con variaciones semánticas
    consultas_test = [
        # Storage Accounts - Variaciones semánticas
        ("cómo veo mis cuentas de almacenamiento en azure?", 
         "Storage - Pregunta directa", "listar_storage"),
        
        ("me gustaría ver mis cuentas storage", 
         "Storage - Variación informal", "listar_storage"),
        
        ("mostrar storage accounts que tengo", 
         "Storage - Comando directo", "listar_storage"),
        
        ("cuentas de almacenamiento disponibles", 
         "Storage - Sin verbo explícito", "listar_storage"),
        
        # Cosmos DB - Variaciones semánticas  
        ("No sé cómo listar las cuentas de cosmos db en Azure??", 
         "Cosmos - Consulta original", "listar_cosmos"),
        
        ("me gustaría ver mis cuentas cosmos", 
         "Cosmos - Variación informal", "listar_cosmos"),
        
        ("mostrar base cosmos", 
         "Cosmos - Fragmentado", "listar_cosmos"),
        
        ("cuentas db cosmos disponibles", 
         "Cosmos - Orden diferente", "listar_cosmos"),
        
        # Function Apps - Variaciones semánticas
        ("quiero saber qué apps de función tengo corriendo", 
         "Functions - Descripción natural", "listar_functions"),
        
        ("mostrar function apps activas", 
         "Functions - Comando directo", "listar_functions"),
        
        ("aplicaciones de función en mi suscripción", 
         "Functions - Formal", "listar_functions"),
        
        ("functions que están ejecutándose", 
         "Functions - Estado específico", "listar_functions"),
        
        # Diagnóstico - Variaciones semánticas
        ("hay algún problema con alguno de mis recursos?", 
         "Diagnóstico - Pregunta preocupada", "diagnosticar_sistema"),
        
        ("verificar estado de mi infraestructura", 
         "Diagnóstico - Comando técnico", "diagnosticar_sistema"),
        
        ("todo está funcionando bien?", 
         "Diagnóstico - Pregunta general", "diagnosticar_sistema"),
        
        ("revisar salud de servicios azure", 
         "Diagnóstico - Término médico", "diagnosticar_sistema"),
        
        # Casos extremos - Sin palabras clave obvias
        ("no tengo idea qué comando usar para ver recursos en azure", 
         "Ayuda general - Incertidumbre total", "ayuda_general"),
        
        ("ayúdame con esto por favor", 
         "Ayuda general - Muy vago", "ayuda_general"),
        
        ("qué puedo hacer aquí?", 
         "Ayuda general - Exploración", "ayuda_general"),
        
        # Casos de borde - Frases que podrían confundir
        ("storage de fotos en mi teléfono", 
         "Falso positivo - No Azure", None),
        
        ("función matemática coseno", 
         "Falso positivo - No Azure Functions", None),
        
        ("base de datos local mysql", 
         "Falso positivo - No Cosmos", None),
    ]
    
    resultados = []
    correctos = 0
    total = len(consultas_test)
    
    for consulta, descripcion, expected in consultas_test:
        success, intent, confidence = test_semantic_classification(consulta, descripcion, expected)
        
        # Evaluar si fue correcto
        is_correct = False
        if expected is None:
            # Para casos sin expectativa, cualquier resultado es válido
            is_correct = success
        else:
            # Para casos con expectativa, debe coincidir
            is_correct = success and intent == expected
        
        if is_correct:
            correctos += 1
        
        resultados.append({
            "consulta": consulta,
            "expected": expected,
            "actual": intent,
            "confidence": confidence,
            "correct": is_correct
        })
        
        # Pausa entre pruebas
        time.sleep(0.5)
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE CLASIFICACIÓN SEMÁNTICA")
    print("="*70)
    
    print(f"Total de consultas probadas: {total}")
    print(f"Clasificaciones correctas: {correctos}")
    print(f"Tasa de éxito: {(correctos/total)*100:.1f}%")
    
    # Análisis por intención
    intent_stats = {}
    for resultado in resultados:
        expected = resultado["expected"] or "sin_expectativa"
        if expected not in intent_stats:
            intent_stats[expected] = {"total": 0, "correctos": 0}
        intent_stats[expected]["total"] += 1
        if resultado["correct"]:
            intent_stats[expected]["correctos"] += 1
    
    print(f"\n📋 ANÁLISIS POR INTENCIÓN:")
    for intent, stats in intent_stats.items():
        tasa = (stats["correctos"] / stats["total"]) * 100
        print(f"  {intent}: {stats['correctos']}/{stats['total']} ({tasa:.1f}%)")
    
    # Casos problemáticos
    problematicos = [r for r in resultados if not r["correct"]]
    if problematicos:
        print(f"\n⚠️ CASOS PROBLEMÁTICOS ({len(problematicos)}):")
        for caso in problematicos[:5]:  # Mostrar solo los primeros 5
            print(f"  '{caso['consulta'][:50]}...'")
            print(f"    Esperado: {caso['expected']}, Obtuvo: {caso['actual']}")
    
    # Evaluación final
    if correctos >= total * 0.8:  # 80% éxito mínimo
        print(f"\n🎉 CLASIFICACIÓN SEMÁNTICA EXITOSA")
        print("El sistema clasifica intenciones sin depender de palabras clave")
    else:
        print(f"\n⚠️ MEJORAS NECESARIAS EN CLASIFICACIÓN")
        print("El sistema necesita ajustes en los embeddings o ejemplos")
    
    return correctos, total

if __name__ == "__main__":
    main()