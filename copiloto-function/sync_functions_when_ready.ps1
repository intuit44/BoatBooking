#!/usr/bin/env powershell
<#
.SYNOPSIS
Script para ejecutar syncfunctiontriggers cuando el host esté completamente listo

.DESCRIPTION
Este script verifica que el Azure Functions Host esté completamente operativo
antes de ejecutar syncfunctiontriggers para registrar endpoints como funciones
individuales en el Portal Azure.

.EXAMPLE
.\sync_functions_when_ready.ps1
#>

param(
  [string]$ResourceGroup = "boat-rental-app-group",
  [string]$FunctionApp = "copiloto-semantico-func-us2",
  [string]$BaseUrl = "https://copiloto-semantico-func-us2.azurewebsites.net",
  [int]$MaxWaitMinutes = 10
)

# Colores para output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }

function Test-Endpoint {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 15
  )
  
  try {
    $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
    return @{ 
      Success = $true
      StatusCode = $response.StatusCode
      Content = $response.Content
    }
  }
  catch {
    return @{ 
      Success = $false
      StatusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
      Error = $_.Exception.Message
    }
  }
}

function Wait-HostFullyReady {
  param(
    [string]$BaseUrl,
    [int]$MaxWaitMinutes = 10
  )
  
  Write-Info "🔍 Verificando readiness completo del host Azure Functions..."
  $healthEndpoint = "$BaseUrl/api/redis-cache-health"
  $maxAttempts = $MaxWaitMinutes * 6  # Cada 10 segundos
  
  for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $result = Test-Endpoint -Url $healthEndpoint -TimeoutSeconds 15
    
    if ($result.Success -and $result.StatusCode -eq 200) {
      # Verificar que la respuesta contiene datos válidos
      try {
        $jsonResponse = $result.Content | ConvertFrom-Json
        if ($jsonResponse.status) {
          Write-Success "Host completamente listo (verificación $attempt)"
          
          # Validar endpoint adicional para confirmación
          $diagResult = Test-Endpoint -Url "$BaseUrl/api/diagnostico" -TimeoutSeconds 10
          if ($diagResult.Success) {
            Write-Success "Validación cruzada exitosa - host estable"
            return $true
          }
        }
      } catch {
        Write-Warning "Respuesta no válida en verificación $attempt"
      }
    } else {
      $statusInfo = if ($result.StatusCode -gt 0) { "Status: $($result.StatusCode)" } else { "Connection failed" }
      Write-Info "Host no listo - $statusInfo (verificación $attempt/$maxAttempts)"
    }
    
    if ($attempt -lt $maxAttempts) {
      Start-Sleep -Seconds 10
    }
  }
  
  Write-Error "Host no alcanzó readiness completo después de $MaxWaitMinutes minutos"
  return $false
}

function Sync-FunctionTriggers {
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
      
      # Esperar propagación
      Write-Info "Esperando propagación de cambios (45s)..."
      Start-Sleep -Seconds 45
      
      # Verificar funciones registradas
      try {
        $functions = az functionapp function list -g $ResourceGroup -n $FunctionApp --query "[].name" -o tsv 2>$null
        if ($functions) {
          $functionCount = ($functions | Measure-Object).Count
          Write-Success "Funciones registradas en portal: $functionCount"
          
          # Mostrar algunas funciones para confirmación
          $sampleFunctions = $functions | Select-Object -First 5
          Write-Info "Ejemplos: $($sampleFunctions -join ', ')..."
        }
      } catch {
        Write-Warning "No se pudo verificar el recuento de funciones"
      }
      
      return $true
    }
    else {
      Write-Error "Falló la sincronización: $syncResult"
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

Write-Host "`n🚀 SINCRONIZADOR DE AZURE FUNCTIONS" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

Write-Info "Function App: $FunctionApp"
Write-Info "Base URL: $BaseUrl"
Write-Info "Tiempo máximo espera: $MaxWaitMinutes minutos"

# 1. Verificar readiness del host
$hostReady = Wait-HostFullyReady -BaseUrl $BaseUrl -MaxWaitMinutes $MaxWaitMinutes

if (-not $hostReady) {
  Write-Error "Host no está listo para sincronización"
  Write-Info "💡 Consejos:"
  Write-Info "  • Verifica que el contenedor esté completamente iniciado"
  Write-Info "  • Espera unos minutos más y vuelve a intentar"
  Write-Info "  • Verifica logs: az webapp log tail -g $ResourceGroup -n $FunctionApp --provider application"
  exit 1
}

# 2. Ejecutar sincronización
$syncSuccess = Sync-FunctionTriggers -ResourceGroup $ResourceGroup -FunctionApp $FunctionApp

if ($syncSuccess) {
  Write-Success "🎉 SINCRONIZACIÓN COMPLETADA EXITOSAMENTE"
  Write-Info "Los endpoints ahora deberían aparecer como funciones individuales en Azure Portal"
  Write-Info "URL Portal: https://portal.azure.com/#@/resource/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionApp/functions"
} else {
  Write-Error "❌ SINCRONIZACIÓN FALLÓ"
  Write-Info "💡 Posibles causas:"
  Write-Info "  • Host runtime aún no completamente estable"
  Write-Info "  • Problemas de red temporal"
  Write-Info "  • Permisos insuficientes"
}

Write-Host "`n========================================" -ForegroundColor Magenta