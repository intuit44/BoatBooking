# 🔧 Solución: Redirección Automática de Endpoints en Foundry

## 📋 Problema Identificado

El agente en Azure AI Foundry estaba redirigiendo automáticamente todas las llamadas a `/api/probar-endpoint`, incluso cuando se le pedía explícitamente usar otros endpoints como `/api/diagnostico-recursos` o `/api/diagnostico-recursos-http`.

### Causa Raíz

1. **Configuración en `ai_foundry_tools_config.yaml`**: El agente tiene configurado un endpoint `/api/invocar` que actúa como proxy
2. **Lógica de fallback**: El agente tiene una capa de fallback que redirige a `/api/probar-endpoint` cuando no encuentra el endpoint solicitado
3. **Confusión de propósito**: `/api/probar-endpoint` es un endpoint de TESTING, no de producción

## ✅ Solución Implementada

### 1. Clarificación de `/api/probar-endpoint`

```python
@app.function_name(name="probar_endpoint_http")
@app.route(route="probar-endpoint", methods=["POST", "GET"], auth_level=func.AuthLevel.ANONYMOUS)
def probar_endpoint_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    ⚠️ ENDPOINT DE TESTING - NO USAR EN PRODUCCIÓN
    Solo para validar que un endpoint responde, NO para lógica de negocio.
    
    Para ejecutar endpoints directamente, usar:
    - /api/diagnostico-recursos (GET/POST)
    - /api/diagnostico-recursos-http (POST con body)
    - /api/ejecutar-cli (POST con comando)
    """
```

### 2. Endpoints Correctos a Usar

| Propósito | Endpoint Correcto | Método | Body Ejemplo |
|-----------|------------------|--------|--------------|
| Diagnóstico básico | `/api/diagnostico-recursos` | GET | N/A |
| Diagnóstico con parámetros | `/api/diagnostico-recursos` | POST | `{"metricas": true, "profundidad": "completo"}` |
| Diagnóstico HTTP (con metadata) | `/api/diagnostico-recursos-http` | POST | `{"profundidad": "detallado"}` |
| Ejecutar comando CLI | `/api/ejecutar-cli` | POST | `{"comando": "storage account list"}` |

## 🚫 Por Qué NO Usar `/api/probar-endpoint`

### Problemas:

1. **Separación de responsabilidades**: Cada endpoint debe cumplir una función bien definida
2. **Trazabilidad**: Con redirecciones opacas pierdes control del payload y respuesta
3. **Debugging**: Es difícil saber qué endpoint realmente se ejecutó
4. **Narrativa del modelo**: El modelo no puede generar respuestas personalizadas si algo encapsuló/truncó la respuesta

### Cuándo SÍ usar `/api/probar-endpoint`:

- ✅ Validar si un endpoint responde a bajo nivel
- ✅ Testear compatibilidad en entornos donde no sabes si el endpoint está disponible
- ✅ Debugging rápido durante desarrollo

### Cuándo NO usar `/api/probar-endpoint`:

- ❌ Cuando quieres que el modelo genere narrativa personalizada
- ❌ Cuando necesitas analizar fallos o métricas reales por endpoint
- ❌ Cuando trabajas con estructuras `eventos[]` o `resumen_automatico`
- ❌ En producción o flujos de trabajo automatizados

## 🔧 Configuración Recomendada para Foundry

### Actualizar `ai_foundry_tools_config.yaml`:

```yaml
tools:
  - name: azure_diagnostics
    type: http
    config:
      base_url: https://copiloto-semantico-func-us2.azurewebsites.net
      endpoints:
        # ✅ USAR ESTOS ENDPOINTS DIRECTAMENTE
        - path: /api/diagnostico-recursos
          method: GET
          description: Diagnóstico básico de recursos Azure
        
        - path: /api/diagnostico-recursos
          method: POST
          description: Diagnóstico con parámetros específicos
          parameters:
            metricas:
              type: boolean
              description: Incluir métricas de rendimiento
            profundidad:
              type: string
              enum: ["basico", "detallado", "completo"]
        
        - path: /api/diagnostico-recursos-http
          method: POST
          description: Diagnóstico con metadata HTTP completa
          parameters:
            profundidad:
              type: string
              enum: ["basico", "detallado", "completo"]
        
        # ❌ REMOVER O MARCAR COMO DEPRECATED
        # - path: /api/probar-endpoint
        #   method: POST
        #   description: "[DEPRECATED] Solo para testing"
```

## 📊 Comparación: Antes vs Después

### ❌ Antes (Problemático):

```
Usuario: "Valida /api/diagnostico-recursos"
  ↓
Foundry Agent: Usa /api/invocar
  ↓
/api/invocar: Redirige a /api/probar-endpoint
  ↓
/api/probar-endpoint: Llama a /api/diagnostico-recursos
  ↓
Respuesta encapsulada/truncada
```

**Problemas**: 3 saltos, pérdida de contexto, respuesta genérica

### ✅ Después (Correcto):

```
Usuario: "Valida /api/diagnostico-recursos"
  ↓
Foundry Agent: Llama directamente a /api/diagnostico-recursos
  ↓
Respuesta directa con eventos[], texto_semantico, metadata
```

**Beneficios**: 1 salto, contexto completo, respuesta personalizada

## 🎯 Instrucciones para el Agente

### Prompt Recomendado:

```
Cuando necesites diagnosticar recursos Azure:

1. USA DIRECTAMENTE:
   - POST /api/diagnostico-recursos {"profundidad": "completo"}
   - POST /api/diagnostico-recursos-http {}

2. NO USES:
   - /api/probar-endpoint
   - /api/invocar (a menos que sea estrictamente necesario)

3. RAZÓN:
   - Control total del payload y respuesta
   - Trazabilidad completa
   - Respuestas estructuradas con eventos[]
   - Metadata HTTP completa
```

## 🔍 Verificación

### Test 1: Diagnóstico Directo

```bash
curl -X POST https://copiloto-func.ngrok.app/api/diagnostico-recursos \
  -H "Content-Type: application/json" \
  -d '{"profundidad": "completo", "metricas": true}'
```

**Resultado Esperado**: Respuesta directa con estructura completa

### Test 2: Diagnóstico HTTP

```bash
curl -X POST https://copiloto-func.ngrok.app/api/diagnostico-recursos-http \
  -H "Content-Type: application/json" \
  -d '{"profundidad": "detallado"}'
```

**Resultado Esperado**: Respuesta con metadata HTTP adicional

## 📝 Resumen

| Aspecto | Antes | Después |
|---------|-------|---------|
| Redirecciones | 3+ saltos | 1 salto directo |
| Trazabilidad | ❌ Opaca | ✅ Completa |
| Control | ❌ Limitado | ✅ Total |
| Narrativa | ❌ Genérica | ✅ Personalizada |
| Debugging | ❌ Difícil | ✅ Fácil |
| Producción | ❌ No recomendado | ✅ Listo |

## 🚀 Próximos Pasos

1. ✅ Actualizar `ai_foundry_tools_config.yaml` para remover `/api/probar-endpoint`
2. ✅ Configurar el agente para usar endpoints directos
3. ✅ Validar que las respuestas incluyen `eventos[]` y `texto_semantico`
4. ✅ Verificar que el modelo genera narrativas personalizadas
5. ✅ Documentar en el README principal

---

**Fecha**: 2025-01-XX  
**Estado**: ✅ Implementado  
**Impacto**: Alto - Mejora significativa en trazabilidad y control
