# SOLUCIÓN PRÁCTICA: Usar /api/agent-output

## ✅ YA TIENES EL ENDPOINT

`/api/agent-output` ya está creado y funciona.

## 🎯 CONFIGURAR EN FOUNDRY

### Paso 1: Ir a Foundry UI

1. https://ai.azure.com
2. Tu proyecto: **AgenteOpenAi-project**
3. Tu agente

### Paso 2: Agregar Post-Run Hook

En la configuración del agente, busca:
- **"After run"** 
- **"Post-processing"**
- **"Callbacks"**
- **"Webhooks"**

Agrega:

```
URL: https://copiloto-semantico-func-us2.azurewebsites.net/api/agent-output
Method: POST
Body:
{
  "thread_id": "{{thread.id}}",
  "texto": "{{response.text}}",
  "agent_id": "{{agent.id}}",
  "metadata": {
    "source": "foundry_postrun"
  }
}
```

### Paso 3: Si NO hay Post-Run Hook

Modifica el **System Prompt** del agente:

```
Después de cada respuesta, SIEMPRE llama a la función agent_output con:
- thread_id: el ID del thread actual
- texto: tu respuesta completa
```

Y agrega `agent_output` como herramienta disponible en el agente.

## 🧪 VALIDAR

Después de configurar:

1. Envía mensaje al agente en Foundry
2. Verifica logs de Function App:
   ```
   POST /api/agent-output
   Session ID: thread_XXXXX
   ```
3. Consulta Cosmos DB:
   ```sql
   SELECT * FROM c 
   WHERE c.session_id LIKE "thread_%"
   ORDER BY c._ts DESC
   ```

## 📊 RESULTADO

- ✅ Cada respuesta del agente se guarda con thread_id correcto
- ✅ No depende de headers
- ✅ No depende de modificar OpenAPI
- ✅ Funciona aunque el agente no llame otros endpoints
