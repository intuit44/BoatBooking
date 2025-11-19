# 🎯 Ajustes para Detección Automática de Intención de Memoria

## Problema Identificado

El agente no interpreta automáticamente cuando el usuario pregunta "¿en qué estábamos?" y requiere que se le pida explícitamente usar herramientas de memoria.

## Solución Implementada

### 1. ✅ Clasificador Semántico (`clasificador_intencion.py`)

Ya existe y funciona correctamente. Usa embeddings + similitud coseno para detectar intenciones sin regex.

**Dataset de intenciones:**

- `resumen_conversacion`: "en qué estábamos", "qué hicimos", "dame un resumen"
- `leer_threads`: "valida con las conversaciones anteriores", "lee el thread anterior"
- `historial_acciones`: "qué archivos leímos", "qué comandos ejecutamos"
- `sin_contexto`: "no tengo información", "no sé de qué hablas"

### 2. ✅ Servicio de Blob (`blob_service.py`)

Creado para operaciones auxiliares de listado y lectura de blobs.

### 3. ✅ Integración en `memory_route_wrapper.py`

El wrapper ahora:

1. Detecta intención usando el clasificador semántico
2. Si `requiere_memoria` es True y confianza > 0.7:
   - **Para `listar_threads_recientes`**: Lista threads y lee el más reciente
   - **Para `historial_interacciones`**: Consulta historial de Cosmos DB
3. Retorna respuesta directamente sin pasar por el endpoint original

### 4. 📝 Actualización Necesaria en `openapi.yaml`

Agregar hints semánticos en las descripciones de endpoints clave:

```yaml
/api/listar-blobs:
  get:
    summary: "📂 MEMORIA: Listar threads guardados"
    description: |
      ⚠️ ACTIVACIÓN AUTOMÁTICA cuando el usuario:
      - Pregunta "¿en qué estábamos?"
      - Solicita "valida con conversaciones anteriores"
      - Dice "no tengo contexto"
      
      El sistema detecta automáticamente estas intenciones y lista threads recientes.
      
/api/historial-interacciones:
  get:
    summary: "📜 MEMORIA: Historial de acciones"
    description: |
      ⚠️ ACTIVACIÓN AUTOMÁTICA cuando el usuario:
      - Pregunta "qué hicimos"
      - Solicita "qué archivos leímos"
      - Pide "historial de comandos"
```

## Flujo Completo

```
Usuario: "en qué estábamos"
    ↓
memory_route_wrapper detecta input
    ↓
clasificador_intencion.clasificar(mensaje)
    ↓
Resultado: {
  "requiere_memoria": True,
  "intencion": "resumen_conversacion",
  "confianza": 0.92,
  "accion_sugerida": "listar_threads_recientes"
}
    ↓
Ejecuta acción automáticamente:
  - Lista threads con blob_service.listar_blobs("threads/", 5)
  - Lee el más reciente con blob_service.leer_blob()
    ↓
Retorna respuesta directa:
{
  "exito": True,
  "respuesta_usuario": "📜 Última conversación recuperada:\n\n[contenido]...",
  "thread_leido": "threads/assistant_2025-01-15.json",
  "intencion_detectada": "resumen_conversacion",
  "metadata": {"memoria_automatica": True, "confianza": 0.92}
}
```

## Ventajas del Enfoque

1. **Sin plantillas rígidas**: Usa similitud semántica, no regex
2. **Extensible**: Agregar nuevas intenciones solo requiere actualizar el dataset
3. **Confianza medible**: Umbral de 0.75 para activación
4. **Transparente**: El agente ve qué intención se detectó y con qué confianza
5. **No invasivo**: Solo se activa cuando la confianza es alta

## Próximos Pasos

1. ✅ Verificar que `embedding_generator.py` funciona correctamente
2. ✅ Probar con mensajes reales del usuario
3. 📝 Actualizar `openapi.yaml` con hints semánticos
4. 🧪 Ajustar umbral de confianza si es necesario (actualmente 0.75)
5. 📊 Monitorear métricas de activación en logs

## Configuración de Umbral

Si el sistema es demasiado sensible o no lo suficiente, ajustar en `clasificador_intencion.py`:

```python
class ClasificadorIntencion:
    def __init__(self):
        self.umbral_confianza = 0.75  # Ajustar aquí (0.0 - 1.0)
```

- **0.6-0.7**: Más sensible, activa con menos certeza
- **0.75-0.8**: Balance (recomendado)
- **0.85-0.95**: Muy estricto, solo activa con alta certeza

## Testing

```python
# Test manual del clasificador
from clasificador_intencion import get_clasificador

clasificador = get_clasificador()

# Casos de prueba
mensajes = [
    "en qué estábamos",
    "qué hicimos",
    "valida con las conversaciones anteriores",
    "cómo crear una función en Python"  # No debería activar memoria
]

for msg in mensajes:
    resultado = clasificador.clasificar(msg)
    print(f"{msg} → {resultado}")
```

## Logs de Diagnóstico

El sistema registra automáticamente:

- `🎯 Intención detectada: resumen_conversacion (confianza: 0.92)`
- `📝 Ejemplo similar: 'en qué estábamos'`
- `✅ Memoria recuperada automáticamente: 2000 chars`

Buscar en logs de Azure Function App para monitorear activaciones.
