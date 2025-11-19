# 🔧 Fix: Flujo de Historial Roto por Mapeo Agresivo

**Fecha**: 2025-01-XX  
**Estado**: ✅ RESUELTO

---

## ❌ Problema

El agente en Foundry no podía acceder al historial y respondía:
> "No he podido acceder a los archivos que has subido, ya que parece que no están disponibles en el sistema."

### Causa Raíz

El mapeo de narrativas en `_construir_texto_semantico_rico()` estaba **sobrescribiendo** el campo `respuesta_usuario` que los endpoints inteligentes ya generaban.

**Flujo roto**:
```python
# Endpoint genera respuesta_usuario rica
response_data = {
    "respuesta_usuario": "Recuperé 15 interacciones sobre deployment...",
    "interacciones": [...],
    "resumen_conversacion": "..."
}

# ❌ Mapeo lo sobrescribe con texto genérico
if "historial" in endpoint_name:
    return f"Recuperé {total} interacciones Resumen: {resumen[:200]}", True
    # Ignora respuesta_usuario original
```

---

## 🔍 Endpoints Afectados

Los siguientes endpoints ya generan `respuesta_usuario` y NO deben ser mapeados:

1. **historial-interacciones** - Genera resumen conversacional
2. **contexto-inteligente** - Genera interpretación semántica
3. **Cualquier endpoint con respuesta_usuario** - Ya tiene narrativa rica

---

## ✅ Solución

### Principio de Prioridad

```python
def _construir_texto_semantico_rico(response_data, endpoint, agent_id, success, params):
    # 1️⃣ PRIORIDAD MÁXIMA: respuesta_usuario (voz del agente)
    if isinstance(response_data, dict) and response_data.get("respuesta_usuario"):
        return str(response_data["respuesta_usuario"]).strip(), False  # ✅ Retorna inmediatamente
    
    # 2️⃣ Texto semántico explícito
    if isinstance(response_data, dict) and response_data.get("texto_semantico"):
        return str(response_data["texto_semantico"]).strip(), False
    
    # 3️⃣ MAPEO solo para endpoints SIN respuesta_usuario
    ...
```

### Cambios Aplicados

**1. Historial - Saltar mapeo**
```python
# ❌ Antes (sobrescribía respuesta_usuario)
elif "historial-interacciones" in endpoint_name:
    interacciones = response_data.get("interacciones", [])
    total = len(interacciones)
    return f"Recuperé {total} interacciones", True

# ✅ Ahora (respeta respuesta_usuario)
elif "historial" in endpoint_name:
    pass  # Saltar mapeo, priorizar respuesta_usuario del endpoint
```

**2. Contexto Inteligente - Saltar mapeo**
```python
# ❌ Antes (sobrescribía respuesta_usuario)
elif "contexto-inteligente" in endpoint_name:
    resumen = response_data.get("resumen_inteligente")
    return f"Contexto inteligente: {resumen}", True

# ✅ Ahora (respeta respuesta_usuario)
elif "contexto-inteligente" in endpoint_name:
    pass  # Ya tiene respuesta_usuario
```

**3. Escribir-archivo - Simplificado**
```python
# ❌ Antes (duplicaba lógica)
elif "escribir-archivo" in endpoint_name:
    # Lógica específica
    ...
if "guardar-memoria" in endpoint_name or "escribir-archivo" in endpoint_name:
    # Lógica duplicada
    ...

# ✅ Ahora (unificado)
if "escribir-archivo" in endpoint_name or "guardar-memoria" in endpoint_name:
    # Lógica única
    ...
```

---

## 📋 Reglas de Mapeo

### ✅ Mapear SOLO cuando:

1. El endpoint NO tiene `respuesta_usuario`
2. El endpoint NO tiene `texto_semantico`
3. El endpoint es técnico (leer-archivo, ejecutar-cli, etc.)
4. Se necesita extraer datos específicos del response

### ❌ NO mapear cuando:

1. El endpoint ya genera `respuesta_usuario`
2. El endpoint es inteligente (historial, contexto, introspection)
3. El endpoint ya tiene narrativa rica
4. El mapeo sobrescribiría información valiosa

---

## 🎯 Endpoints que DEBEN Mapearse

Estos endpoints NO generan `respuesta_usuario` y necesitan mapeo:

```python
✅ leer-archivo          # Extraer: ruta, contenido, contexto
✅ ejecutar-cli          # Extraer: comando, resultado, código
✅ modificar-archivo     # Extraer: ruta, pattern, replacement
✅ eliminar-archivo      # Extraer: ruta, éxito, nota
✅ crear-contenedor      # Extraer: nombre, cuenta, tipo
✅ preparar-script       # Extraer: nombre, descripción, contenido
✅ diagnostico-recursos  # Extraer: recursos, total, detalles
✅ configurar-*          # Extraer: app, configuraciones
```

---

## 🎯 Endpoints que NO DEBEN Mapearse

Estos endpoints YA generan `respuesta_usuario`:

```python
❌ historial-interacciones    # Ya tiene resumen conversacional
❌ contexto-inteligente        # Ya tiene interpretación semántica
❌ introspection               # Ya tiene narrativa de identidad
❌ Cualquier endpoint con respuesta_usuario
```

---

## 🧪 Verificación

### Antes del Fix
```
Usuario: "dame un resumen de lo que estuvimos haciendo"
Agente: "No he podido acceder a los archivos..."
```

### Después del Fix
```
Usuario: "dame un resumen de lo que estuvimos haciendo"
Agente: "Recuperé 15 interacciones sobre deployment de Azure Functions, 
         configuración de storage y troubleshooting de permisos..."
```

---

## 📊 Flujo Correcto

```
Endpoint ejecutado
    ↓
¿Tiene respuesta_usuario?
    ↓ SÍ
    Usar respuesta_usuario (NO mapear)
    ↓ NO
¿Tiene texto_semantico?
    ↓ SÍ
    Usar texto_semantico (NO mapear)
    ↓ NO
¿Es endpoint técnico?
    ↓ SÍ
    Aplicar mapeo con datos reales
    ↓ NO
    Fallback genérico
```

---

## 📁 Archivo Modificado

```
copiloto-function/
└── services/
    └── memory_service.py          ✅ CORREGIDO
        └── _construir_texto_semantico_rico()
            ├── Simplificado mapeo de historial
            ├── Simplificado mapeo de contexto-inteligente
            └── Unificado mapeo de escribir-archivo
```

---

## 🎓 Lección Aprendida

**Regla de Oro**: El mapeo es para endpoints **técnicos** que no generan narrativas propias.

**Verificación**: Antes de mapear un endpoint, confirmar que NO tiene `respuesta_usuario` o `texto_semantico`.

**Prioridad**: Siempre respetar `respuesta_usuario` > `texto_semantico` > mapeo > fallback.

---

## ✅ Estado Final

- ✅ Historial funciona correctamente
- ✅ Contexto inteligente funciona correctamente
- ✅ Endpoints técnicos tienen narrativas detalladas
- ✅ No se sobrescribe respuesta_usuario
- ✅ Sintaxis correcta
- ✅ Compatible con sistema existente

**Estado**: ✅ Flujo restaurado, agente puede acceder al historial correctamente
