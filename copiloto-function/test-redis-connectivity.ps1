# =======================================================================
# REDIS CONNECTIVITY TEST - AZURE FUNCTIONS FALLBACK
# =======================================================================
# Prueba la conectividad Redis usando Azure Functions como proxy
# cuando redis-cli no tiene soporte TLS

Write-Host "🔄 Probando conectividad Redis via Azure Functions..." -ForegroundColor Yellow

# Endpoints de Azure Functions para Redis
$redisHealthEndpoint = "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-health"
$redisMonitorEndpoint = "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-monitor"

function Test-RedisViaAzureFunctions {
    Write-Host "📡 Probando endpoint de salud Redis..."
    
    try {
        $healthResponse = Invoke-RestMethod -Uri $redisHealthEndpoint -Method GET -TimeoutSec 10
        
        Write-Host "✅ Respuesta de salud recibida:" -ForegroundColor Green
        Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
        Write-Host "   Ping: $($healthResponse.ping_result)" -ForegroundColor Cyan
        Write-Host "   Latencia: $($healthResponse.response_time_ms)ms" -ForegroundColor Cyan
        
        if ($healthResponse.status -eq "healthy") {
            Write-Host ""
            Write-Host "📊 Obteniendo métricas detalladas..."
            
            $monitorResponse = Invoke-RestMethod -Uri $redisMonitorEndpoint -Method GET -TimeoutSec 15
            
            Write-Host "✅ Métricas de Redis:" -ForegroundColor Green
            Write-Host "   Hit Ratio: $($monitorResponse.cache_hit_ratio)%" -ForegroundColor Cyan
            Write-Host "   Total Keys: $($monitorResponse.total_keys)" -ForegroundColor Cyan
            Write-Host "   Memory Used: $($monitorResponse.used_memory_human)" -ForegroundColor Cyan
            Write-Host "   Connected Clients: $($monitorResponse.connected_clients)" -ForegroundColor Cyan
            Write-Host "   Uptime: $($monitorResponse.uptime_in_seconds)s" -ForegroundColor Cyan
            
            return $true
        }
        else {
            Write-Host "❌ Redis no está saludable: $($healthResponse.status)" -ForegroundColor Red
            return $false
        }
        
    }
    catch {
        Write-Host "❌ Error conectando a Azure Functions:" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "💡 Posibles causas:" -ForegroundColor Yellow
        Write-Host "   • Azure Functions no está ejecutándose" -ForegroundColor Gray
        Write-Host "   • Problemas de red o DNS" -ForegroundColor Gray
        Write-Host "   • Credenciales Redis mal configuradas en Functions" -ForegroundColor Gray
        return $false
    }
}

function Test-DirectRedisConnection {
    Write-Host "🔍 Probando conexión directa a Redis..."
    
    # Verificar variables de entorno
    if (-not $env:REDIS_HOST) {
        Write-Host "❌ REDIS_HOST no configurado" -ForegroundColor Red
        return $false
    }
    
    if (-not $env:REDIS_KEY) {
        Write-Host "❌ REDIS_KEY no configurado" -ForegroundColor Red
        return $false
    }
    
    # Comprobar si redis-cli soporta TLS
    $redisCliPath = Get-Command "redis-cli" -ErrorAction SilentlyContinue
    if (-not $redisCliPath) {
        # Intentar ruta específica
        $redisCliPath = "C:\redis\redis-cli.exe"
        if (-not (Test-Path $redisCliPath)) {
            Write-Host "❌ redis-cli no encontrado" -ForegroundColor Red
            return $false
        }
    }
    else {
        $redisCliPath = $redisCliPath.Source
    }
    
    # Verificar versión y soporte TLS
    $redisVersion = & $redisCliPath --version 2>&1
    Write-Host "   Redis CLI: $redisVersion" -ForegroundColor Gray
    
    $helpOutput = & $redisCliPath --help 2>&1 | Out-String
    $hasTlsSupport = $helpOutput -match "--tls"
    
    if (-not $hasTlsSupport) {
        Write-Host "❌ Redis CLI no tiene soporte TLS" -ForegroundColor Red
        Write-Host "   Azure Redis Cache requiere TLS en puerto 6380" -ForegroundColor Yellow
        return $false
    }
    
    # Intentar conexión TLS
    try {
        Write-Host "🔐 Probando conexión TLS..."
        $pingResult = & $redisCliPath -h $env:REDIS_HOST -p $env:REDIS_PORT -a $env:REDIS_KEY --tls --insecure ping 2>&1
        
        if ($pingResult -match "PONG") {
            Write-Host "✅ Conexión TLS exitosa" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Redis no respondió correctamente: $pingResult" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error en conexión TLS: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =======================================================================
# EJECUTAR PRUEBAS
# =======================================================================

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 REDIS CONNECTIVITY TEST                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Mostrar configuración
Write-Host "🔧 Configuración actual:" -ForegroundColor White
Write-Host "   Host: $env:REDIS_HOST" -ForegroundColor Gray
Write-Host "   Port: $env:REDIS_PORT" -ForegroundColor Gray
Write-Host "   SSL:  $env:REDIS_SSL" -ForegroundColor Gray
Write-Host "   Key:  $(if($env:REDIS_KEY){'[CONFIGURADO]'}else{'[NO CONFIGURADO]'})" -ForegroundColor Gray
Write-Host ""

# Probar conexión directa primero
Write-Host "1️⃣ PRUEBA DIRECTA REDIS CLI" -ForegroundColor Yellow
$directSuccess = Test-DirectRedisConnection
Write-Host ""

# Si falla la directa, usar Azure Functions
if (-not $directSuccess) {
    Write-Host "2️⃣ PRUEBA VIA AZURE FUNCTIONS" -ForegroundColor Yellow
    $azureFunctionSuccess = Test-RedisViaAzureFunctions
    Write-Host ""
    
    if ($azureFunctionSuccess) {
        Write-Host "✅ Redis está funcionando (via Azure Functions)" -ForegroundColor Green
        Write-Host "💡 Usar MCP tools o Azure Functions para acceso Redis" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ Redis no accesible por ningún método" -ForegroundColor Red
    }
}
else {
    Write-Host "✅ Redis accesible directamente via CLI" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 PRÓXIMOS PASOS:" -ForegroundColor White
Write-Host "   • Para usar redis-cli con TLS, instalar versión 6.0+" -ForegroundColor Gray
Write-Host "   • Usar MCP tools para diagnósticos avanzados" -ForegroundColor Gray
Write-Host "   • Azure Functions como proxy para operaciones Redis" -ForegroundColor Gray
Write-Host ""