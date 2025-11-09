# 🔧 Corrección: Función `sintetizar()` en function_app.py

## 🎯 Problema Identificado

La función `sintetizar()` en `function_app.py` está generando respuestas técnicas con formato de lista en lugar de respuestas conversacionales naturales para Foundry UI.

### Salida Actual (❌ Técnica)

```
🔸 Otros resultados vectoriales:

• [unknown]
valida si puedes ver los últimos cambios que he realizado...
```

### Salida Esperada (✅ Conversacional)

```
He consultado el historial de interacciones y encontré que recientemente validaste 
los últimos cambios realizados. El sistema registró 8 interacciones previas en esta 
sesión. ¿Necesitas más detalles sobre alguna interacción específica?
```

## 📋 Ubicación del Código

**Archivo**: `copiloto-function/function_app.py`  
**Función**: `sintetizar(docs_search, docs_cosmos, max_items=7, max_chars_per_item=1200)`  
**Línea aproximada**: ~1200-1400

## 🔧 Corrección Necesaria

### Cambio 1: Formato de Salida Conversacional

**Antes**:

```python
partes.append(f"🔸 Otros resultados vectoriales:")
for doc in remaining_vecs:
    partes.append(f"• [{endpoint}]\\n{body}")
```

**Después**:

```python
# Generar respuesta conversacional natural
items_texto = []
for doc in remaining_vecs[:3]:  # Solo top 3
    texto = doc.get("texto_semantico", "")
    if texto and len(texto) > 40:
        items_texto.append(texto.splitlines()[0][:260])

if items_texto:
    cabecera = f"He revisado el historial y encontré {len(docs_search)} interacciones relevantes. "
    bullets = "\\n".join(f"• {s}" for s in items_texto)
    return f"{cabecera}\\n\\n{bullets}"
```

### Cambio 2: Eliminar Encabezados Técnicos

**Remover**:

- `"🔸 Otros resultados vectoriales:"`
- `"🔹 Actividad relevante (vectores, score>0.65):"`
- `"📡 Interacciones tipo endpoint_call (Cosmos, cronológicas):"`
- `"📘 Resúmenes enriquecidos (Cosmos):"`

**Reemplazar con**:

- Texto conversacional directo
- Sin emojis técnicos
- Sin referencias a "vectores" o "Cosmos"

### Cambio 3: Sintetizar en Lugar de Listar

**Antes** (lista cruda):

```python
for doc in docs:
    partes.append(f"• [{endpoint}]\\n{texto}")
```

**Después** (síntesis conversacional):

```python
# Agrupar por tema/endpoint
temas = {}
for doc in docs:
    endpoint = doc.get("endpoint", "general")
    texto = doc.get("texto_semantico", "")
    if endpoint not in temas:
        temas[endpoint] = []
    temas[endpoint].append(texto)

# Generar resumen por tema
resumen_partes = []
for tema, textos in list(temas.items())[:3]:
    resumen_partes.append(f"En {tema}: {textos[0][:200]}...")

return "\\n\\n".join(resumen_partes)
```

## 🧪 Test de Validación

Ejecutar después de aplicar cambios:

```bash
cd copiloto-function
python test_foundry_input_capture.py
```

**Resultado esperado en logs**:

```
🌐 VALIDACIÓN DE MEMORIA GLOBAL (RESPUESTA FOUNDRY)
✅ Respuesta es conversacional (sin patrones técnicos)
✅ Respuesta tiene contenido útil y formato humano
```

**Resultado esperado en Cosmos**:

```json
{
  "event_type": "respuesta_semantica",
  "texto_semantico": "He revisado el historial y encontré 5 interacciones relevantes. En copiloto: validaste los últimos cambios realizados. En listar-blobs: consultaste los archivos disponibles..."
}
```

## 📊 Impacto

| Componente | Antes | Después |
|------------|-------|---------|
| Formato respuesta | ❌ Técnico (listas) | ✅ Conversacional |
| Emojis técnicos | ❌ Presentes | ✅ Removidos |
| Referencias internas | ❌ "vectores", "Cosmos" | ✅ Lenguaje natural |
| Longitud respuesta | ❌ Muy larga | ✅ Sintetizada |
| Experiencia usuario | ❌ Confusa | ✅ Clara |

## 🎯 Próximos Pasos

1. ✅ Localizar función `sintetizar()` en `function_app.py`
2. ⏳ Aplicar cambios de formato conversacional
3. ⏳ Remover encabezados técnicos
4. ⏳ Implementar síntesis por temas
5. ⏳ Ejecutar test de validación
6. ⏳ Verificar en Foundry UI

## 💡 Notas Adicionales

- La función `sintetizar()` es llamada desde `endpoints/memoria_global.py`
- El cambio NO afecta la indexación en Cosmos/AI Search
- Solo cambia el formato de presentación al usuario
- Los embeddings vectoriales siguen funcionando igual
- La memoria semántica se mantiene intacta

## 🔗 Archivos Relacionados

- `copiloto-function/function_app.py` - Función `sintetizar()`
- `copiloto-function/endpoints/memoria_global.py` - Llamada a `sintetizar()`
- `copiloto-function/test_foundry_input_capture.py` - Test de validación
- `copiloto-function/registrar_respuesta_semantica.py` - Guardado de respuestas

---

**Estado**: ⏳ Pendiente de aplicación  
**Prioridad**: 🔴 Alta  
**Impacto**: 🎯 Experiencia de usuario en Foundry
