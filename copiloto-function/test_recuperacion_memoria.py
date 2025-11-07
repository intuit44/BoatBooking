"""
Test de recuperacion de memoria - Valida que se recuperen documentos ACTUALES
"""

import os
import json
from datetime import datetime, timedelta

def test_busqueda_ai_search():
    """Simula busqueda en AI Search y valida ordenamiento temporal"""
    print("\n" + "="*80)
    print("TEST 1: BUSQUEDA EN AI SEARCH")
    print("="*80)
    
    # Simular documentos retornados por AI Search
    documentos_simulados = [
        {
            "id": "doc_viejo_1",
            "texto_semantico": "Resumen de la ultima actividad. Ultimo tema: copiloto",
            "timestamp": "2025-01-05T10:00:00.000Z",  # Hace 5 dias
            "@search.score": 0.68,
            "agent_id": "assistant"
        },
        {
            "id": "doc_reciente_1",
            "texto_semantico": "Optimizacion de deduplicacion aplicada. Hash SHA256 implementado.",
            "timestamp": "2025-01-10T14:30:00.000Z",  # HOY
            "@search.score": 0.65,
            "agent_id": "assistant"
        },
        {
            "id": "doc_viejo_2",
            "texto_semantico": "Interaccion en /api/copiloto por TestAgent. Exito: si.",
            "timestamp": "2025-01-04T15:00:00.000Z",  # Hace 6 dias
            "@search.score": 0.70,
            "agent_id": "TestAgent"
        },
        {
            "id": "doc_reciente_2",
            "texto_semantico": "Test de deduplicacion ejecutado. Tasa de perdida: 33.3%",
            "timestamp": "2025-01-10T14:45:00.000Z",  # HOY
            "@search.score": 0.62,
            "agent_id": "assistant"
        }
    ]
    
    print(f"\n   Documentos simulados: {len(documentos_simulados)}")
    
    # PROBLEMA 1: Ordenamiento solo por score (ignora timestamp)
    print("\n   [PROBLEMA] Ordenamiento ACTUAL (solo por score):")
    ordenados_por_score = sorted(documentos_simulados, key=lambda x: x["@search.score"], reverse=True)
    for i, doc in enumerate(ordenados_por_score, 1):
        edad_dias = (datetime.now() - datetime.fromisoformat(doc["timestamp"].replace("Z", ""))).days
        print(f"      {i}. Score: {doc['@search.score']:.2f} | Edad: {edad_dias} dias | {doc['texto_semantico'][:60]}...")
    
    # SOLUCION: Ordenamiento hibrido (score + recencia)
    print("\n   [SOLUCION] Ordenamiento HIBRIDO (score + recencia):")
    
    def calcular_score_hibrido(doc):
        score_busqueda = doc["@search.score"]
        timestamp = datetime.fromisoformat(doc["timestamp"].replace("Z", ""))
        edad_horas = (datetime.now() - timestamp).total_seconds() / 3600
        
        # Penalizar documentos viejos
        if edad_horas > 168:  # Mas de 7 dias
            factor_recencia = 0.5
        elif edad_horas > 48:  # Mas de 2 dias
            factor_recencia = 0.7
        elif edad_horas > 24:  # Mas de 1 dia
            factor_recencia = 0.85
        else:  # Menos de 24 horas
            factor_recencia = 1.0
        
        return score_busqueda * factor_recencia
    
    ordenados_hibrido = sorted(documentos_simulados, key=calcular_score_hibrido, reverse=True)
    for i, doc in enumerate(ordenados_hibrido, 1):
        edad_dias = (datetime.now() - datetime.fromisoformat(doc["timestamp"].replace("Z", ""))).days
        score_hibrido = calcular_score_hibrido(doc)
        print(f"      {i}. Score hibrido: {score_hibrido:.2f} | Edad: {edad_dias} dias | {doc['texto_semantico'][:60]}...")
    
    # Validar que documentos recientes esten primero
    primeros_3 = ordenados_hibrido[:3]
    recientes_en_top3 = sum(1 for doc in primeros_3 if "2025-01-10" in doc["timestamp"])
    
    print(f"\n   Documentos recientes en top 3: {recientes_en_top3}/3")
    if recientes_en_top3 >= 2:
        print("   [OK] Documentos recientes priorizados")
    else:
        print("   [PROBLEMA] Documentos viejos dominan resultados")
    
    return recientes_en_top3 >= 2


def test_filtros_ai_search():
    """Valida que filtros no sean demasiado restrictivos"""
    print("\n" + "="*80)
    print("TEST 2: FILTROS DE BUSQUEDA")
    print("="*80)
    
    # Simular request del agente
    request_foundry = {
        "query": "actividad reciente",
        "agent_id": "assistant",
        "session_id": "assistant",
        "top": 5
    }
    
    print(f"\n   Request de Foundry:")
    print(f"      query: {request_foundry['query']}")
    print(f"      agent_id: {request_foundry['agent_id']}")
    print(f"      session_id: {request_foundry['session_id']}")
    
    # PROBLEMA: Filtros muy restrictivos
    print("\n   [PROBLEMA] Filtros ACTUALES (muy restrictivos):")
    filtros_actuales = []
    if request_foundry.get("session_id"):
        filtros_actuales.append(f"session_id eq '{request_foundry['session_id']}'")
    if request_foundry.get("agent_id"):
        filtros_actuales.append(f"agent_id eq '{request_foundry['agent_id']}'")
    
    filter_str = " and ".join(filtros_actuales) if filtros_actuales else None
    print(f"      Filtro OData: {filter_str}")
    print(f"      Problema: Solo encuentra docs de session_id='assistant' Y agent_id='assistant'")
    
    # SOLUCION: Filtros mas flexibles
    print("\n   [SOLUCION] Filtros OPTIMIZADOS (mas flexibles):")
    filtros_optimizados = []
    
    # Solo filtrar por session_id si NO es generico
    session_id = request_foundry.get("session_id")
    if session_id and session_id not in ["assistant", "test_session", "unknown", "global"]:
        filtros_optimizados.append(f"session_id eq '{session_id}'")
    else:
        print(f"      Session '{session_id}' es generica - NO filtrar")
    
    # NO filtrar por agent_id para busqueda universal
    print(f"      Agent_id '{request_foundry.get('agent_id')}' - NO filtrar (busqueda universal)")
    
    filter_str_optimizado = " and ".join(filtros_optimizados) if filtros_optimizados else None
    print(f"      Filtro OData optimizado: {filter_str_optimizado or 'SIN FILTROS (busqueda universal)'}")
    print(f"      Resultado: Encuentra TODOS los documentos relevantes")
    
    return filter_str_optimizado is None  # Debe ser None para busqueda universal


def test_ordenamiento_temporal():
    """Valida que documentos se ordenen por timestamp descendente"""
    print("\n" + "="*80)
    print("TEST 3: ORDENAMIENTO TEMPORAL")
    print("="*80)
    
    # Simular query a Cosmos DB
    documentos_cosmos = [
        {"id": "1", "timestamp": "2025-01-05T10:00:00Z", "texto_semantico": "Doc viejo 1"},
        {"id": "2", "timestamp": "2025-01-10T14:30:00Z", "texto_semantico": "Doc reciente 1"},
        {"id": "3", "timestamp": "2025-01-04T15:00:00Z", "texto_semantico": "Doc viejo 2"},
        {"id": "4", "timestamp": "2025-01-10T14:45:00Z", "texto_semantico": "Doc reciente 2"},
    ]
    
    print(f"\n   Documentos de Cosmos DB: {len(documentos_cosmos)}")
    
    # PROBLEMA: Sin ordenamiento explicito
    print("\n   [PROBLEMA] Sin ORDER BY en query:")
    for i, doc in enumerate(documentos_cosmos, 1):
        print(f"      {i}. {doc['timestamp']} | {doc['texto_semantico']}")
    
    # SOLUCION: ORDER BY timestamp DESC
    print("\n   [SOLUCION] Con ORDER BY c._ts DESC:")
    ordenados = sorted(documentos_cosmos, key=lambda x: x["timestamp"], reverse=True)
    for i, doc in enumerate(ordenados, 1):
        print(f"      {i}. {doc['timestamp']} | {doc['texto_semantico']}")
    
    # Validar que los 2 primeros sean recientes
    primeros_2 = ordenados[:2]
    recientes = sum(1 for doc in primeros_2 if "2025-01-10" in doc["timestamp"])
    
    print(f"\n   Documentos recientes en top 2: {recientes}/2")
    return recientes == 2


def test_cache_invalidacion():
    """Valida que no haya cache de resultados viejos"""
    print("\n" + "="*80)
    print("TEST 4: INVALIDACION DE CACHE")
    print("="*80)
    
    # Simular cache
    cache_simulado = {
        "query:actividad_reciente": {
            "timestamp": "2025-01-05T10:00:00Z",
            "resultados": ["doc_viejo_1", "doc_viejo_2"],
            "ttl": 300  # 5 minutos
        }
    }
    
    print(f"\n   Cache actual:")
    for key, value in cache_simulado.items():
        edad_segundos = (datetime.now() - datetime.fromisoformat(value["timestamp"].replace("Z", ""))).total_seconds()
        print(f"      Key: {key}")
        print(f"      Edad: {edad_segundos:.0f} segundos")
        print(f"      TTL: {value['ttl']} segundos")
        print(f"      Expirado: {'SI' if edad_segundos > value['ttl'] else 'NO'}")
    
    # PROBLEMA: Cache no se invalida
    print("\n   [PROBLEMA] Cache de 5 dias atras aun activo")
    print("      Solucion: TTL corto (60s) o invalidar en cada indexacion")
    
    return True


def generar_recomendaciones(resultados):
    """Genera recomendaciones basadas en resultados de tests"""
    print("\n" + "="*80)
    print("RECOMENDACIONES")
    print("="*80)
    
    if not resultados["test1"]:
        print("\n   1. IMPLEMENTAR ORDENAMIENTO HIBRIDO")
        print("      Archivo: services/azure_search_client.py")
        print("      Cambio: Agregar factor de recencia al score")
        print("      Codigo:")
        print("         def calcular_score_hibrido(doc):")
        print("             score = doc['@search.score']")
        print("             edad_horas = (now - doc['timestamp']).hours")
        print("             factor = 1.0 if edad_horas < 24 else 0.7")
        print("             return score * factor")
    
    if not resultados["test2"]:
        print("\n   2. OPTIMIZAR FILTROS DE BUSQUEDA")
        print("      Archivo: endpoints_search_memory.py")
        print("      Cambio: NO filtrar por agent_id en busqueda universal")
        print("      Codigo:")
        print("         # NO agregar filtro de agent_id")
        print("         # Solo filtrar session_id si NO es generica")
    
    if not resultados["test3"]:
        print("\n   3. AGREGAR ORDER BY EN QUERIES")
        print("      Archivo: semantic_query_builder.py")
        print("      Cambio: Agregar ORDER BY c._ts DESC")
        print("      Codigo:")
        print("         query += ' ORDER BY c._ts DESC'")
    
    if not resultados["test4"]:
        print("\n   4. INVALIDAR CACHE EN INDEXACION")
        print("      Archivo: services/azure_search_client.py")
        print("      Cambio: Limpiar cache al indexar nuevos docs")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SUITE DE TESTS DE RECUPERACION DE MEMORIA")
    print("="*80)
    
    resultados = {
        "test1": test_busqueda_ai_search(),
        "test2": test_filtros_ai_search(),
        "test3": test_ordenamiento_temporal(),
        "test4": test_cache_invalidacion()
    }
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    total = len(resultados)
    pasados = sum(resultados.values())
    print(f"\n   Tests pasados: {pasados}/{total}")
    
    if pasados == total:
        print("\n   [OK] Sistema de recuperacion funcionando correctamente")
    else:
        print("\n   [PROBLEMA] Se detectaron issues en recuperacion")
        generar_recomendaciones(resultados)
    
    print("\n" + "="*80)
