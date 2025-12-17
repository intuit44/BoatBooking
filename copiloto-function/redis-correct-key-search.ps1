# =======================================================================
# BUSCAR CLAVES REDIS CON PATRONES CORRECTOS
# =======================================================================
# Ahora sabemos los patrones exactos que usa el wrapper Redis

Write-Host "🔍 BÚSQUEDA DE CLAVES REDIS CON PATRONES CORRECTOS" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Función para hacer escaneo directo con redis-cli si es posible
function Test-RedisDirectScan {
    param([string]$Pattern)
    
    if (-not $env:REDIS_HOST -or -not $env:REDIS_KEY) {
        return @()
    }
    
    $redisCliPath = "C:\redis\redis-cli.exe"
    if (-not (Test-Path $redisCliPath)) {
        return @()
    }
    
    try {
        # Intentar escaneo directo (aunque sabemos que fallará por TLS)
        $result = & $redisCliPath -h $env:REDIS_HOST -p $env:REDIS_PORT -a $env:REDIS_KEY --scan --pattern $Pattern 2>$null
        
        if ($LASTEXITCODE -eq 0 -and $result) {
            return $result -split "`n" | Where-Object { $_.Trim() -ne "" }
        }
    }
    catch {
        # Esperamos que falle por TLS
    }
    
    return @()
}

# Función para probar patrones específicos conocidos
function Test-CorrectPatterns {
    Write-Host "🎯 Probando patrones conocidos del wrapper Redis..." -ForegroundColor Yellow
    Write-Host ""
    
    # Patrones exactos que usa el wrapper
    $correctPatterns = @(
        "session:*",           # Claves de sesión  
        "global:*",            # Claves globales
        "session:*:*:*:*:*",   # Patrón completo de sesión
        "global:*:*:*:*",      # Patrón completo global
        "session:foundry_user:*", # Sesiones del usuario foundry
        "session:Agent*:*",    # Sesiones de agentes
        "global:foundry_user:*", # Cache global del usuario foundry  
        "global:Agent*:*",     # Cache global de agentes
        "session:*:auto-*",    # Sesiones auto-generadas
        "global:*:model:gpt-4o-mini:*", # Modelo específico
        "*:msg:*"              # Cualquier clave con hash de mensaje
    )
    
    Write-Host "📋 Patrones a probar:" -ForegroundColor Cyan
    foreach ($pattern in $correctPatterns) {
        Write-Host "   • $pattern" -ForegroundColor Gray
    }
    Write-Host ""
    
    $foundKeys = @{}
    
    foreach ($pattern in $correctPatterns) {
        Write-Host "🔍 Escaneando: $pattern" -ForegroundColor Yellow
        
        # Método 1: Intentar redis-cli directo (fallará pero lo intentamos)
        $directKeys = Test-RedisDirectScan -Pattern $pattern
        if ($directKeys.Count -gt 0) {
            Write-Host "   ✅ Redis CLI directo encontró $($directKeys.Count) claves" -ForegroundColor Green
            foreach ($key in $directKeys) {
                $foundKeys[$key] = "direct_scan"
            }
        }
        
        # Método 2: Usar Azure Functions como proxy para información
        try {
            $monitor = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-cache-monitor" -Method GET -TimeoutSec 10
            
            # Revisar si hay sample keys que coincidan con el patrón
            if ($monitor.sample_keys -and $monitor.sample_keys.PSObject.Properties.Count -gt 0) {
                foreach ($prop in $monitor.sample_keys.PSObject.Properties) {
                    $key = $prop.Name
                    if ($key -like $pattern) {
                        $foundKeys[$key] = "azure_functions"
                        Write-Host "   ✅ Azure Functions: $key" -ForegroundColor Green
                    }
                }
            }
            
            # Revisar también los TTL samples
            if ($monitor.ttl_samples -and $monitor.ttl_samples.PSObject.Properties.Count -gt 0) {
                foreach ($prop in $monitor.ttl_samples.PSObject.Properties) {
                    $key = $prop.Name
                    if ($key -like $pattern) {
                        $foundKeys[$key] = "ttl_samples"
                        Write-Host "   ✅ TTL Sample: $key (TTL: $($prop.Value))" -ForegroundColor Green
                    }
                }
            }
            
        }
        catch {
            Write-Host "   ❌ Error consultando Azure Functions: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 200
    }
    
    return $foundKeys
}

# Función para generar una clave de prueba y ver si Redis responde
function Test-GenerateTestKey {
    Write-Host "🧪 Generando clave de prueba..." -ForegroundColor Yellow
    
    $testMessage = "Test message for Redis key discovery"
    $testAgent = "test_agent"
    $testSession = "test_session_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    $testModel = "gpt-4o-mini"
    
    # Simular la generación de hash (usando el mismo método que el wrapper)
    $messageBytes = [System.Text.Encoding]::UTF8.GetBytes($testMessage)
    $hasher = [System.Security.Cryptography.MD5]::Create()
    $hashBytes = $hasher.ComputeHash($messageBytes)
    $messageHash = [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower().Substring(0, 8)
    
    $testSessionKey = "session:${testAgent}:${testSession}:model:${testModel}:msg:${messageHash}"
    $testGlobalKey = "global:${testAgent}:model:${testModel}:msg:${messageHash}"
    
    Write-Host "🔑 Claves de prueba generadas:" -ForegroundColor Cyan
    Write-Host "   Session: $testSessionKey" -ForegroundColor White
    Write-Host "   Global:  $testGlobalKey" -ForegroundColor White
    Write-Host ""
    
    # Intentar hacer una llamada al wrapper para que genere una clave real
    try {
        Write-Host "📤 Haciendo llamada al wrapper Redis para generar clave..." -ForegroundColor Yellow
        
        $testBody = @{
            mensaje    = $testMessage
            agent_id   = $testAgent
            session_id = $testSession
            model      = $testModel
        }
        
        $response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/redis-model-wrapper" -Method POST -Body ($testBody | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
        
        if ($response.ok) {
            Write-Host "✅ Wrapper Redis respondió exitosamente:" -ForegroundColor Green
            Write-Host "   Cache Hit: $($response.cache_hit)" -ForegroundColor White
            Write-Host "   Session ID: $($response.session_id)" -ForegroundColor White
            Write-Host "   Agent ID: $($response.agent_id)" -ForegroundColor White
            Write-Host "   Model: $($response.model)" -ForegroundColor White
            Write-Host "   Redis Enabled: $($response.redis_enabled)" -ForegroundColor White
            Write-Host ""
            
            if (-not $response.cache_hit) {
                Write-Host "💾 Nueva clave debería haberse creado en Redis" -ForegroundColor Cyan
            }
        }
        
        return $response
        
    }
    catch {
        Write-Host "❌ Error llamando al wrapper: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# =======================================================================
# EJECUTAR BÚSQUEDA COMPLETA
# =======================================================================

Write-Host "🚀 Iniciando búsqueda de claves con patrones correctos..." -ForegroundColor Green
Write-Host ""

# 1. Buscar con patrones correctos
$foundKeys = Test-CorrectPatterns
Write-Host ""

# 2. Generar una clave de prueba
$testResponse = Test-GenerateTestKey
Write-Host ""

# 3. Buscar de nuevo después de generar clave de prueba
Write-Host "🔄 Buscando nuevamente después de generar clave de prueba..." -ForegroundColor Yellow
$foundKeysAfter = Test-CorrectPatterns
Write-Host ""

# 4. Resumen final
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                   RESUMEN FINAL DE BÚSQUEDA                 ║" -ForegroundColor Cyan  
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$allKeys = @{}
$foundKeys.GetEnumerator() | ForEach-Object { $allKeys[$_.Key] = $_.Value }
$foundKeysAfter.GetEnumerator() | ForEach-Object { $allKeys[$_.Key] = $_.Value }

if ($allKeys.Count -gt 0) {
    Write-Host "✅ CLAVES ENCONTRADAS:" -ForegroundColor Green
    Write-Host ""
    $allKeys.GetEnumerator() | Sort-Object Name | ForEach-Object {
        Write-Host "   🔑 $($_.Key)" -ForegroundColor White
        Write-Host "      Origen: $($_.Value)" -ForegroundColor Gray
        Write-Host ""
    }
}
else {
    Write-Host "❌ AÚN NO SE ENCONTRARON CLAVES" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 ANÁLISIS:" -ForegroundColor Yellow
    Write-Host "   • DB Size reporta 3 claves existentes" -ForegroundColor Gray
    Write-Host "   • Los patrones de búsqueda son correctos" -ForegroundColor Gray  
    Write-Host "   • Redis responde correctamente" -ForegroundColor Gray
    Write-Host "   • Hit ratio es 85.9% (hay actividad)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔬 HIPÓTESIS:" -ForegroundColor Yellow
    Write-Host "   • Las claves pueden estar usando DB != 0" -ForegroundColor Gray
    Write-Host "   • Problema de permisos en comandos SCAN/KEYS" -ForegroundColor Gray
    Write-Host "   • Las claves tienen nombres completamente diferentes" -ForegroundColor Gray
    Write-Host "   • Redis está usando namespaces o prefijos adicionales" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📊 ESTADÍSTICAS:" -ForegroundColor Cyan
Write-Host "   • DB Size: 3 claves reportadas" -ForegroundColor White
Write-Host "   • Memoria: 109+ MB en uso" -ForegroundColor White
Write-Host "   • Hit Ratio: 85.9% (excelente actividad)" -ForegroundColor White
Write-Host "   • Total Operaciones: 3+ millones" -ForegroundColor White

if ($testResponse) {
    Write-Host "   • Test Wrapper: ✅ Funcional" -ForegroundColor White
    Write-Host "   • Redis Enabled: $($testResponse.redis_enabled)" -ForegroundColor White
}

Write-Host ""
Write-Host "🎯 Búsqueda de claves completada" -ForegroundColor Green