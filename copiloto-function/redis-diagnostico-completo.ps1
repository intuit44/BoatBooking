#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script completo de diagnóstico Redis con escaneo de claves y análisis detallado
.DESCRIPTION
    Realiza diagnóstico exhaustivo de Redis incluyendo:
    - Conexión y health check
    - Info del servidor y estadísticas
    - Escaneo completo de claves con patrones
    - Análisis de memoria y rendimiento
    - Diagnóstico de cache hit/miss
    - Reporte consolidado con recomendaciones
.PARAMETER RedisHost
    Host de Redis (default: desde variable de entorno)
.PARAMETER RedisPort  
    Puerto de Redis (default: desde variable de entorno)
.PARAMETER RedisPassword
    Password de Redis (default: desde variable de entorno)
.PARAMETER UseTLS
    Usar conexión TLS (default: true para Azure Redis)
.PARAMETER ScanLimit
    Límite de claves a escanear (default: 1000)
.PARAMETER OutputFile
    Archivo para guardar el reporte (opcional)
.EXAMPLE
    .\redis-diagnostico-completo.ps1
.EXAMPLE
    .\redis-diagnostico-completo.ps1 -ScanLimit 5000 -OutputFile "redis-report.json"
#>

param(
    [string]$RedisHost = $env:REDIS_HOST,
    [int]$RedisPort = [int]($env:REDIS_PORT ?? 6379),
    [string]$RedisPassword = ($env:REDIS_KEY ?? $env:REDIS_PASSWORD),
    [bool]$UseTLS = ($env:REDIS_SSL -eq "1" -or $env:REDIS_TLS -eq "1"),
    [int]$ScanLimit = 1000,
    [string]$OutputFile = ""
)

# Colores para output
$Colors = @{
    Success = 'Green'
    Warning = 'Yellow'
    Error   = 'Red'
    Info    = 'Cyan'
    Header  = 'Magenta'
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Get-RedisCliPath {
    # Intentar encontrar redis-cli
    $paths = @(
        "C:\redis\redis-cli.exe",
        "C:\Program Files\Redis\redis-cli.exe", 
        "C:\Program Files (x86)\Redis\redis-cli.exe",
        "C:\tools\redis\redis-cli.exe"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Intentar which/where
    $whichResult = Get-Command redis-cli -ErrorAction SilentlyContinue
    if ($whichResult) {
        return $whichResult.Source
    }
    
    return $null
}

function Test-RedisCliVersion {
    param([string]$RedisCliPath)
    
    try {
        $versionOutput = & $RedisCliPath --version 2>&1
        $supportsTLS = $false
        
        if ($versionOutput -match "redis-cli (\d+\.\d+\.\d+)") {
            $version = $matches[1]
            $versionParts = $version.Split('.')
            $major = [int]$versionParts[0]
            $minor = [int]$versionParts[1]
            
            # TLS support desde 6.0.0+
            $supportsTLS = ($major -gt 6) -or ($major -eq 6 -and $minor -ge 0)
        }
        
        return @{
            Version     = $version ?? "unknown"
            SupportsTLS = $supportsTLS
            Output      = $versionOutput
        }
    }
    catch {
        return @{
            Version     = "unknown"
            SupportsTLS = $false
            Output      = $_.Exception.Message
        }
    }
}

function Invoke-RedisCommand {
    param(
        [string]$RedisCliPath,
        [string]$Command,
        [bool]$IncludeTLS = $false
    )
    
    $args = @()
    
    if ($RedisHost) { $args += @("-h", $RedisHost) }
    if ($RedisPort -and $RedisPort -ne 6379) { $args += @("-p", $RedisPort) }
    if ($RedisPassword) { $args += @("-a", $RedisPassword) }
    if ($IncludeTLS) { $args += @("--tls") }
    
    $args += $Command.Split(' ')
    
    try {
        $result = & $RedisCliPath @args 2>&1
        return @{
            Success  = $LASTEXITCODE -eq 0
            Output   = $result
            ExitCode = $LASTEXITCODE
        }
    }
    catch {
        return @{
            Success  = $false
            Output   = $_.Exception.Message
            ExitCode = -1
        }
    }
}

function Get-RedisInfo {
    param([string]$RedisCliPath, [bool]$UseTLS)
    
    Write-ColorOutput "🔍 Obteniendo información del servidor Redis..." -Color Info
    
    $commands = @(
        @{ Name = "PING"; Command = "PING" },
        @{ Name = "INFO"; Command = "INFO" },
        @{ Name = "INFO_SERVER"; Command = "INFO SERVER" },
        @{ Name = "INFO_MEMORY"; Command = "INFO MEMORY" },
        @{ Name = "INFO_STATS"; Command = "INFO STATS" },
        @{ Name = "INFO_REPLICATION"; Command = "INFO REPLICATION" },
        @{ Name = "CONFIG_GET_MAXMEMORY"; Command = "CONFIG GET maxmemory*" },
        @{ Name = "DBSIZE"; Command = "DBSIZE" }
    )
    
    $results = @{}
    
    foreach ($cmd in $commands) {
        Write-Host "  • Ejecutando $($cmd.Name)..." -ForegroundColor Gray
        $result = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command $cmd.Command -IncludeTLS $UseTLS
        $results[$cmd.Name] = $result
        
        if ($result.Success) {
            Write-Host "    ✓ OK" -ForegroundColor Green
        }
        else {
            Write-Host "    ✗ Error: $($result.Output)" -ForegroundColor Red
        }
    }
    
    return $results
}

function Get-RedisKeys {
    param([string]$RedisCliPath, [bool]$UseTLS, [int]$Limit)
    
    Write-ColorOutput "🔑 Escaneando claves Redis (límite: $Limit)..." -Color Info
    
    # Patrones comunes a buscar
    $patterns = @(
        "*",
        "llm:*",
        "session:*", 
        "agent:*",
        "cache:*",
        "memoria:*",
        "cognitive:*",
        "foundry:*"
    )
    
    $keyResults = @{}
    $totalKeys = 0
    
    foreach ($pattern in $patterns) {
        Write-Host "  • Buscando patrón: $pattern" -ForegroundColor Gray
        
        # Usar SCAN en lugar de KEYS para mejor rendimiento
        $scanResult = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command "SCAN 0 MATCH $pattern COUNT 100" -IncludeTLS $UseTLS
        
        if ($scanResult.Success) {
            $keys = $scanResult.Output | Where-Object { $_ -and $_ -notmatch "^\d+$" }
            $keyCount = ($keys | Measure-Object).Count
            $totalKeys += $keyCount
            
            $keyResults[$pattern] = @{
                Count  = $keyCount
                Keys   = $keys | Select-Object -First 20  # Primeras 20 para muestra
                Sample = $keys | Select-Object -First 5
            }
            
            Write-Host "    ✓ Encontradas: $keyCount claves" -ForegroundColor Green
        }
        else {
            $keyResults[$pattern] = @{
                Count = 0
                Keys  = @()
                Error = $scanResult.Output
            }
            Write-Host "    ✗ Error: $($scanResult.Output)" -ForegroundColor Red
        }
        
        if ($totalKeys -ge $Limit) {
            Write-Host "  ⚠️ Límite de $Limit claves alcanzado" -ForegroundColor Yellow
            break
        }
    }
    
    return $keyResults
}

function Get-RedisMemoryAnalysis {
    param([string]$RedisCliPath, [bool]$UseTLS, $KeyResults)
    
    Write-ColorOutput "💾 Analizando uso de memoria..." -Color Info
    
    $memoryInfo = @{}
    
    # Obtener información detallada de memoria
    $memoryResult = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command "INFO MEMORY" -IncludeTLS $UseTLS
    
    if ($memoryResult.Success) {
        $memoryLines = $memoryResult.Output -split "`n"
        foreach ($line in $memoryLines) {
            if ($line -match "^([^:]+):(.+)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $memoryInfo[$key] = $value
            }
        }
    }
    
    # Analizar algunas claves individuales para tamaño
    $sampleAnalysis = @()
    foreach ($pattern in $KeyResults.Keys) {
        $keys = $KeyResults[$pattern].Sample
        foreach ($key in $keys) {
            if ($key) {
                $typeResult = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command "TYPE $key" -IncludeTLS $UseTLS
                $ttlResult = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command "TTL $key" -IncludeTLS $UseTLS
                
                $sampleAnalysis += @{
                    Key     = $key
                    Type    = if ($typeResult.Success) { $typeResult.Output.Trim() } else { "unknown" }
                    TTL     = if ($ttlResult.Success) { $ttlResult.Output.Trim() } else { "unknown" }
                    Pattern = $pattern
                }
            }
        }
    }
    
    return @{
        MemoryInfo     = $memoryInfo
        SampleAnalysis = $sampleAnalysis
    }
}

function Get-RedisCacheStats {
    param([string]$RedisCliPath, [bool]$UseTLS)
    
    Write-ColorOutput "📊 Analizando estadísticas de cache..." -Color Info
    
    $statsResult = Invoke-RedisCommand -RedisCliPath $RedisCliPath -Command "INFO STATS" -IncludeTLS $UseTLS
    
    $stats = @{}
    if ($statsResult.Success) {
        $statsLines = $statsResult.Output -split "`n"
        foreach ($line in $statsLines) {
            if ($line -match "^([^:]+):(.+)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $stats[$key] = $value
            }
        }
    }
    
    # Calcular métricas derivadas
    $totalCommands = [long]($stats["total_commands_processed"] ?? 0)
    $keyspaceHits = [long]($stats["keyspace_hits"] ?? 0)
    $keyspaceMisses = [long]($stats["keyspace_misses"] ?? 0)
    
    $hitRatio = if (($keyspaceHits + $keyspaceMisses) -gt 0) {
        [math]::Round(($keyspaceHits / ($keyspaceHits + $keyspaceMisses)) * 100, 2)
    }
    else { 0 }
    
    return @{
        RawStats = $stats
        Metrics  = @{
            TotalCommands  = $totalCommands
            KeyspaceHits   = $keyspaceHits
            KeyspaceMisses = $keyspaceMisses
            HitRatio       = $hitRatio
        }
    }
}

function New-DiagnosticReport {
    param($RedisInfo, $KeyResults, $MemoryAnalysis, $CacheStats, $CliInfo)
    
    $report = @{
        Timestamp        = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        RedisConnection  = @{
            Host   = $RedisHost
            Port   = $RedisPort
            TLS    = $UseTLS
            Status = if ($RedisInfo.PING.Success) { "Connected" } else { "Failed" }
        }
        RedisCliInfo     = $CliInfo
        ServerInfo       = $RedisInfo
        KeyAnalysis      = @{
            TotalScanned     = ($KeyResults.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
            PatternBreakdown = $KeyResults
        }
        MemoryUsage      = $MemoryAnalysis
        CachePerformance = $CacheStats
        Recommendations  = @()
        HealthScore      = 0
    }
    
    # Generar recomendaciones
    $recommendations = @()
    $healthScore = 100
    
    # Análisis de conectividad
    if (-not $RedisInfo.PING.Success) {
        $recommendations += "❌ Redis no responde - verificar conexión, credenciales y firewall"
        $healthScore -= 50
    }
    else {
        $recommendations += "✅ Conexión Redis exitosa"
    }
    
    # Análisis de rendimiento de cache
    $hitRatio = $CacheStats.Metrics.HitRatio
    if ($hitRatio -lt 30) {
        $recommendations += "⚠️ Hit ratio muy bajo ($hitRatio%) - revisar patrones de cache"
        $healthScore -= 20
    }
    elseif ($hitRatio -lt 60) {
        $recommendations += "⚡ Hit ratio moderado ($hitRatio%) - oportunidades de mejora"
        $healthScore -= 10
    }
    else {
        $recommendations += "✅ Hit ratio excelente ($hitRatio%)"
    }
    
    # Análisis de claves
    $totalKeys = $report.KeyAnalysis.TotalScanned
    if ($totalKeys -eq 0) {
        $recommendations += "ℹ️ No se encontraron claves - cache vacía o patrones incorrectos"
    }
    elseif ($totalKeys -lt 100) {
        $recommendations += "ℹ️ Pocas claves en cache ($totalKeys) - cache en crecimiento"
    }
    else {
        $recommendations += "✅ Cache activa con $totalKeys claves"
    }
    
    # Análisis de memoria
    if ($MemoryAnalysis.MemoryInfo.ContainsKey("used_memory_human")) {
        $memoryUsed = $MemoryAnalysis.MemoryInfo["used_memory_human"]
        $recommendations += "💾 Uso de memoria: $memoryUsed"
    }
    
    # Análisis de TLS
    if ($UseTLS -and -not $CliInfo.SupportsTLS) {
        $recommendations += "⚠️ TLS requerido pero Redis CLI no lo soporta - actualizar a versión 6.0+"
        $healthScore -= 15
    }
    
    $report.Recommendations = $recommendations
    $report.HealthScore = [math]::Max(0, $healthScore)
    
    return $report
}

function Show-DiagnosticReport {
    param($Report)
    
    Write-Host ""
    Write-ColorOutput "╔══════════════════════════════════════════════════════════════╗" -Color Header
    Write-ColorOutput "║                    REDIS DIAGNOSTIC REPORT                  ║" -Color Header
    Write-ColorOutput "╚══════════════════════════════════════════════════════════════╝" -Color Header
    Write-Host ""
    
    # Conexión
    Write-ColorOutput "🔌 CONEXIÓN" -Color Header
    Write-Host "   Host: $($Report.RedisConnection.Host):$($Report.RedisConnection.Port)"
    Write-Host "   TLS: $($Report.RedisConnection.TLS)"
    Write-Host "   Status: $($Report.RedisConnection.Status)"
    Write-Host ""
    
    # Redis CLI
    Write-ColorOutput "🛠️ REDIS CLI" -Color Header
    Write-Host "   Versión: $($Report.RedisCliInfo.Version)"
    Write-Host "   Soporte TLS: $($Report.RedisCliInfo.SupportsTLS)"
    Write-Host ""
    
    # Claves
    Write-ColorOutput "🔑 ANÁLISIS DE CLAVES" -Color Header
    Write-Host "   Total escaneadas: $($Report.KeyAnalysis.TotalScanned)"
    foreach ($pattern in $Report.KeyAnalysis.PatternBreakdown.Keys) {
        $count = $Report.KeyAnalysis.PatternBreakdown[$pattern].Count
        Write-Host "   $pattern : $count claves"
    }
    Write-Host ""
    
    # Cache Performance
    Write-ColorOutput "📊 RENDIMIENTO CACHE" -Color Header
    $metrics = $Report.CachePerformance.Metrics
    Write-Host "   Hit Ratio: $($metrics.HitRatio)%"
    Write-Host "   Hits: $($metrics.KeyspaceHits)"
    Write-Host "   Misses: $($metrics.KeyspaceMisses)"
    Write-Host "   Total Commands: $($metrics.TotalCommands)"
    Write-Host ""
    
    # Health Score
    $healthColor = if ($Report.HealthScore -ge 80) { "Success" } 
    elseif ($Report.HealthScore -ge 60) { "Warning" }
    else { "Error" }
    Write-ColorOutput "💯 HEALTH SCORE: $($Report.HealthScore)/100" -Color $healthColor
    Write-Host ""
    
    # Recomendaciones
    Write-ColorOutput "💡 RECOMENDACIONES" -Color Header
    foreach ($rec in $Report.Recommendations) {
        Write-Host "   $rec"
    }
    Write-Host ""
    
    Write-ColorOutput "Diagnóstico completado: $($Report.Timestamp)" -Color Info
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-ColorOutput "🚀 INICIANDO DIAGNÓSTICO COMPLETO DE REDIS" -Color Header
Write-Host ""

# Validar parámetros
if (-not $RedisHost) {
    Write-ColorOutput "❌ Error: REDIS_HOST no configurado" -Color Error
    Write-Host "Configura la variable de entorno REDIS_HOST o pásala como parámetro"
    exit 1
}

# Encontrar Redis CLI
Write-ColorOutput "🔍 Buscando Redis CLI..." -Color Info
$redisCliPath = Get-RedisCliPath

if (-not $redisCliPath) {
    Write-ColorOutput "❌ Error: redis-cli no encontrado" -Color Error
    Write-Host "Instala Redis CLI o asegúrate de que esté en el PATH"
    exit 1
}

Write-ColorOutput "✅ Redis CLI encontrado: $redisCliPath" -Color Success

# Verificar versión y soporte TLS
$cliInfo = Test-RedisCliVersion -RedisCliPath $redisCliPath
Write-Host "Versión: $($cliInfo.Version) | TLS Support: $($cliInfo.SupportsTLS)"

if ($UseTLS -and -not $cliInfo.SupportsTLS) {
    Write-ColorOutput "⚠️ Advertencia: TLS requerido pero Redis CLI no lo soporta" -Color Warning
    Write-Host "Continuando sin TLS..."
    $UseTLS = $false
}

Write-Host ""

# Ejecutar diagnósticos
try {
    $redisInfo = Get-RedisInfo -RedisCliPath $redisCliPath -UseTLS $UseTLS
    $keyResults = Get-RedisKeys -RedisCliPath $redisCliPath -UseTLS $UseTLS -Limit $ScanLimit
    $memoryAnalysis = Get-RedisMemoryAnalysis -RedisCliPath $redisCliPath -UseTLS $UseTLS -KeyResults $keyResults
    $cacheStats = Get-RedisCacheStats -RedisCliPath $redisCliPath -UseTLS $UseTLS
    
    # Generar reporte
    $report = New-DiagnosticReport -RedisInfo $redisInfo -KeyResults $keyResults -MemoryAnalysis $memoryAnalysis -CacheStats $cacheStats -CliInfo $cliInfo
    
    # Mostrar reporte
    Show-DiagnosticReport -Report $report
    
    # Guardar a archivo si se especifica
    if ($OutputFile) {
        $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-ColorOutput "💾 Reporte guardado en: $OutputFile" -Color Success
    }
    
}
catch {
    Write-ColorOutput "❌ Error durante el diagnóstico: $($_.Exception.Message)" -Color Error
    exit 1
}

Write-Host ""
Write-ColorOutput "🎉 Diagnóstico completado exitosamente" -Color Success