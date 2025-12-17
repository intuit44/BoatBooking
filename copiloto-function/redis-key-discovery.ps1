# =======================================================================
# REDIS KEY DISCOVERY - ENCONTRAR CLAVES REALES
# =======================================================================
# Escanea Redis para encontrar qué claves existen realmente
# Usa diferentes enfoques para descubrir patrones de claves

Write-Host "🔍 REDIS KEY DISCOVERY" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""

# Función para hacer solicitudes a Azure Functions
function Invoke-AzureFunctionRequest {
    param(
        [string]$Endpoint,
        [hashtable]$Body = @{},
        [string]$Method = "POST"
    )
    
    try {
        $baseUrl = "https://copiloto-semantico-func-us2.azurewebsites.net"
        $fullUrl = "$baseUrl$Endpoint"
        
        if ($Method -eq "GET") {
            return Invoke-RestMethod -Uri $fullUrl -Method GET -TimeoutSec 30
        }
        else {
            return Invoke-RestMethod -Uri $fullUrl -Method POST -Body ($Body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
        }
    }
    catch {
        Write-Host "❌ Error llamando a $Endpoint`: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Función para probar patrones de claves específicos
function Test-KeyPatterns {
    Write-Host "🔑 Probando patrones de claves conocidos..." -ForegroundColor Yellow
    
    $patterns = @(
        "*",           # Todas las claves
        "llm:*",       # Claves LLM
        "session:*",   # Claves de sesión  
        "agent:*",     # Claves de agente
        "cache:*",     # Claves de cache
        "memoria:*",   # Claves de memoria
        "cognitive:*", # Claves cognitivas
        "foundry:*",   # Claves de foundry
        "thread:*",    # Claves de hilo
        "global:*",    # Claves globales
        "user:*",      # Claves de usuario
        "temp:*",      # Claves temporales
        "redis:*",     # Claves internas de Redis
        "ai:*",        # Claves de AI
        "model:*",     # Claves de modelo
        "response:*",  # Claves de respuesta
        "context:*",   # Claves de contexto
        "history:*",   # Claves de historial
        "embedding:*", # Claves de embeddings
        "vector:*",    # Claves vectoriales
        "search:*",    # Claves de búsqueda
        "index:*",     # Claves de índice
        "meta:*",      # Claves de metadatos
        "config:*",    # Claves de configuración
        "state:*",     # Claves de estado
        "lock:*",      # Claves de bloqueo
        "queue:*",     # Claves de cola
        "job:*",       # Claves de trabajo
        "task:*",      # Claves de tarea
        "log:*",       # Claves de log
        "metric:*",    # Claves de métricas
        "stat:*",      # Claves estadísticas
        "count:*",     # Contadores
        "rate:*",      # Tasas
        "limit:*",     # Límites
        "quota:*",     # Cuotas
        "policy:*",    # Políticas
        "rule:*",      # Reglas
        "filter:*",    # Filtros
        "trigger:*",   # Disparadores
        "event:*",     # Eventos
        "notification:*", # Notificaciones
        "alert:*",     # Alertas
        "warning:*",   # Advertencias
        "error:*",     # Errores
        "debug:*",     # Debug
        "trace:*",     # Trazas
        "audit:*",     # Auditoría
        "security:*",  # Seguridad
        "auth:*",      # Autenticación
        "token:*",     # Tokens
        "session_*",   # Sesiones (guión bajo)
        "llm_*",       # LLM (guión bajo)  
        "agent_*",     # Agente (guión bajo)
        "user_*",      # Usuario (guión bajo)
        "temp_*",      # Temporal (guión bajo)
        "redis_*"      # Redis (guión bajo)
    )
    
    $foundKeys = @{}
    
    foreach ($pattern in $patterns) {
        Write-Host "   Escaneando patrón: $pattern" -ForegroundColor Gray
        
        # Intentar diferentes enfoques para encontrar claves
        try {
            # Método 1: A través del endpoint de diagnóstico
            $result = Invoke-AzureFunctionRequest -Endpoint "/api/redis-cache-monitor" -Method "GET"
            
            if ($result -and $result.sample_keys) {
                foreach ($key in $result.sample_keys.PSObject.Properties.Name) {
                    if ($key -like $pattern) {
                        $foundKeys[$key] = $result.sample_keys.$key
                        Write-Host "      ✅ Encontrada: $key" -ForegroundColor Green
                    }
                }
            }
            
        }
        catch {
            Write-Host "      ❌ Error escaneando $pattern`: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 100  # Evitar saturar el servidor
    }
    
    return $foundKeys
}

# Función para obtener información detallada de Redis
function Get-RedisDetailedInfo {
    Write-Host "📊 Obteniendo información detallada de Redis..." -ForegroundColor Yellow
    
    $health = Invoke-AzureFunctionRequest -Endpoint "/api/redis-cache-health" -Method "GET"
    $monitor = Invoke-AzureFunctionRequest -Endpoint "/api/redis-cache-monitor" -Method "GET"
    
    Write-Host "🔍 Información básica:" -ForegroundColor Cyan
    if ($health) {
        Write-Host "   Status: $($health.status)" -ForegroundColor White
        Write-Host "   Ping: $($health.checks.ping)" -ForegroundColor White
        Write-Host "   LLM Keys Count: $($health.checks.llm_keys_count)" -ForegroundColor White
        Write-Host "   Auto Sessions: $($health.checks.auto_sessions_count)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "📈 Estadísticas de rendimiento:" -ForegroundColor Cyan
    if ($monitor) {
        Write-Host "   DB Size: $($monitor.redis_stats.dbsize)" -ForegroundColor White
        Write-Host "   Used Memory: $($monitor.redis_stats.used_memory)" -ForegroundColor White
        Write-Host "   Hit Ratio: $($monitor.cache_effectiveness.hit_ratio)" -ForegroundColor White
        Write-Host "   Total Operations: $($monitor.cache_effectiveness.total_operations)" -ForegroundColor White
        
        Write-Host ""
        Write-Host "🔑 Key Counts por categoría:" -ForegroundColor Cyan
        if ($monitor.key_counts) {
            $monitor.key_counts.PSObject.Properties | ForEach-Object {
                Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor White
            }
        }
        
        Write-Host ""
        Write-Host "📋 Sample Keys:" -ForegroundColor Cyan
        if ($monitor.sample_keys -and $monitor.sample_keys.PSObject.Properties.Count -gt 0) {
            $monitor.sample_keys.PSObject.Properties | ForEach-Object {
                Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor White
            }
        }
        else {
            Write-Host "   ❌ No se encontraron sample keys" -ForegroundColor Red
        }
    }
    
    return @{
        Health  = $health
        Monitor = $monitor
    }
}

# Función para intentar diferentes enfoques de escaneo
function Try-AlternativeScanning {
    Write-Host "🔄 Intentando métodos alternativos de escaneo..." -ForegroundColor Yellow
    
    # Intentar con comandos Redis directos si fuera posible
    Write-Host "   Método 1: Escaneo directo de patrones básicos" -ForegroundColor Gray
    
    $basicPatterns = @("*", "session*", "llm*", "agent*", "cache*", "redis*")
    
    foreach ($pattern in $basicPatterns) {
        Write-Host "      Probando: $pattern" -ForegroundColor Gray
        
        # Aquí podrías intentar llamar endpoints específicos que hagan SCAN
        # Por ahora usamos el monitor endpoint
        try {
            $result = Invoke-AzureFunctionRequest -Endpoint "/api/redis-cache-monitor" -Method "GET"
            if ($result) {
                Write-Host "         Redis responde correctamente" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "         ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# =======================================================================
# EJECUTAR DESCUBRIMIENTO
# =======================================================================

Write-Host "🚀 Iniciando descubrimiento de claves Redis..." -ForegroundColor Green
Write-Host ""

# 1. Información básica
$redisInfo = Get-RedisDetailedInfo
Write-Host ""

# 2. Escaneo de patrones
$foundKeys = Test-KeyPatterns
Write-Host ""

# 3. Métodos alternativos
Try-AlternativeScanning
Write-Host ""

# 4. Resumen final
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    KEY DISCOVERY SUMMARY                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($foundKeys.Count -gt 0) {
    Write-Host "✅ CLAVES ENCONTRADAS:" -ForegroundColor Green
    $foundKeys.GetEnumerator() | ForEach-Object {
        Write-Host "   $($_.Key): $($_.Value)" -ForegroundColor White
    }
}
else {
    Write-Host "❌ NO SE ENCONTRARON CLAVES CON LOS PATRONES ESPERADOS" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 POSIBLES CAUSAS:" -ForegroundColor Yellow
    Write-Host "   • Las claves usan patrones diferentes a los esperados" -ForegroundColor Gray
    Write-Host "   • Las claves son internas de Redis y no visibles por SCAN" -ForegroundColor Gray
    Write-Host "   • Problema de permisos o configuración de acceso" -ForegroundColor Gray
    Write-Host "   • Las claves expiraron pero la memoria no se liberó" -ForegroundColor Gray
    Write-Host "   • Redis está configurado con múltiples bases de datos" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 PRÓXIMOS PASOS:" -ForegroundColor Yellow
    Write-Host "   • Revisar logs de la aplicación para ver qué claves se crean" -ForegroundColor Gray
    Write-Host "   • Verificar la configuración del wrapper Redis" -ForegroundColor Gray
    Write-Host "   • Comprobar si hay TTL muy corto en las claves" -ForegroundColor Gray
    Write-Host "   • Analizar el código que interactúa con Redis" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📊 ESTADÍSTICAS FINALES:" -ForegroundColor Cyan
if ($redisInfo.Monitor) {
    Write-Host "   DB Size: $($redisInfo.Monitor.redis_stats.dbsize) claves" -ForegroundColor White
    Write-Host "   Memoria usada: $($redisInfo.Monitor.redis_stats.used_memory)" -ForegroundColor White
    Write-Host "   Total operaciones: $($redisInfo.Monitor.cache_effectiveness.total_operations)" -ForegroundColor White
    Write-Host "   Hit ratio: $($redisInfo.Monitor.cache_effectiveness.hit_ratio)" -ForegroundColor White
}

Write-Host ""
Write-Host "🎯 Key Discovery completado" -ForegroundColor Green