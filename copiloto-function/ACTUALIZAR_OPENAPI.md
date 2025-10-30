# 📝 Instrucciones para Actualizar OpenAPI

## ⚠️ Nota Importante

El archivo `openapi.yaml` está en formato **JSON**, no YAML (a pesar del nombre).

## 🔧 Pasos para Agregar Endpoints de Azure AI Search

### 1. Abrir `openapi.yaml` (es JSON)

### 2. Buscar la sección `"paths":`

### 3. Agregar ANTES del cierre de `"paths"` (antes de `},`):

```json
    "/api/buscar-memoria": {
      "post": {
        "operationId": "buscarMemoriaSematica",
        "summary": "Buscar en memoria semántica usando Azure AI Search",
        "description": "Busca documentos en el índice de memoria semántica usando Managed Identity. No requiere claves en el payload.",
        "tags": ["🧠 Memoria Semántica"],
        "security": [],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Texto de búsqueda semántica",
                    "example": "errores recientes en ejecutar_cli"
                  },
                  "agent_id": {
                    "type": "string",
                    "description": "Filtrar por agente específico"
                  },
                  "session_id": {
                    "type": "string",
                    "description": "Filtrar por sesión específica"
                  },
                  "top": {
                    "type": "integer",
                    "description": "Número máximo de resultados",
                    "default": 10
                  },
                  "tipo": {
                    "type": "string",
                    "description": "Filtrar por tipo de documento"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Búsqueda exitosa",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "exito": {"type": "boolean"},
                    "total": {"type": "integer"},
                    "documentos": {"type": "array"},
                    "metadata": {"type": "object"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/indexar-memoria": {
      "post": {
        "operationId": "indexarMemoriaSematica",
        "summary": "Indexar documentos en memoria semántica",
        "description": "Indexa documentos en Azure AI Search usando Managed Identity.",
        "tags": ["🧠 Memoria Semántica"],
        "security": [],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["documentos"],
                "properties": {
                  "documentos": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "required": ["id", "agent_id", "texto_semantico"],
                      "properties": {
                        "id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "session_id": {"type": "string"},
                        "endpoint": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "tipo": {"type": "string"},
                        "texto_semantico": {"type": "string"},
                        "vector": {"type": "array", "items": {"type": "number"}},
                        "exito": {"type": "boolean"}
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Indexación exitosa",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "exito": {"type": "boolean"},
                    "documentos_subidos": {"type": "integer"},
                    "resultado": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    },
```

### 4. Agregar tag en la sección `"tags"`:

```json
    {
      "name": "🧠 Memoria Semántica",
      "description": "Búsqueda e indexación semántica con Azure AI Search usando Managed Identity"
    }
```

## ✅ Resultado

Los endpoints estarán disponibles en Foundry sin exponer claves en el payload.

## 🚀 Alternativa Rápida

Usar el archivo `openapi.yaml` completo ya actualizado que se puede generar con el script de Python.
