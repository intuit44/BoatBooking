#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script rápido de diagnóstico Redis para uso cotidiano
.DESCRIPTION
    Versión simplificada del diagnóstico Redis para checks rápidos
.EXAMPLE
    .\redis-quick-check.ps1
.EXAMPLE  
    .\redis-quick-check.ps1 -Verbose
#>

param(
    [switch]$Verbose
)

# Configuración desde variables de entorno
$RedisHost = $env:REDIS_HOST
$RedisPort = $env:REDIS_PORT ?? 6379
$RedisPassword = $env:REDIS_KEY ?? $env:REDIS_PASSWORD
$UseTLS = ($env:REDIS_SSL -eq "1" -or $env:REDIS_TLS -eq "1")

function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    
    $color = switch ($Status) {
        "OK" { "Green" }
        "WARN" { "Yellow" }
        "ERROR" { "Red" }
        default { "Cyan" }
    }
    
    $prefix = switch ($Status) {
        "OK" { "✅" }
        "WARN" { "⚠️" }
        "ERROR" { "❌" }
        default { "ℹ️" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Get-RedisCliCommand {
    # Construir comando redis-cli
    $cmd = "redis-cli"
    
    if ($RedisHost) { $cmd += " -h $RedisHost" }
    if ($RedisPort -ne 6379) { $cmd += " -p $RedisPort" }
    if ($RedisPassword) { $cmd += " -a `"$RedisPassword`"" }
    if ($UseTLS) { $cmd += " --tls" }
    
    return $cmd
}

function Test-RedisConnection {
    Write-Status "Probando conexión Redis..." "INFO"
    
    $cmd = Get-RedisCliCommand
    $fullCmd = "$cmd PING"
    
    try {
        $result = Invoke-Expression $fullCmd 2>&1
        if ($result -match "PONG") {
            Write-Status "Conexión exitosa" "OK"
            return $true
        }
        else {
            Write-Status "Conexión falló: $result" "ERROR"
            return $false
        }
    }
    catch {
        Write-Status "Error de conexión: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Get-QuickStats {
    Write-Status "Obteniendo estadísticas rápidas..." "INFO"
    
    $cmd = Get-RedisCliCommand
    
    # DBSIZE
    try {
        $dbsize = Invoke-Expression "$cmd DBSIZE" 2>&1
        Write-Status "Total de claves: $dbsize" "OK"
    }
    catch {
        Write-Status "No se pudo obtener DBSIZE" "WARN"
    }
    
    # INFO stats básico
    try {
        $stats = Invoke-Expression "$cmd INFO STATS" 2>&1
        
        $hits = ($stats | Select-String "keyspace_hits:(\d+)").Matches.Groups[1].Value ?? "0"
        $misses = ($stats | Select-String "keyspace_misses:(\d+)").Matches.Groups[1].Value ?? "0"
        
        $totalRequests = [long]$hits + [long]$misses
        if ($totalRequests -gt 0) {
            $hitRatio = [math]::Round(([long]$hits / $totalRequests) * 100, 1)
            Write-Status "Cache Hit Ratio: $hitRatio% ($hits hits, $misses misses)" "OK"
        }
        else {
            Write-Status "No hay estadísticas de cache disponibles" "WARN"
        }
    }
    catch {
        Write-Status "No se pudieron obtener estadísticas" "WARN"
    }
}

function Get-SampleKeys {
    Write-Status "Muestreando claves..." "INFO"
    
    $cmd = Get-RedisCliCommand
    $patterns = @("llm:*", "session:*", "agent:*", "cache:*")
    
    foreach ($pattern in $patterns) {
        try {
            $keys = Invoke-Expression "$cmd --scan --pattern `"$pattern`" --count 5" 2>&1
            $keyCount = ($keys | Measure-Object).Count
            
            if ($keyCount -gt 0) {
                Write-Status "$pattern -> $keyCount claves" "OK"
                if ($Verbose) {
                    $keys | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
                }
            }
        }
        catch {
            # Ignorar errores de patrones
        }
    }
}

function Get-MemoryInfo {
    Write-Status "Información de memoria..." "INFO"
    
    $cmd = Get-RedisCliCommand
    
    try {
        $memInfo = Invoke-Expression "$cmd INFO MEMORY" 2>&1
        
        $usedMemory = ($memInfo | Select-String "used_memory_human:(.+)").Matches.Groups[1].Value?.Trim()
        $maxMemory = ($memInfo | Select-String "maxmemory_human:(.+)").Matches.Groups[1].Value?.Trim()
        
        if ($usedMemory) {
            $memMsg = "Memoria usada: $usedMemory"
            if ($maxMemory -and $maxMemory -ne "0B") {
                $memMsg += " de $maxMemory"
            }
            Write-Status $memMsg "OK"
        }
    }
    catch {
        Write-Status "No se pudo obtener info de memoria" "WARN"
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host ""
Write-Host "🔍 REDIS QUICK CHECK" -ForegroundColor Magenta
Write-Host "===================" -ForegroundColor Magenta
Write-Host ""

# Verificar configuración
if (-not $RedisHost) {
    Write-Status "REDIS_HOST no configurado" "ERROR"
    exit 1
}

Write-Status "Redis: ${RedisHost}:${RedisPort} (TLS: $UseTLS)" "INFO"
Write-Host ""

# Ejecutar checks
$connected = Test-RedisConnection

if ($connected) {
    Get-QuickStats
    Get-SampleKeys  
    Get-MemoryInfo
}
else {
    Write-Status "Conexión falló - revisar configuración" "ERROR"
    Write-Host ""
    Write-Host "Variables de entorno actuales:" -ForegroundColor Yellow
    Write-Host "REDIS_HOST: $RedisHost" -ForegroundColor Gray
    Write-Host "REDIS_PORT: $RedisPort" -ForegroundColor Gray
    Write-Host "REDIS_SSL: $($env:REDIS_SSL)" -ForegroundColor Gray
    Write-Host "REDIS_KEY: $(if($RedisPassword) {'***SET***'} else {'NOT SET'})" -ForegroundColor Gray
}

Write-Host ""
Write-Status "Quick check completado" "OK"