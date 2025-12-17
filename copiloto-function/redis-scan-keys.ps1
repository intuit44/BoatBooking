#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script especializado para escaneo y análisis de claves Redis
.DESCRIPTION
    Escanea Redis con patrones específicos y analiza estructura de claves
.PARAMETER Pattern
    Patrón de claves a buscar (default: *)
.PARAMETER Count
    Número de claves por iteración SCAN (default: 100)
.PARAMETER Limit
    Límite total de claves a procesar (default: 1000)
.PARAMETER Analyze
    Analizar cada clave individualmente (TTL, tipo, tamaño)
.PARAMETER Export
    Exportar resultados a archivo JSON
.EXAMPLE
    .\redis-scan-keys.ps1 -Pattern "llm:*" -Count 50
.EXAMPLE
    .\redis-scan-keys.ps1 -Pattern "session:*" -Analyze -Export "session-keys.json"
#>

param(
    [string]$Pattern = "*",
    [int]$Count = 100,
    [int]$Limit = 1000,
    [switch]$Analyze,
    [string]$Export = ""
)

# Configuración Redis
$RedisHost = $env:REDIS_HOST
$RedisPort = $env:REDIS_PORT ?? 6379
$RedisPassword = $env:REDIS_KEY ?? $env:REDIS_PASSWORD
$UseTLS = ($env:REDIS_SSL -eq "1" -or $env:REDIS_TLS -eq "1")

function Get-RedisCliPath {
    $paths = @(
        "C:\redis\redis-cli.exe",
        "C:\Program Files\Redis\redis-cli.exe",
        "C:\Program Files (x86)\Redis\redis-cli.exe"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) { return $path }
    }
    
    $which = Get-Command redis-cli -ErrorAction SilentlyContinue
    return $which?.Source
}

function Invoke-RedisCmd {
    param([string]$Command)
    
    $redisCliPath = Get-RedisCliPath
    if (-not $redisCliPath) {
        throw "redis-cli no encontrado"
    }
    
    $args = @()
    if ($RedisHost) { $args += @("-h", $RedisHost) }
    if ($RedisPort -ne 6379) { $args += @("-p", $RedisPort) }
    if ($RedisPassword) { $args += @("-a", $RedisPassword) }
    if ($UseTLS) { $args += @("--tls") }
    
    $args += $Command.Split(' ')
    
    $result = & $redisCliPath @args 2>&1
    return @{
        Success  = $LASTEXITCODE -eq 0
        Output   = $result
        ExitCode = $LASTEXITCODE
    }
}

function Get-AllKeysWithScan {
    param([string]$Pattern, [int]$Count, [int]$Limit)
    
    Write-Host "🔍 Escaneando claves con patrón: $Pattern" -ForegroundColor Cyan
    
    $allKeys = @()
    $cursor = 0
    $totalScanned = 0
    
    do {
        Write-Progress -Activity "Escaneando Redis" -Status "Cursor: $cursor | Encontradas: $($allKeys.Count)" -PercentComplete (($allKeys.Count / $Limit) * 100)
        
        $scanCmd = "SCAN $cursor MATCH `"$Pattern`" COUNT $Count"
        $result = Invoke-RedisCmd -Command $scanCmd
        
        if (-not $result.Success) {
            Write-Warning "Error en SCAN: $($result.Output)"
            break
        }
        
        $lines = $result.Output -split "`n"
        $cursor = [int]$lines[0].Trim()
        
        $keys = $lines[1..($lines.Length - 1)] | Where-Object { $_ -and $_.Trim() }
        $allKeys += $keys
        $totalScanned++
        
        Write-Host "  Iteración $totalScanned | Cursor: $cursor | Nuevas claves: $($keys.Count) | Total: $($allKeys.Count)" -ForegroundColor Gray
        
    } while ($cursor -ne 0 -and $allKeys.Count -lt $Limit -and $totalScanned -lt 100)
    
    Write-Progress -Completed -Activity "Escaneando Redis"
    
    return $allKeys | Select-Object -First $Limit
}

function Analyze-Key {
    param([string]$Key)
    
    $typeResult = Invoke-RedisCmd -Command "TYPE `"$Key`""
    $ttlResult = Invoke-RedisCmd -Command "TTL `"$Key`""
    
    $keyInfo = @{
        Key    = $Key
        Type   = if ($typeResult.Success) { $typeResult.Output.Trim() } else { "unknown" }
        TTL    = if ($ttlResult.Success) { [int]$ttlResult.Output.Trim() } else { -999 }
        Size   = $null
        Sample = $null
    }
    
    # Obtener muestra del contenido según el tipo
    try {
        switch ($keyInfo.Type) {
            "string" {
                $lenResult = Invoke-RedisCmd -Command "STRLEN `"$Key`""
                if ($lenResult.Success) {
                    $keyInfo.Size = [int]$lenResult.Output.Trim()
                }
                
                $getResult = Invoke-RedisCmd -Command "GET `"$Key`""
                if ($getResult.Success) {
                    $content = $getResult.Output.Trim()
                    $keyInfo.Sample = if ($content.Length -gt 100) { 
                        $content.Substring(0, 100) + "..."
                    }
                    else { 
                        $content 
                    }
                }
            }
            "hash" {
                $hlenResult = Invoke-RedisCmd -Command "HLEN `"$Key`""
                if ($hlenResult.Success) {
                    $keyInfo.Size = [int]$hlenResult.Output.Trim()
                }
                
                $keysResult = Invoke-RedisCmd -Command "HKEYS `"$Key`""
                if ($keysResult.Success) {
                    $fields = $keysResult.Output -split "`n" | Where-Object { $_ }
                    $keyInfo.Sample = "Fields: " + ($fields | Select-Object -First 5) -join ", "
                }
            }
            "list" {
                $llenResult = Invoke-RedisCmd -Command "LLEN `"$Key`""
                if ($llenResult.Success) {
                    $keyInfo.Size = [int]$llenResult.Output.Trim()
                }
            }
            "set" {
                $scardResult = Invoke-RedisCmd -Command "SCARD `"$Key`""
                if ($scardResult.Success) {
                    $keyInfo.Size = [int]$scardResult.Output.Trim()
                }
            }
            "zset" {
                $zcardResult = Invoke-RedisCmd -Command "ZCARD `"$Key`""
                if ($zcardResult.Success) {
                    $keyInfo.Size = [int]$zcardResult.Output.Trim()
                }
            }
        }
    }
    catch {
        # Ignorar errores de análisis individual
    }
    
    return $keyInfo
}

function Show-KeysSummary {
    param($Keys, $Analysis = $null)
    
    Write-Host ""
    Write-Host "📊 RESUMEN DE CLAVES" -ForegroundColor Magenta
    Write-Host "===================" -ForegroundColor Magenta
    
    Write-Host "Total encontradas: $($Keys.Count)" -ForegroundColor Green
    
    if ($Keys.Count -eq 0) {
        Write-Host "No se encontraron claves con el patrón especificado." -ForegroundColor Yellow
        return
    }
    
    # Agrupar por prefijos
    $prefixes = @{}
    foreach ($key in $Keys) {
        $parts = $key -split ":"
        $prefix = if ($parts.Count -gt 1) { $parts[0] } else { "sin_prefijo" }
        
        if (-not $prefixes.ContainsKey($prefix)) {
            $prefixes[$prefix] = 0
        }
        $prefixes[$prefix]++
    }
    
    Write-Host ""
    Write-Host "Distribución por prefijos:" -ForegroundColor Cyan
    foreach ($prefix in $prefixes.Keys | Sort-Object) {
        Write-Host "  $prefix`: $($prefixes[$prefix]) claves" -ForegroundColor Gray
    }
    
    if ($Analysis) {
        Write-Host ""
        Write-Host "Análisis detallado:" -ForegroundColor Cyan
        
        # Agrupar por tipos
        $types = $Analysis | Group-Object Type
        foreach ($typeGroup in $types) {
            Write-Host "  Tipo $($typeGroup.Name): $($typeGroup.Count) claves" -ForegroundColor Gray
        }
        
        # TTL stats
        $withTTL = ($Analysis | Where-Object { $_.TTL -gt 0 }).Count
        $withoutTTL = ($Analysis | Where-Object { $_.TTL -eq -1 }).Count
        $expired = ($Analysis | Where-Object { $_.TTL -eq -2 }).Count
        
        Write-Host ""
        Write-Host "TTL (Time To Live):" -ForegroundColor Cyan
        Write-Host "  Con TTL: $withTTL" -ForegroundColor Gray
        Write-Host "  Sin TTL (persistentes): $withoutTTL" -ForegroundColor Gray
        Write-Host "  Expiradas: $expired" -ForegroundColor Gray
    }
    
    # Mostrar muestra de claves
    Write-Host ""
    Write-Host "Muestra de claves (primeras 20):" -ForegroundColor Cyan
    $Keys | Select-Object -First 20 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    if ($Keys.Count -gt 20) {
        Write-Host "  ... y $($Keys.Count - 20) más" -ForegroundColor Yellow
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host ""
Write-Host "🔑 REDIS KEY SCANNER" -ForegroundColor Magenta
Write-Host "====================" -ForegroundColor Magenta
Write-Host ""

# Validaciones
if (-not $RedisHost) {
    Write-Host "❌ Error: REDIS_HOST no configurado" -ForegroundColor Red
    exit 1
}

Write-Host "Redis: $RedisHost`:$RedisPort (TLS: $UseTLS)" -ForegroundColor Cyan
Write-Host "Patrón: $Pattern | Límite: $Limit | Análisis: $Analyze" -ForegroundColor Cyan
Write-Host ""

# Test conexión
$pingResult = Invoke-RedisCmd -Command "PING"
if (-not $pingResult.Success) {
    Write-Host "❌ Error de conexión: $($pingResult.Output)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Conexión exitosa" -ForegroundColor Green
Write-Host ""

try {
    # Escanear claves
    $keys = Get-AllKeysWithScan -Pattern $Pattern -Count $Count -Limit $Limit
    
    $analysis = $null
    if ($Analyze -and $keys.Count -gt 0) {
        Write-Host ""
        Write-Host "🔬 Analizando claves individuales..." -ForegroundColor Cyan
        
        $analysis = @()
        $i = 0
        foreach ($key in $keys) {
            $i++
            Write-Progress -Activity "Analizando claves" -Status "Procesando $key" -PercentComplete (($i / $keys.Count) * 100)
            
            $keyAnalysis = Analyze-Key -Key $key
            $analysis += $keyAnalysis
        }
        Write-Progress -Completed -Activity "Analizando claves"
    }
    
    # Mostrar resumen
    Show-KeysSummary -Keys $keys -Analysis $analysis
    
    # Exportar si se solicita
    if ($Export -and $keys.Count -gt 0) {
        $exportData = @{
            Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            Pattern   = $Pattern
            TotalKeys = $keys.Count
            Keys      = $keys
            Analysis  = $analysis
            RedisInfo = @{
                Host = $RedisHost
                Port = $RedisPort
                TLS  = $UseTLS
            }
        }
        
        $exportData | ConvertTo-Json -Depth 10 | Out-File -FilePath $Export -Encoding UTF8
        Write-Host ""
        Write-Host "💾 Resultados exportados a: $Export" -ForegroundColor Green
    }
    
}
catch {
    Write-Host "❌ Error durante el escaneo: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Escaneo completado" -ForegroundColor Green