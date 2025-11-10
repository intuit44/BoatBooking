# 🔧 Umbral de Captura Reducido: 50 → 20 caracteres

**Fecha**: 2025-01-09  
**Problema**: Respuestas cortas del agente (<50 chars) no se guardaban en Cosmos  
**Solución**: Reducir umbral de 50 a 20 caracteres

---

## 🎯 Problema Identificado

### Antes (umbral 50)

```python
if len(texto_limpio.strip()) > 50:
    registrar_respuesta_semantica(...)
```

**Resultado**: Respuestas como "No se encontraron interacciones" (40 chars) NO se guardaban.

---

## ✅ Solución Implementada

### Archivos Modificados

1. **`registrar_respuesta_semantica.py`** línea 52:

```python
# ANTES
if not response_text or len(str(response_text).strip()) < 50:
    return False

# DESPUÉS
if not response_text or len(str(response_text).strip()) < 20:
    return False
```

2. **`memory_route_wrapper.py`** línea 414:

```python
# ANTES
if len(texto_limpio.strip()) > 50:
    registrar_respuesta_semantica(...)

# DESPUÉS
if len(texto_limpio.strip()) > 20:
    registrar_respuesta_semantica(...)
```

---

## 📊 Impacto

| Longitud Respuesta | Antes (>50) | Después (>20) |
|-------------------|-------------|---------------|
| "Error" (5 chars) | ❌ No captura | ❌ No captura |
| "No encontrado" (13 chars) | ❌ No captura | ❌ No captura |
| "Sin resultados disponibles" (27 chars) | ❌ No captura | ✅ **Captura** |
| "No se encontraron interacciones" (35 chars) | ❌ No captura | ✅ **Captura** |
| "Análisis completo..." (100 chars) | ✅ Captura | ✅ Captura |

---

## 🧪 Validación

### Test 1: Respuesta Corta

```bash
# Simular respuesta de 30 caracteres
curl -X POST http://localhost:7071/api/copiloto \
  -H "Session-ID: test" \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "test corto"}'
```

**Log Esperado**:

```
[BLOQUE 6] texto_limpio len=30
[BLOQUE 6] Llamando registrar_respuesta_semantica...
✅ Respuesta guardada e indexada
```

### Test 2: Respuesta Muy Corta (rechazada)

```bash
# Respuesta de 10 caracteres
```

**Log Esperado**:

```
⏭️ Respuesta muy corta (<20 chars), no se vectoriza
```

---

## 🎯 Beneficios

✅ **Más cobertura**: Captura respuestas cortas pero significativas  
✅ **Mejor contexto**: El agente tiene más información histórica  
✅ **Sin ruido**: Umbral 20 evita capturar mensajes triviales  
✅ **Consistente**: Mismo umbral en ambos archivos

---

## 📝 Notas

- **Umbral mínimo razonable**: 20 caracteres es suficiente para frases cortas
- **Evita ruido**: Mensajes <20 chars suelen ser triviales ("OK", "Error", etc.)
- **Duplicados**: El sistema ya valida duplicados por hash, no por longitud

---

**Estado**: ✅ Implementado  
**Impacto**: 🟢 Bajo riesgo, alta efectividad  
**Requiere reinicio**: ✅ Sí
