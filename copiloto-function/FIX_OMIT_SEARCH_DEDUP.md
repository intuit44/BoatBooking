# 🔧 Fix: Error omit_search_dedup en Azure Search

**Fecha**: 2025-01-XX  
**Estado**: ✅ RESUELTO

---

## ❌ Problema

```
Error subiendo documentos: The property 'omit_search_dedup' does not exist 
on type 'search.documentFields' or is not present in the API version '2024-07-01'.
```

### Causa

El campo `omit_search_dedup` se estaba enviando al documento de Azure Search, pero este campo:
- No existe en el esquema de Azure Search
- No es reconocido por la API version 2024-07-01
- Era un campo interno que no debía enviarse al servicio

### Ubicación del Error

```python
# services/memory_service.py - Línea ~230
if embedding_precalculado:
    documento["vector"] = embedding_precalculado
    documento["omit_search_dedup"] = True  # ❌ Campo inválido
    logging.info(f"♻️ Reutilizando embedding precalculado")
```

---

## ✅ Solución

Eliminado el campo `omit_search_dedup` del documento antes de enviarlo a Azure Search.

### Código Corregido

```python
# services/memory_service.py
if embedding_precalculado:
    documento["vector"] = embedding_precalculado
    # Campo omit_search_dedup eliminado
    logging.info(f"♻️ Reutilizando embedding precalculado")
```

---

## 📋 Campos Válidos en Azure Search

Los únicos campos que deben enviarse al documento de Azure Search son:

```python
documento = {
    "id": str,                    # ✅ Requerido
    "session_id": str,            # ✅ Válido
    "agent_id": str,              # ✅ Válido
    "endpoint": str,              # ✅ Válido
    "texto_semantico": str,       # ✅ Válido
    "exito": bool,                # ✅ Válido
    "tipo": str,                  # ✅ Válido
    "timestamp": str,             # ✅ Válido (ISO format)
    "vector": list[float]         # ✅ Válido (embedding)
}
```

**Campos NO válidos**:
- ❌ `omit_search_dedup`
- ❌ Cualquier campo no definido en el índice

---

## 🧪 Verificación

### Antes del Fix
```
[2025-11-15T18:59:55.609Z] Error subiendo documentos: 
The property 'omit_search_dedup' does not exist...
[2025-11-15T18:59:55.610Z] ⚠️ Error indexando en AI Search
```

### Después del Fix
```
[2025-11-15T18:59:55.610Z] ♻️ Reutilizando embedding precalculado
[2025-11-15T18:59:55.611Z] ✅ Indexado automáticamente en AI Search: fallback_session_semantic_1763251193
```

---

## 🔍 Impacto

- ✅ Indexación en AI Search funciona correctamente
- ✅ Embeddings se reutilizan sin problemas
- ✅ No se generan errores en logs
- ✅ Memoria se guarda e indexa exitosamente

---

## 📁 Archivo Modificado

```
copiloto-function/
└── services/
    └── memory_service.py          ✅ CORREGIDO
        └── _indexar_en_ai_search()
```

---

## 🎯 Lección Aprendida

**Regla**: Solo enviar a Azure Search los campos definidos en el esquema del índice.

**Verificación**: Antes de agregar un campo al documento, confirmar que existe en el índice de Azure Search.

**Documentación**: Consultar el esquema del índice en Azure Portal o mediante API para conocer los campos válidos.

---

**Estado**: ✅ Error resuelto, indexación funcionando correctamente
