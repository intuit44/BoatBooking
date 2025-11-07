"""
🔍 Diagnóstico de Calidad de Memoria Semántica
Analiza datos en AI Search y Cosmos DB para detectar basura o mal guardado
"""

import os
import json
from datetime import datetime
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from collections import Counter

# ===== CONFIGURACIÓN =====
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://boatrentalcosmosdb.documents.azure.com:443/")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE_NAME", "MemoriaSemantica")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER_NAME", "Interacciones")

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://boatrentalsearch.search.windows.net")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "memoria-semantica-index")

# ===== MÉTRICAS DE CALIDAD =====
class MetricasCalidad:
    def __init__(self):
        self.total_docs = 0
        self.docs_vacios = 0
        self.docs_truncados = 0
        self.docs_sin_texto_semantico = 0
        self.docs_con_basura = 0
        self.docs_duplicados = 0
        self.docs_utiles = 0
        self.longitud_promedio = 0
        self.endpoints_mas_comunes = Counter()
        self.agentes_mas_activos = Counter()
        self.errores_encontrados = []
        self.ejemplos_basura = []
        self.ejemplos_buenos = []

# ===== DETECTORES DE BASURA =====
def es_basura(doc):
    """Detecta si un documento es basura o tiene bajo valor semántico"""
    razones = []
    
    # 1. Documento vacío o sin contenido útil
    texto_sem = doc.get("texto_semantico", "").strip()
    if not texto_sem or len(texto_sem) < 20:
        razones.append("texto_semantico muy corto o vacío")
    
    # 2. Mensajes genéricos sin valor
    mensajes_basura = [
        "Evento semantic",
        "unknown endpoint",
        "truncated",
        "status: ok",
        "success: true"
    ]
    if any(msg in texto_sem.lower() for msg in mensajes_basura):
        razones.append("contiene mensaje genérico sin valor")
    
    # 3. Respuesta truncada sin contenido real
    if doc.get("response_data", {}).get("status") == "truncated":
        if not doc.get("respuesta_usuario"):
            razones.append("truncado sin respuesta_usuario")
    
    # 4. Endpoint desconocido sin contexto
    if doc.get("endpoint") == "unknown" and not doc.get("respuesta_usuario"):
        razones.append("endpoint unknown sin respuesta útil")
    
    # 5. Sin timestamp o metadata básica
    if not doc.get("timestamp"):
        razones.append("sin timestamp")
    
    return razones

def analizar_calidad_texto(texto):
    """Analiza la calidad del texto semántico"""
    if not texto:
        return "vacío", 0
    
    longitud = len(texto)
    
    # Detectar patrones de calidad
    tiene_emojis = any(c in texto for c in "📝🧠📊🔢💾📄🎯✅⚠️🔧")
    tiene_estructura = any(sep in texto for sep in ["|", "\n", ":", "-"])
    tiene_contexto = any(word in texto.lower() for word in ["interpretación", "contexto", "procesado", "resultado"])
    
    if longitud > 200 and tiene_emojis and tiene_estructura and tiene_contexto:
        return "excelente", longitud
    elif longitud > 100 and (tiene_estructura or tiene_contexto):
        return "bueno", longitud
    elif longitud > 50:
        return "aceptable", longitud
    else:
        return "pobre", longitud

# ===== ANÁLISIS COSMOS DB =====
def analizar_cosmos_db():
    """Analiza documentos en Cosmos DB"""
    print("\n" + "="*60)
    print("🔍 ANALIZANDO COSMOS DB")
    print("="*60)
    
    if not COSMOS_KEY:
        print("❌ COSMOS_KEY no configurada")
        return None
    
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        metricas = MetricasCalidad()
        textos_vistos = set()
        
        # Leer todos los documentos
        query = "SELECT * FROM c ORDER BY c.timestamp DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        metricas.total_docs = len(items)
        print(f"📊 Total documentos: {metricas.total_docs}")
        
        longitudes = []
        
        for doc in items:
            # Analizar texto semántico
            texto_sem = doc.get("texto_semantico", "")
            calidad, longitud = analizar_calidad_texto(texto_sem)
            longitudes.append(longitud)
            
            # Detectar basura
            razones_basura = es_basura(doc)
            if razones_basura:
                metricas.docs_con_basura += 1
                metricas.ejemplos_basura.append({
                    "id": doc.get("id"),
                    "endpoint": doc.get("endpoint"),
                    "texto": texto_sem[:100],
                    "razones": razones_basura
                })
            else:
                metricas.docs_utiles += 1
                if len(metricas.ejemplos_buenos) < 3:
                    metricas.ejemplos_buenos.append({
                        "id": doc.get("id"),
                        "endpoint": doc.get("endpoint"),
                        "texto": texto_sem[:200],
                        "calidad": calidad
                    })
            
            # Detectar duplicados
            if texto_sem in textos_vistos:
                metricas.docs_duplicados += 1
            textos_vistos.add(texto_sem)
            
            # Estadísticas
            if not texto_sem:
                metricas.docs_sin_texto_semantico += 1
            if doc.get("response_data", {}).get("status") == "truncated":
                metricas.docs_truncados += 1
            
            metricas.endpoints_mas_comunes[doc.get("endpoint", "unknown")] += 1
            metricas.agentes_mas_activos[doc.get("agent_id", "unknown")] += 1
        
        metricas.longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
        
        return metricas
        
    except Exception as e:
        print(f"❌ Error en Cosmos DB: {e}")
        return None

# ===== ANÁLISIS AI SEARCH =====
def analizar_ai_search():
    """Analiza documentos en AI Search"""
    print("\n" + "="*60)
    print("🔍 ANALIZANDO AI SEARCH")
    print("="*60)
    
    if not SEARCH_KEY:
        print("❌ AZURE_SEARCH_KEY no configurada")
        return None
    
    try:
        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
        
        metricas = MetricasCalidad()
        
        # Buscar todos los documentos
        results = search_client.search(search_text="*", top=1000)
        
        longitudes = []
        textos_vistos = set()
        
        for result in results:
            metricas.total_docs += 1
            
            texto_sem = result.get("texto_semantico", "")
            calidad, longitud = analizar_calidad_texto(texto_sem)
            longitudes.append(longitud)
            
            # Detectar basura
            razones_basura = es_basura(result)
            if razones_basura:
                metricas.docs_con_basura += 1
                if len(metricas.ejemplos_basura) < 5:
                    metricas.ejemplos_basura.append({
                        "id": result.get("id"),
                        "endpoint": result.get("endpoint"),
                        "texto": texto_sem[:100],
                        "razones": razones_basura
                    })
            else:
                metricas.docs_utiles += 1
            
            # Duplicados
            if texto_sem in textos_vistos:
                metricas.docs_duplicados += 1
            textos_vistos.add(texto_sem)
            
            if not texto_sem:
                metricas.docs_sin_texto_semantico += 1
            
            metricas.endpoints_mas_comunes[result.get("endpoint", "unknown")] += 1
            metricas.agentes_mas_activos[result.get("agent_id", "unknown")] += 1
        
        metricas.longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
        
        return metricas
        
    except Exception as e:
        print(f"❌ Error en AI Search: {e}")
        return None

# ===== REPORTE =====
def generar_reporte(metricas_cosmos, metricas_search):
    """Genera reporte de diagnóstico"""
    print("\n" + "="*60)
    print("📊 REPORTE DE CALIDAD DE MEMORIA SEMÁNTICA")
    print("="*60)
    print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for nombre, metricas in [("COSMOS DB", metricas_cosmos), ("AI SEARCH", metricas_search)]:
        if not metricas:
            continue
            
        print(f"\n{'='*60}")
        print(f"📦 {nombre}")
        print(f"{'='*60}")
        
        total = metricas.total_docs
        if total == 0:
            print("⚠️ No hay documentos")
            continue
        
        # Métricas generales
        print(f"\n📈 MÉTRICAS GENERALES:")
        print(f"  Total documentos: {total}")
        print(f"  Documentos útiles: {metricas.docs_utiles} ({metricas.docs_utiles/total*100:.1f}%)")
        print(f"  Documentos basura: {metricas.docs_con_basura} ({metricas.docs_con_basura/total*100:.1f}%)")
        print(f"  Duplicados: {metricas.docs_duplicados} ({metricas.docs_duplicados/total*100:.1f}%)")
        print(f"  Sin texto semántico: {metricas.docs_sin_texto_semantico}")
        print(f"  Truncados: {metricas.docs_truncados}")
        print(f"  Longitud promedio: {metricas.longitud_promedio:.0f} caracteres")
        
        # Calidad general
        porcentaje_basura = metricas.docs_con_basura / total * 100
        if porcentaje_basura > 50:
            print(f"\n❌ CALIDAD: CRÍTICA ({porcentaje_basura:.1f}% basura)")
        elif porcentaje_basura > 30:
            print(f"\n⚠️ CALIDAD: MALA ({porcentaje_basura:.1f}% basura)")
        elif porcentaje_basura > 15:
            print(f"\n🟡 CALIDAD: REGULAR ({porcentaje_basura:.1f}% basura)")
        else:
            print(f"\n✅ CALIDAD: BUENA ({porcentaje_basura:.1f}% basura)")
        
        # Top endpoints
        print(f"\n🔝 TOP 5 ENDPOINTS:")
        for endpoint, count in metricas.endpoints_mas_comunes.most_common(5):
            print(f"  {endpoint}: {count} ({count/total*100:.1f}%)")
        
        # Top agentes
        print(f"\n🤖 TOP 5 AGENTES:")
        for agente, count in metricas.agentes_mas_activos.most_common(5):
            print(f"  {agente}: {count} ({count/total*100:.1f}%)")
        
        # Ejemplos de basura
        if metricas.ejemplos_basura:
            print(f"\n🗑️ EJEMPLOS DE BASURA (primeros 3):")
            for i, ejemplo in enumerate(metricas.ejemplos_basura[:3], 1):
                print(f"\n  {i}. ID: {ejemplo['id']}")
                print(f"     Endpoint: {ejemplo['endpoint']}")
                print(f"     Razones: {', '.join(ejemplo['razones'])}")
                print(f"     Texto: {ejemplo['texto']}")
        
        # Ejemplos buenos
        if metricas.ejemplos_buenos:
            print(f"\n✅ EJEMPLOS DE CALIDAD:")
            for i, ejemplo in enumerate(metricas.ejemplos_buenos[:2], 1):
                print(f"\n  {i}. ID: {ejemplo['id']}")
                print(f"     Endpoint: {ejemplo['endpoint']}")
                print(f"     Calidad: {ejemplo['calidad']}")
                print(f"     Texto: {ejemplo['texto']}")

# ===== MAIN =====
if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico de memoria semántica...")
    
    metricas_cosmos = analizar_cosmos_db()
    metricas_search = analizar_ai_search()
    
    generar_reporte(metricas_cosmos, metricas_search)
    
    print("\n" + "="*60)
    print("✅ Diagnóstico completado")
    print("="*60)
