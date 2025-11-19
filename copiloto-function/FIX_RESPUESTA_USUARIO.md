# Fix Aplicado: respuesta_usuario del Backend

## Problema

Foundry estaba generando miles de llamadas a `text-embedding-3-large` porque:

1. El backend fusiona threads + Cosmos + AI Search en `respuesta_usuario` (líneas 3987 y 5228)
2. Pero el código sobrescribía este campo con `""` en 3 ubicaciones
3. Foundry al recibir `respuesta_usuario: ""` re-procesaba `eventos[]` generando embeddings

## Solución Aplicada

Se modificaron 3 ubicaciones en `function_app.py` para **usar** el campo `respuesta_usuario` del backend en lugar de sobrescribirlo:

### Ubicación 1: Línea 4404 (historial-interacciones)

```python
# ANTES:
respuesta_struct["respuesta_usuario"] = ""

# DESPUÉS:
# FIX: Usar respuesta_usuario del backend si no existe
if not respuesta_struct.get("respuesta_usuario"):
    respuesta_struct["respuesta_usuario"] = (
        respuesta_struct.get("resumen_automatico")
        or (respuesta_struct.get("contexto_inteligente") or {}).get("resumen")
        or "Consulta completada"
    )
```

### Ubicación 2: Línea 4574 (historial-interacciones con query dinámica)

```python
# ANTES:
respuesta_struct["respuesta_usuario"] = ""

# DESPUÉS:
# FIX: Usar respuesta_usuario del backend si no existe
if not respuesta_struct.get("respuesta_usuario"):
    respuesta_struct["respuesta_usuario"] = (
        respuesta_struct.get("resumen_automatico")
        or (respuesta_struct.get("contexto_inteligente") or {}).get("resumen")
        or "Consulta completada"
    )
```

### Ubicación 3: Línea 5124 (copiloto)

```python
# ANTES:
respuesta_base["respuesta_usuario"] = ""

# DESPUÉS:
# FIX: Usar respuesta_usuario del backend si no existe
if not respuesta_base.get("respuesta_usuario"):
    respuesta_base["respuesta_usuario"] = (
        respuesta_base.get("resumen_automatico")
        or (respuesta_base.get("contexto_inteligente") or {}).get("resumen")
        or "Consulta completada"
    )
```

## Resultado Esperado

- ✅ Foundry recibe `respuesta_usuario` con el resumen ya fusionado del backend
- ✅ No necesita re-procesar `eventos[]` ni generar embeddings
- ✅ Se eliminan miles de llamadas innecesarias a `text-embedding-3-large`
- ✅ El modelo puede usar directamente el campo sin re-sumarizar

## Validación

Para validar que el fix funciona:

```bash
cd copiloto-function
python -m pytest tests/test_foundry_flows.py -v
```

## Archivos Modificados

- `function_app.py` (3 ubicaciones corregidas)

## Scripts Utilizados

- `fix_respuesta_usuario.py` - Script inicial (generó errores)
- `fix_respuesta_usuario_v2.py` - Aplicó el fix correcto
- `fix_respuesta_usuario_v3.py` - Limpió líneas duplicadas

## Fecha

2025-01-16
