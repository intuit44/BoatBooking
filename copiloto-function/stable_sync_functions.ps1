#!/usr/bin/env powershell
<#
.SYNOPSIS
Script para validar estabilidad del host y ejecutar syncfunctiontriggers de forma segura

.DESCRIPTION
Este script verifica que el Azure Functions Host sea estable (sin reinicios)
antes de ejecutar syncfunctiontriggers para evitar el error Connection refused.
#>

param(
    [string]$ResourceGroup = "boat-rental-app-group",
    [string]$FunctionApp = "copiloto-semantico-func-us2",
    [string]$BaseUrl = "https://copiloto-semantico-func-us2.azurewebsites.net",
    [int]$StabilityCheckMinutes = 3,
    [int]$MaxRetries = 2
)

# Colores para output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }

function Test-Endpoint {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 10
    )
  
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
        return @{ 
            Success      = $true
            StatusCode   = $response.StatusCode
            Content      = $response.Content
            ResponseTime = (Measure-Command { $null }).TotalMilliseconds
        }
    }
    catch {
        return @{ 
            Success      = $false
            StatusCode   = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
            Error        = $_.Exception.Message
            ResponseTime = 0
        }
    }
}

function Test-HostStability {
    param(
        [string]$BaseUrl,
        [int]$CheckMinutes = 3
    )
  
    Write-Info "🔍 Validando estabilidad del host durante $CheckMinutes minutos..."
    $healthEndpoint = "$BaseUrl/api/redis-cache-health"
    $checks = $CheckMinutes * 6  # Cada 10 segundos
    $successCount = 0
    $consecutiveSuccesses = 0
    $requiredConsecutive = 6  # 1 minuto de estabilidad
  
    for ($check = 1; $check -le $checks; $check++) {
        $result = Test-Endpoint -Url $healthEndpoint -TimeoutSeconds 12
    
        if ($result.Success -and $result.StatusCode -eq 200) {
            $successCount++
            $consecutiveSuccesses++
      
            # Validar que la respuesta es válida JSON
            try {
                $jsonResponse = $result.Content | ConvertFrom-Json
                if ($jsonResponse.status) {
                    Write-Info "✓ Check $check/$checks - Host estable (consecutivos: $consecutiveSuccesses)"
          
                    # Si tenemos suficientes éxitos consecutivos, consideramos estable
                    if ($consecutiveSuccesses -ge $requiredConsecutive) {
                        Write-Success "Host alcanzó estabilidad requerida ($requiredConsecutive checks consecutivos)"
                        return $true
                    }
                }
                else {
                    Write-Warning "Respuesta inválida en check $check"
                    $consecutiveSuccesses = 0
                }
            }
            catch {
                Write-Warning "JSON inválido en check $check"
                $consecutiveSuccesses = 0
            }
        }
        else {
            $statusInfo = if ($result.StatusCode -gt 0) { "Status: $($result.StatusCode)" } else { "Connection failed" }
            Write-Warning "✗ Check $check/$checks - $statusInfo (reiniciando contador)"
            $consecutiveSuccesses = 0
        }
    
        if ($check -lt $checks) {
            Start-Sleep -Seconds 10
        }
    }
  
    $successRate = [math]::Round(($successCount / $checks) * 100, 1)
    Write-Warning "Host no alcanzó estabilidad requerida"
    Write-Info "Tasa de éxito: $successRate% ($successCount/$checks)"
    Write-Info "Éxitos consecutivos máximos: $consecutiveSuccesses"
  
    return $false
}

function Invoke-SyncFunctionTriggers {
    param(
        [string]$ResourceGroup,
        [string]$FunctionApp
    )
  
    Write-Info "🔄 Ejecutando syncfunctiontriggers..."
  
    $syncUrl = "https://management.azure.com/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionApp/syncfunctiontriggers?api-version=2022-09-01"
  
    try {
        $syncResult = az rest --method POST --url $syncUrl 2>&1
    
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Sincronización exitosa"
            return $true
        }
        else {
            Write-Error "Sincronización falló: $syncResult"
      
            # Detectar si es el error específico de Connection refused
            if ($syncResult -like "*Connection refused*" -or $syncResult -like "*InternalServerError*") {
                Write-Warning "Detectado error de Connection refused - host posiblemente reiniciando"
                return "host_restarting"
            }
      
            return $false
        }
    }
    catch {
        Write-Error "Error durante sincronización: $($_.Exception.Message)"
        return $false
    }
}

# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

Write-Host "`n🚀 SINCRONIZADOR ESTABLE DE AZURE FUNCTIONS" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

Write-Info "Function App: $FunctionApp"
Write-Info "Base URL: $BaseUrl"
Write-Info "Validación de estabilidad: $StabilityCheckMinutes minutos"

# 1. Verificar que el host esté estable antes de sincronizar
$isStable = Test-HostStability -BaseUrl $BaseUrl -CheckMinutes $StabilityCheckMinutes

if (-not $isStable) {
    Write-Error "Host no es estable - abortar sincronización"
    Write-Info "💡 Consejos:"
    Write-Info "  • Verificar logs de errores en Cosmos DB (texto_semantico)"
    Write-Info "  • Esperar más tiempo para que el host se estabilice"
    Write-Info "  • Corregir errores que causan reinicios del contenedor"
    exit 1
}

# 2. Ejecutar sincronización con reintentos
$syncSuccess = $false

for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
    Write-Info "Intento $attempt/$MaxRetries de sincronización..."
  
    # Verificación final antes del intento
    $quickCheck = Test-Endpoint -Url "$BaseUrl/api/redis-cache-health" -TimeoutSeconds 8
    if (-not ($quickCheck.Success -and $quickCheck.StatusCode -eq 200)) {
        Write-Warning "Host no responde en verificación previa - saltando intento $attempt"
        Start-Sleep -Seconds 30
        continue
    }
  
    $syncResult = Invoke-SyncFunctionTriggers -ResourceGroup $ResourceGroup -FunctionApp $FunctionApp
  
    if ($syncResult -eq $true) {
        Write-Success "🎉 Sincronización exitosa en intento $attempt"
        $syncSuccess = $true
        break
    }
    elseif ($syncResult -eq "host_restarting") {
        Write-Warning "Host reiniciando detectado - esperando estabilización..."
        if ($attempt -lt $MaxRetries) {
            Write-Info "Esperando 2 minutos antes del siguiente intento..."
            Start-Sleep -Seconds 120
      
            # Re-validar estabilidad
            Write-Info "Re-validando estabilidad del host..."
            $isStableAgain = Test-HostStability -BaseUrl $BaseUrl -CheckMinutes 2
            if (-not $isStableAgain) {
                Write-Error "Host sigue inestable después de espera"
                break
            }
        }
    }
    else {
        Write-Warning "Sincronización falló por razón diferente"
        if ($attempt -lt $MaxRetries) {
            Start-Sleep -Seconds 60
        }
    }
}

if ($syncSuccess) {
    Write-Success "🎉 SINCRONIZACIÓN COMPLETADA EXITOSAMENTE"
  
    # Esperar y verificar funciones registradas
    Write-Info "Esperando propagación de cambios (45s)..."
    Start-Sleep -Seconds 45
  
    try {
        $functions = az functionapp function list -g $ResourceGroup -n $FunctionApp --query "[].name" -o tsv 2>$null
        if ($functions) {
            $functionCount = ($functions | Measure-Object).Count
            Write-Success "Funciones registradas en portal: $functionCount"
      
            # Mostrar algunas funciones para confirmación
            $sampleFunctions = $functions | Select-Object -First 5
            Write-Info "Ejemplos: $($sampleFunctions -join ', ')..."
      
            Write-Info "✅ URL Portal: https://portal.azure.com/#@/resource/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionApp/functions"
        }
    }
    catch {
        Write-Warning "No se pudo verificar el recuento de funciones"
    }
}
else {
    Write-Error "❌ SINCRONIZACIÓN FALLÓ DESPUÉS DE $MaxRetries INTENTOS"
    Write-Info "💡 Acciones recomendadas:"
    Write-Info "  1. Verificar logs: az webapp log tail -g $ResourceGroup -n $FunctionApp --provider application"
    Write-Info "  2. Corregir errores de Cosmos DB que causan reinicios"
    Write-Info "  3. Intentar sincronización manual cuando el host esté más estable"
}

Write-Host "`n==============================================" -ForegroundColor Magenta