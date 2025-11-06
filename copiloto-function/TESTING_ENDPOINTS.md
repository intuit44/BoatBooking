# 🧪 Guía de Testing de Endpoints

## ⚠️ Problema Común: Endpoints Decorados Devuelven `None`

### 🔴 Incorrecto (devuelve `None`)
```python
from endpoints.diagnostico_recursos import diagnostico_recursos_http

req = func.HttpRequest(...)
response = diagnostico_recursos_http(req)  # ❌ Devuelve None
```

**Por qué falla:**
- El decorador `@app.route()` solo **registra** la función en Azure Functions
- Llamar directamente a la función **no pasa por el runtime de Azure Functions**
- El wrapper de memoria **no se ejecuta**
- La función devuelve `None` porque espera ser manejada por el runtime

---

## ✅ Solución: Usar `app.get_functions()`

### Método Correcto
```python
from function_app import app
import azure.functions as func

# 1. Obtener la función registrada
func_obj = None
for f in app.get_functions():
    if f.get_function_name() == "diagnostico_recursos_http":
        func_obj = f
        break

# 2. Crear request
req = func.HttpRequest(
    method="POST",
    url="http://localhost:7071/api/diagnostico-recursos",
    headers={"Session-ID": "test123", "Agent-ID": "TestAgent"},
    params={},
    body=json.dumps({"recurso": "test-resource"}).encode('utf-8')
)

# 3. Invocar a través del runtime
response = func_obj.get_user_function()(req)  # ✅ Funciona correctamente
```

**Por qué funciona:**
- ✅ Pasa por el pipeline completo de Azure Functions
- ✅ El wrapper de memoria se ejecuta
- ✅ Todos los decoradores se aplican correctamente
- ✅ Devuelve `HttpResponse` válido

---

## 📋 Tests Disponibles

### Test Simple
```bash
python test_diagnostico_con_app.py
```
Valida que el endpoint funciona correctamente usando `app.get_functions()`.

### Test Completo de Memoria
```bash
python test_diagnostico_memoria.py
```
Valida el flujo completo:
1. ✅ Endpoint ejecutado
2. ✅ Guardado en Cosmos DB
3. ✅ Indexado en AI Search
4. ✅ Memoria recuperada en segunda llamada

### Test de Lógica Interna
```bash
python test_diagnostico_directo.py
```
Valida la lógica del endpoint sin decoradores (útil para debugging).

---

## 🎯 Patrón Recomendado para Nuevos Tests

```python
#!/usr/bin/env python3
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno
try:
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            if key not in os.environ:
                os.environ[key] = value
except Exception:
    pass

import azure.functions as func
from function_app import app

def test_mi_endpoint():
    # 1. Obtener función de app
    func_obj = None
    for f in app.get_functions():
        if f.get_function_name() == "mi_endpoint_http":
            func_obj = f
            break
    
    if not func_obj:
        print("[FAIL] Función no encontrada")
        return False
    
    # 2. Crear request
    req = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/mi-endpoint",
        headers={"Session-ID": "test123"},
        params={},
        body=json.dumps({"param": "value"}).encode('utf-8')
    )
    
    # 3. Invocar
    response = func_obj.get_user_function()(req)
    
    # 4. Validar
    if response is None:
        print("[FAIL] Response es None")
        return False
    
    data = json.loads(response.get_body().decode())
    print(f"[OK] Status: {response.status_code}")
    print(f"[OK] OK: {data.get('ok')}")
    
    return data.get('ok')

if __name__ == "__main__":
    success = test_mi_endpoint()
    sys.exit(0 if success else 1)
```

---

## 🔍 Debugging

### Ver logs del wrapper
El wrapper imprime:
```
>>> WRAPPER EJECUTANDOSE para: nombre_endpoint <<<
```

Si NO ves este mensaje, el wrapper no se está ejecutando.

### Ver logs del endpoint
Los endpoints imprimen:
```
>>> ENDPOINT nombre_endpoint_http INICIADO - Method: POST <<<
```

Si NO ves este mensaje, el endpoint no se está ejecutando.

---

## 📊 Estado de Validación

| Componente | Estado | Test |
|------------|--------|------|
| Endpoint ejecuta | ✅ | test_diagnostico_con_app.py |
| Wrapper se activa | ✅ | test_diagnostico_memoria.py |
| Cosmos DB guarda | ✅ | test_diagnostico_memoria.py |
| AI Search indexa | ✅ | test_diagnostico_memoria.py |
| Memoria recupera | ✅ | test_diagnostico_memoria.py |
| Lógica interna | ✅ | test_diagnostico_directo.py |

---

## 🚀 Ejecución en Producción

En producción, Azure Functions maneja automáticamente el routing:
```
HTTP Request → Azure Functions Runtime → @app.route → Wrapper → Endpoint
```

Los tests simulan este flujo usando `app.get_functions()`.
