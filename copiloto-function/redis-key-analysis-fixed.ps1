# =======================================================================
# REDIS SCAN KEYS CORRECTO - CON PATRONES DESCUBIERTOS
# =======================================================================
# Busca claves Redis usando los patrones correctos con prefijo llm:

param(
    [switch]$Verbose,
    [int]$MaxKeys = 100
)

Write-Host "🔍 REDIS KEY SCAN - PATRONES CORRECTOS" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Función para obtener información detallada de una clave específica
function Get-KeyDetails {
    param([string]$Key)
    
    try {
        $monitor = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-monitor" -Method GET -TimeoutSec 10
        
        # Buscar en TTL samples
        if ($monitor.ttl_samples -and $monitor.ttl_samples.$Key) {
            return @{
                TTL    = $monitor.ttl_samples.$Key
                Source = "ttl_samples"
                Found  = $true
            }
        }
        
        # Buscar en sample keys  
        if ($monitor.sample_keys -and $monitor.sample_keys.$Key) {
            return @{
                Value  = $monitor.sample_keys.$Key
                Source = "sample_keys"
                Found  = $true
            }
        }
        
        return @{ Found = $false }
        
    }
    catch {
        return @{ Found = $false; Error = $_.Exception.Message }
    }
}

# Función para hacer múltiples llamadas y recolectar claves
function Get-AllRedisKeys {
    Write-Host "🔄 Recolectando claves a través de múltiples consultas..." -ForegroundColor Yellow
    
    $allKeys = @{}
    $attempts = 5
    
    for ($i = 1; $i -le $attempts; $i++) {
        Write-Host "   Intento $i/$attempts..." -ForegroundColor Gray
        
        try {
            $monitor = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-monitor" -Method GET -TimeoutSec 15
            
            # Recolectar de sample_keys
            if ($monitor.sample_keys) {
                $monitor.sample_keys.PSObject.Properties | ForEach-Object {
                    if (-not $allKeys.ContainsKey($_.Name)) {
                        $allKeys[$_.Name] = @{
                            Value   = $_.Value
                            Source  = "sample_keys"
                            Attempt = $i
                        }
                    }
                }
            }
            
            # Recolectar de ttl_samples 
            if ($monitor.ttl_samples) {
                $monitor.ttl_samples.PSObject.Properties | ForEach-Object {
                    if (-not $allKeys.ContainsKey($_.Name)) {
                        $allKeys[$_.Name] = @{
                            TTL     = $_.Value
                            Source  = "ttl_samples"
                            Attempt = $i
                        }
                    }
                    else {
                        # Agregar TTL si ya existe la clave
                        $allKeys[$_.Name].TTL = $_.Value
                    }
                }
            }
            
        }
        catch {
            Write-Host "      ❌ Error en intento $i : $($_.Exception.Message)" -ForegroundColor Red
        }
        
        if ($i -lt $attempts) {
            Start-Sleep -Seconds 2
        }
    }
    
    return $allKeys
}

# Función para generar claves de prueba y descubrir más patrones
function New-TestKeys {
    Write-Host "🧪 Generando claves de prueba para descubrir más patrones..." -ForegroundColor Yellow
    
    $testCases = @(
        @{ agent_id = "foundry_user"; session_id = "discovery_session_1"; mensaje = "Test message 1"; model = "gpt-4o-mini" },
        @{ agent_id = "Agent975"; session_id = "auto-test123"; mensaje = "Test message 2"; model = "gpt-4o-mini" },
        @{ agent_id = "GlobalAgent"; session_id = "manual_session"; mensaje = "Test message 3"; model = "gpt-4o-mini" }
    )
    
    foreach ($test in $testCases) {
        Write-Host "   Generando clave para agent=$($test.agent_id), session=$($test.session_id)..." -ForegroundColor Gray
        
        try {
            $body = $test | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-model-wrapper" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
            
            if ($response.ok) {
                Write-Host "      ✅ Cache hit: $($response.cache_hit), Session: $($response.session_id)" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 500
    }
}

# Función para analizar patrones de claves
function Get-KeyPatterns {
    param([hashtable]$Keys)
    
    Write-Host "🔬 Analizando patrones de claves..." -ForegroundColor Yellow
    Write-Host ""
    
    $patterns = @{}
    $prefixes = @{}
    $models = @{}
    $agents = @{}
    
    foreach ($key in $Keys.Keys) {
        # Analizar prefijos
        if ($key -match "^([^:]+):") {
            $prefix = $matches[1]
            if ($prefixes.ContainsKey($prefix)) {
                $prefixes[$prefix] = $prefixes[$prefix] + 1
            }
            else {
                $prefixes[$prefix] = 1
            }
        }
        
        # Analizar modelos
        if ($key -match ":model:([^:]+):") {
            $model = $matches[1]
            if ($models.ContainsKey($model)) {
                $models[$model] = $models[$model] + 1
            }
            else {
                $models[$model] = 1
            }
        }
        
        # Analizar agentes
        if ($key -match ":(session|global):([^:]+):") {
            $agent = $matches[2]
            if ($agents.ContainsKey($agent)) {
                $agents[$agent] = $agents[$agent] + 1
            }
            else {
                $agents[$agent] = 1
            }
        }
        
        # Analizar patrones generales
        $pattern = $key -replace ":[a-f0-9]{8,}$", ":HASH" -replace ":[a-f0-9]{32,}$", ":HASH"
        if ($patterns.ContainsKey($pattern)) {
            $patterns[$pattern] = $patterns[$pattern] + 1
        }
        else {
            $patterns[$pattern] = 1
        }
    }
    
    Write-Host "📊 ANÁLISIS DE PATRONES:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "🏷️  Prefijos encontrados:" -ForegroundColor Yellow
    $prefixes.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        Write-Host "   $($_.Key): $($_.Value) claves" -ForegroundColor White
    }
    Write-Host ""
    
    Write-Host "🤖 Modelos en uso:" -ForegroundColor Yellow
    $models.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        Write-Host "   $($_.Key): $($_.Value) claves" -ForegroundColor White
    }
    Write-Host ""
    
    Write-Host "👤 Agentes activos:" -ForegroundColor Yellow
    $agents.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        Write-Host "   $($_.Key): $($_.Value) claves" -ForegroundColor White
    }
    Write-Host ""
    
    Write-Host "🔍 Patrones de claves:" -ForegroundColor Yellow
    $patterns.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        Write-Host "   $($_.Key)" -ForegroundColor White
        Write-Host "     Ocurrencias: $($_.Value)" -ForegroundColor Gray
    }
}

# =======================================================================
# EJECUTAR ANÁLISIS COMPLETO
# =======================================================================

Write-Host "🚀 Iniciando análisis completo de claves Redis..." -ForegroundColor Green
Write-Host ""

# 1. Generar claves de prueba para tener más datos
New-TestKeys
Write-Host ""

# 2. Recolectar todas las claves posibles
$allKeys = Get-AllRedisKeys
Write-Host ""

# 3. Mostrar claves encontradas
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                     CLAVES ENCONTRADAS                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($allKeys.Count -gt 0) {
    Write-Host "✅ TOTAL CLAVES ENCONTRADAS: $($allKeys.Count)" -ForegroundColor Green
    Write-Host ""
    
    $counter = 0
    $allKeys.GetEnumerator() | Sort-Object Name | ForEach-Object {
        $counter++
        if ($counter -le $MaxKeys) {
            Write-Host "🔑 $($_.Key)" -ForegroundColor White
            
            if ($_.Value.TTL) {
                $hours = [math]::Round($_.Value.TTL / 3600, 1)
                Write-Host "   TTL: $($_.Value.TTL)s ($hours h)" -ForegroundColor Gray
            }
            if ($_.Value.Value) {
                $valueJson = $_.Value.Value | ConvertTo-Json -Depth 1 -Compress
                $valuePreview = $valueJson.Substring(0, [math]::Min(100, $valueJson.Length))
                Write-Host "   Value: $valuePreview..." -ForegroundColor Gray
            }
            Write-Host "   Source: $($_.Value.Source) (intento $($_.Value.Attempt))" -ForegroundColor DarkGray
            Write-Host ""
        }
    }
    
    if ($allKeys.Count -gt $MaxKeys) {
        Write-Host "... y $($allKeys.Count - $MaxKeys) claves más (usa -MaxKeys para ver más)" -ForegroundColor Yellow
        Write-Host ""
    }
    
    # 4. Análisis de patrones
    Get-KeyPatterns -Keys $allKeys
    
}
else {
    Write-Host "❌ NO SE ENCONTRARON CLAVES" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Esto es extraño porque:" -ForegroundColor Yellow
    Write-Host "   • DB Size reporta 3+ claves" -ForegroundColor Gray
    Write-Host "   • Hit ratio es 85.9%" -ForegroundColor Gray
    Write-Host "   • Redis está activo con 3M+ operaciones" -ForegroundColor Gray
    Write-Host "   • El wrapper funciona correctamente" -ForegroundColor Gray
}

# 5. Obtener estadísticas finales
try {
    Write-Host ""
    Write-Host "📊 ESTADÍSTICAS REDIS ACTUALES:" -ForegroundColor Cyan
    $monitor = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-monitor" -Method GET -TimeoutSec 10
    
    Write-Host "   DB Size: $($monitor.redis_stats.dbsize)" -ForegroundColor White
    Write-Host "   Used Memory: $($monitor.redis_stats.used_memory)" -ForegroundColor White
    Write-Host "   Hit Ratio: $($monitor.cache_effectiveness.hit_ratio)" -ForegroundColor White
    Write-Host "   Total Operations: $($monitor.cache_effectiveness.total_operations)" -ForegroundColor White
    
    if ($monitor.key_counts) {
        Write-Host ""
        Write-Host "🔢 Conteos por categoría:" -ForegroundColor Yellow
        $monitor.key_counts.PSObject.Properties | ForEach-Object {
            Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor White
        }
    }
    
}
catch {
    Write-Host "❌ Error obteniendo estadísticas finales: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 Análisis de claves Redis completado" -ForegroundColor Green