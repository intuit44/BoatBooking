# 🧪 Instrucciones de Testing - Azure AI Search con Managed Identity

## 📋 Prerequisitos

1. ✅ Ejecutar `setup_managed_identity_search.ps1`
2. ✅ Instalar `azure-search-documents>=11.4.0`
3. ✅ Agregar endpoints a `function_app.py`

## 🚀 Tests Disponibles

### 1. Test de Integración Completa

Valida el cliente Azure Search con Managed Identity:

```bash
cd copiloto-function
python test_azure_search_integration.py
```

**Qué valida:**

- ✅ Configuración de variables de entorno
- ✅ Inicialización del cliente (MI o API Key)
- ✅ Búsqueda de documentos existentes
- ✅ Indexación de documento de prueba
- ✅ Recuperación de documento indexado
- ✅ Búsqueda semántica con filtros
- ✅ Eliminación de documento
- ✅ Simulación de request desde Foundry

### 2. Test de Endpoints HTTP

Simula requests reales desde Foundry OpenAPI:

```bash
# Terminal 1: Iniciar Function App
func start

# Terminal 2: Ejecutar tests
python test_search_endpoints.py
```

**Qué valida:**

- ✅ POST `/api/buscar-memoria`
- ✅ POST `/api/indexar-memoria`
- ✅ Flujo completo: indexar → buscar

## 📝 Agregar Endpoints a function_app.py

Agregar al final de `function_app.py`:

```python
# Endpoints de Búsqueda Semántica
from endpoints_search_memory import buscar_memoria_endpoint, indexar_memoria_endpoint

@app.route(route="buscar-memoria", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def buscar_memoria(req: func.HttpRequest) -> func.HttpResponse:
    """Buscar en memoria semántica"""
    try:
        req_body = req.get_json()
        resultado = buscar_memoria_endpoint(req_body)
        return func.HttpResponse(
            json.dumps(resultado, default=str),
            mimetype="application/json",
            status_code=200 if resultado.get("exito") else 400
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="indexar-memoria", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def indexar_memoria(req: func.HttpRequest) -> func.HttpResponse:
    """Indexar documentos en memoria semántica"""
    try:
        req_body = req.get_json()
        resultado = indexar_memoria_endpoint(req_body)
        return func.HttpResponse(
            json.dumps(resultado, default=str),
            mimetype="application/json",
            status_code=200 if resultado.get("exito") else 400
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

## 🔧 Actualizar OpenAPI

Agregar contenido de `openapi_search_endpoint.yaml` a tu `openapi.yaml` principal.

## 🎯 Flujo de Validación Completo

### Paso 1: Configurar Managed Identity

```powershell
.\setup_managed_identity_search.ps1
```

### Paso 2: Instalar Dependencias

```bash
pip install azure-search-documents>=11.4.0
```

### Paso 3: Test de Integración

```bash
python test_azure_search_integration.py
```

**Salida esperada:**

```
✅ TEST COMPLETADO EXITOSAMENTE
📊 Resumen:
   • Endpoint: https://boatrentalfoundrysearch.search.windows.net
   • Índice: agent-memory-index
   • Autenticación: Managed Identity (Azure)
   • Tests ejecutados: 7/7
   • Estado: ✅ FUNCIONAL
```

### Paso 4: Agregar Endpoints

Copiar código de endpoints a `function_app.py`

### Paso 5: Test de Endpoints HTTP

```bash
# Terminal 1
func start

# Terminal 2
python test_search_endpoints.py
```

**Salida esperada:**

```
✅ Búsqueda exitosa: 5 documentos
✅ Indexación exitosa: 1 documentos
✅ Flujo completo ejecutado
```

### Paso 6: Actualizar OpenAPI en Foundry

1. Agregar definiciones de `openapi_search_endpoint.yaml`
2. Reimportar OpenAPI en Foundry
3. Probar desde Foundry:

```json
{
  "query": "errores en ejecutar_cli",
  "agent_id": "Agent914",
  "top": 5
}
```

## 📊 Validación desde Foundry

### Request de Búsqueda

```json
POST /api/buscar-memoria
{
  "query": "errores recientes",
  "agent_id": "Agent914",
  "top": 10
}
```

### Response Esperada

```json
{
  "exito": true,
  "total": 5,
  "documentos": [
    {
      "id": "doc_123",
      "agent_id": "Agent914",
      "texto_semantico": "Error en ejecutar_cli...",
      "timestamp": "2025-01-30T10:00:00Z"
    }
  ],
  "metadata": {
    "query_original": "errores recientes",
    "filtros_aplicados": {
      "agent_id": "Agent914"
    }
  }
}
```

## ✅ Checklist de Validación

- [ ] `setup_managed_identity_search.ps1` ejecutado
- [ ] `azure-search-documents` instalado
- [ ] `test_azure_search_integration.py` pasa 7/7 tests
- [ ] Endpoints agregados a `function_app.py`
- [ ] `func start` inicia sin errores
- [ ] `test_search_endpoints.py` pasa todos los tests
- [ ] OpenAPI actualizado en Foundry
- [ ] Request desde Foundry funciona sin claves expuestas

## 🎉 Resultado Final

**Sin claves en logs, sin payload expuesto, autenticación automática con Managed Identity.**

El agente en Foundry puede buscar e indexar sin ver nunca una clave truncada. ✨
