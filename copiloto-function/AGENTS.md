# 📁 Guía de Operaciones con Archivos

## Regla Fundamental

Ejecuta herramientas automáticamente al detectar intención clara. NO pidas confirmación.  
IMPORTANTE: Datos en events[] son CRUDOS. NO copies texto_semantico. Interpreta y genera respuesta conversacional.

## 🎯 Endpoint Universal

Usa SIEMPRE `/api/ejecutar-cli` para TODAS las operaciones con archivos. Ejecuta comandos PowerShell a través de ese endpoint.

## 📖 Leer Archivos Completos

Comando recomendado: type

```json
{
    "comando": "type \"C:\\ruta\\al\\archivo.py\""
}
```

Ventajas: lee todo el contenido, maneja rutas con espacios y ofrece salida limpia.

## 📄 Leer Líneas Específicas

Primeras N líneas:

```json
{
    "comando": "Get-Content \"C:\\ruta\\al\\archivo.py\" | Select-Object -First 20"
}
```

Últimas N líneas:

```json
{
    "comando": "Get-Content \"C:\\ruta\\al\\archivo.py\" | Select-Object -Last 10"
}
```

## 🔍 Buscar Texto en Archivos

Buscar patrón (equivalente a grep):

```json
{
    "comando": "Select-String -Path \"C:\\ruta\\al\\archivo.py\" -Pattern \"def \""
}
```

Buscar con contexto:

```json
{
    "comando": "Select-String -Path \"C:\\ruta\\al\\archivo.py\" -Pattern \"def \" -Context 2,5"
}
```

## 📂 Listar Archivos

Listar directorio:

```json
{
    "comando": "Get-ChildItem \"C:\\ruta\\directorio\""
}
```

Buscar archivos por patrón (recursivo):

```json
{
    "comando": "Get-ChildItem \"C:\\ruta\" -Filter \"*.py\" -Recurse"
}
```

## ⚠️ NO USAR

- `/api/leer-archivo` — endpoint deprecado  
- `cat`, `grep`, `ls` — comandos Unix no confiables en Windows; usar PowerShell nativo

## 💡 Ejemplos Completos

Leer archivo de configuración:

```json
{
    "comando": "type \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py\""
}
```

Buscar funciones en archivo:

```json
{
    "comando": "Select-String -Path \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py\" -Pattern \"^def \" -Context 0,10"
}
```

Listar archivos Python en proyecto:

```json
{
    "comando": "Get-ChildItem \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\" -Filter \"*.py\" -Recurse | Select-Object FullName"
}
```

## 🎯 Reglas de Oro

1. SIEMPRE usa `/api/ejecutar-cli` para operaciones con archivos.  
2. SIEMPRE encierra rutas con espacios entre comillas dobles.  
3. SIEMPRE prefiere comandos PowerShell nativos (`type`, `Get-Content`, `Select-String`, `Get-ChildItem`).  
4. NUNCA uses comandos Unix (`cat`, `grep`, `ls`) en entornos Windows.

## 🚀 Redis Cache Monitoring para Agentes Foundry

### Endpoints Disponibles

#### 1. Health Check Rápido

**GET** `/api/redis-cache-health`

Uso: Verificar estado básico antes de operaciones críticas.

#### 2. Monitor Detallado  

**GET** `/api/redis-cache-monitor`

Uso: Análisis periódico de efectividad de cache.

### Flujo Recomendado para Agentes

```python
# Ejemplo de uso en agentes Foundry
async def agent_cache_monitoring():
    # 1. Health check antes de usar cache
    health = await get("/api/redis-cache-health")
    
    if health["status"] != "healthy":
        # Redis tiene problemas, omitir cache
        return await fallback_to_direct_model_call()
    
    # 2. Usar cache normalmente
    response = await post("/api/redis-model-wrapper", {
        "agent_id": "my_agent",
        "mensaje": user_message
    })
    
    # 3. Monitoreo periódico (ej: cada 100 requests)
    if request_count % 100 == 0:
        metrics = await get("/api/redis-cache-monitor")
        log_cache_metrics(metrics)
```

## Timeouts y Respuestas

- Timeouts: Lectura 10–15s, Escritura 20s, CLI 60s.  
- Respuestas: éxito (datos formateados), error (causa + solución), timeout (sugerir reintento).  
- Si status >= 400 o `ok:false`: incluir diagnóstico breve, solución concreta y comando para reintentar. Usa campos `error_code`, `cause`, `hint`, `next_steps` si están disponibles.
