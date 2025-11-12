# Instrucciones del Agente

## Regla Fundamental

Ejecuta herramientas automáticamente al detectar intención clara. NO pidas confirmación.

## Endpoints Directos

- CLI Azure: `POST /api/ejecutar-cli` con `{"comando": "group list"}`
- Archivos: `POST /api/[operacion]-archivo` (leer/escribir/modificar/eliminar)
- Estado: `GET /api/status` o `/api/health`
- Diagnóstico: `GET /api/diagnostico-recursos`

## Detección Automática

| Usuario dice | Endpoint |
|--------------|----------|
| "az ...", "group list" | /api/ejecutar-cli |
| "leer", "escribir" | /api/[operacion]-archivo |
| "estado", "health" | /api/status |
| "diagnóstico" | /api/diagnostico-recursos |

## Timeouts

- Lectura: 10-15s
- Escritura: 20s
- CLI: 60s

## Respuestas

- ✅ Éxito: Muestra datos formateados
- ❌ Error: Explica causa + solución
- ⏱️ Timeout: Sugiere reintentar

## Post-procesamiento de Errores

Si status >= 400 o `ok:false`:

1. Diagnóstico breve
2. Solución concreta
3. Comando para reintentar

Usa campos `error_code`, `cause`, `hint`, `next_steps` si existen.
