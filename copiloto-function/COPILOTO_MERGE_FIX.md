# FIX COPILOTO - MERGE COSMOS + VECTORIAL

## PROBLEMA IDENTIFICADO

El endpoint `/api/copiloto` (línea ~4970) hace búsqueda vectorial pero **retorna inmediatamente** sin hacer MERGE con Cosmos.

## CÓDIGO A REEMPLAZAR

Buscar en `function_app.py` línea ~4970:

```python
# Si hay resultados vectoriales, aplicar sintetizador real
if docs_sem:
    docs_cosmos = memoria_previa.get("interacciones_recientes", []) or []
    respuesta_semantica = sintetizar(docs_sem, docs_cosmos)
    
    response_data = {
        "exito": True,
        "respuesta_usuario": respuesta_semantica,
        "fuente_datos": "AzureSearch+CognitiveSynth",
        "total_docs_semanticos": len(docs_sem),
        "session_id": session_id,
        "agent_id": agent_id,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "consulta_original": consulta_usuario,
            "fuente": "azure_search_vectorial"
        }
    }
    
    return func.HttpResponse(
        json.dumps(response_data, ensure_ascii=False),
        mimetype="application/json",
        status_code=200
    )
```

## CÓDIGO CORRECTO (REEMPLAZAR CON ESTO)

```python
# 🔥 EXTRAER session_id y agent_id SIEMPRE (incluso con body vacío)
session_id = req.headers.get("Session-ID") or req.params.get("session_id") or "test_session"
agent_id = req.headers.get("Agent-ID") or req.params.get("agent_id") or "GlobalAgent"

# 🧠 OBTENER MEMORIA DEL WRAPPER
memoria_previa = getattr(req, '_memoria_contexto', {})
docs_vectoriales = memoria_previa.get("docs_vectoriales", [])
docs_cosmos = memoria_previa.get("interacciones_recientes", [])

# 🔥 MERGE: Combinar vectorial + secuencial
docs_merged = []
ids_vistos = set()

# Prioridad 1: Docs vectoriales (más relevantes)
for doc in docs_vectoriales:
    doc_id = doc.get("id")
    if doc_id and doc_id not in ids_vistos:
        docs_merged.append(doc)
        ids_vistos.add(doc_id)

# Prioridad 2: Docs de Cosmos (cronológicos)
for doc in docs_cosmos[:10]:
    doc_id = doc.get("id")
    if doc_id and doc_id not in ids_vistos:
        docs_merged.append(doc)
        ids_vistos.add(doc_id)

logging.info(f"🔥 MERGE: {len(docs_vectoriales)} vectorial + {len(docs_cosmos)} cosmos = {len(docs_merged)} total")

# 🧠 SINTETIZAR RESPUESTA
if docs_merged:
    respuesta_semantica = sintetizar(docs_vectoriales, docs_cosmos)
    
    # 🔥 SANITIZAR respuesta_usuario
    respuesta_sanitizada = respuesta_semantica[:2000] if respuesta_semantica else "Sin contexto disponible"
    
    response_data = {
        "exito": True,
        "respuesta_usuario": respuesta_sanitizada,
        "fuente_datos": "Cosmos+AISearch",
        "total_docs_semanticos": len(docs_vectoriales),
        "total_docs_cosmos": len(docs_cosmos),
        "total_merged": len(docs_merged),
        "session_id": session_id,
        "agent_id": agent_id,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "consulta_original": consulta_usuario,
            "fuente": "azure_search_vectorial",
            "wrapper_aplicado": True,
            "memoria_aplicada": True,
            "interacciones_previas": len(docs_cosmos)
        },
        "contexto_conversacion": {
            "mensaje": f"Continuando conversación con {len(docs_cosmos)} interacciones previas",
            "ultimas_consultas": memoria_previa.get("resumen_conversacion", "")[:500],
            "session_id": session_id,
            "ultima_actividad": memoria_previa.get("ultima_actividad")
        }
    }
    
    return func.HttpResponse(
        json.dumps(response_data, ensure_ascii=False),
        mimetype="application/json",
        status_code=200
    )
```

## CAMBIOS CLAVE

1. **Extracción de agent_id**: Ahora lee de headers incluso con body vacío
2. **MERGE explícito**: Combina docs vectoriales + cosmos sin duplicados
3. **Sanitización**: Trunca respuesta_usuario a 2000 chars
4. **Metadata completa**: Incluye todos los contadores (vectorial, cosmos, merged)
5. **contexto_conversacion**: Trunca resumen a 500 chars para evitar overflow

## APLICAR FIX

```bash
# Editar function_app.py línea ~4970
code function_app.py:4970
```
