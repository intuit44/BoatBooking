# 🎯 Hook para Captura de Agent Output

**Fecha**: 2025-01-09  
**Problema**: Respuestas del agente sin endpoint no se guardaban en Cosmos  
**Solución**: Helper `agent_output_logger.py` (sin endpoint adicional)

---

## 🔍 Problema

El wrapper solo captura respuestas que pasan por endpoints. Las respuestas generadas directamente por el agente en Foundry UI (sin invocar función OpenAPI) nunca se registran.

---

## ✅ Solución Mínima

### Helper Creado: `services/agent_output_logger.py`

```python
def registrar_output_agente(texto: str, session_id: str, agent_id: str = "foundry_user") -> bool:
    """Registra output del agente sin pasar por endpoint."""
    from registrar_respuesta_semantica import registrar_respuesta_semantica
    return registrar_respuesta_semantica(texto, session_id, agent_id, "agent_output")
```

---

## 🔧 Integración (1 línea)

En el código donde Foundry genera la respuesta final:

```python
from services.agent_output_logger import registrar_output_agente

# Generar respuesta
respuesta = agente.generar_respuesta(mensaje)

# Hook: Registrar antes de devolver
registrar_output_agente(respuesta, session_id, agent_id)

# Devolver al usuario
return respuesta
```

---

## 🎯 Características

✅ Reutiliza flujo existente (`registrar_respuesta_semantica`)  
✅ Mismo umbral (>20 chars)  
✅ Misma validación de duplicados  
✅ Mismo flujo Cosmos + AI Search  
✅ Sin endpoints adicionales  
✅ Sin modificar wrapper

---

## 🧪 Test

```python
from services.agent_output_logger import registrar_output_agente

ok = registrar_output_agente(
    texto="No se encontraron interacciones",
    session_id="test",
    agent_id="foundry_user"
)
# ok = True (guardado en Cosmos + AI Search)
```

---

**Estado**: ✅ Implementado  
**Requiere**: 1 línea en el código del agente  
**Impacto**: 🟢 Solución mínima sin complejidad adicional
