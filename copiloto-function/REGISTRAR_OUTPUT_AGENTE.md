# 📝 Registro de Output del Agente

## ❌ Problema Identificado

El wrapper `memory_route_wrapper.py` **solo captura tráfico de endpoints**, no respuestas conversacionales del agente que no invocan funciones.

## ✅ Solución

### 1. Helper Compartido ✅ YA EXISTE

**Archivo**: `services/agent_output_logger.py`

```python
def registrar_output_agente(texto: str, session_id: str, agent_id: str = "foundry_user") -> bool:
    """Registra output del agente sin pasar por endpoint."""
    from registrar_respuesta_semantica import registrar_respuesta_semantica
    return registrar_respuesta_semantica(texto, session_id, agent_id, "agent_output")
```

**Estado**: ✅ Implementado y probado

### 2. Integración en Foundry Workflow

**Ubicación**: En el código de Azure AI Foundry, justo después de generar `respuesta_final`.

#### Opción A: Llamada HTTP (Recomendada)

```python
# En el workflow de Foundry
import requests

def registrar_output_foundry(respuesta_final, session_id, agent_id):
    """Registra output del agente desde Foundry"""
    try:
        requests.post(
            "https://copiloto-semantico-func-us2.azurewebsites.net/api/guardar-memoria",
            json={
                "texto": respuesta_final,
                "session_id": session_id,
                "agent_id": agent_id,
                "tipo": "agent_output"
            },
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ Error registrando output: {e}")

# Usar justo antes de devolver respuesta al usuario
registrar_output_foundry(respuesta_final, session_id, agent_id)
```

#### Opción B: Import Directo (Si Foundry tiene acceso al código)

```python
# En el workflow de Foundry
from services.agent_output_logger import registrar_output_agente

# Justo antes de devolver respuesta al usuario
registrar_output_agente(respuesta_final, session_id, agent_id)
```

### 3. Flujo Completo

```
Usuario pregunta
    ↓
Foundry genera respuesta
    ↓
registrar_output_foundry(respuesta_final, session_id, agent_id)  ← AQUÍ
    ↓
Mostrar respuesta al usuario
```

## 🎯 Características

- ✅ Reutiliza flujo existente completo
- ✅ Sin endpoints adicionales
- ✅ Sin modificar el wrapper
- ✅ Mismo umbral (>20 chars)
- ✅ Misma validación de duplicados
- ✅ Mismo flujo Cosmos + AI Search

## 📊 Cobertura

| Escenario | Capturado |
|-----------|-----------|
| Endpoint invocado | ✅ Wrapper automático |
| Respuesta conversacional | ✅ Helper en Foundry |
| Respuesta con función | ✅ Wrapper automático |
| Respuesta sin función | ✅ Helper en Foundry |

## 🔍 Verificación

```bash
# Verificar que se registran outputs conversacionales
curl "https://copiloto-semantico-func-us2.azurewebsites.net/api/historial-interacciones?session_id=test"
```

## 📝 Notas

- El helper **no** está en `memory_route_wrapper.py` porque ese archivo solo ve tráfico HTTP de endpoints
- La captura debe hacerse **en el runtime de Foundry**, donde se genera la respuesta final
- Si Foundry no permite hooks, usar la Opción A (HTTP POST)

## ✅ Implementación Completada

**Archivo**: `copiloto-function/agent_client.py`

### Ejecución en Azure

```bash
# Desplegar a Azure Function con Managed Identity
func azure functionapp publish copiloto-semantico-func-us2

# O ejecutar directamente en Azure con az cli
az functionapp run --name copiloto-semantico-func-us2 --resource-group <rg> --script agent_client.py
```

### Variables de Entorno Requeridas

```bash
FOUNDRY_ENDPOINT=https://AgenteOpenAi.services.ai.azure.com/api/projects/AgenteOpenAi-project
AGENT_ID=asst_MjPrm7kpfPODo2ntofJ1oys0
AZURE_OPENAI_ENDPOINT=https://...
COSMOS_ENDPOINT=https://...
```

## ❓ ¿Dónde está el código de Foundry?

Buscar archivos que contengan:

- `agent.run()` o `agent.invoke()`
- `generate_response()` o `get_completion()`
- Integración con Azure OpenAI
- Workflow de agentes

Posibles ubicaciones:

- `Multi-Agent-Custom-Automation-Engine-Solution-Accelerator/src/backend/`
- Archivos con nombres como `agent_controller.py`, `foundry_agent.py`, `orchestrator.py`
