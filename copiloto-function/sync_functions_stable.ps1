#!/usr/bin/env pwsh
<#
.SYNOPSIS
Sincronización estable de Azure Functions después de correcciones de Cosmos DB

.DESCRIPTION
Script que espera a que el host esté estable antes de ejecutar syncfunctiontriggers
para evitar "Connection refused" durante reinicios del host.
#>

param(
    [string]$ResourceGroup = "boat-rental-app-group",
    [string]$FunctionAppName = "copiloto-semantico-func-us2",
    [int]$MaxRetries = 5,
    [int]$StabilityCheckSeconds = 30
)

Write-Host "🔧 Iniciando sincronización estable de Azure Functions..." -ForegroundColor Green
Write-Host "📋 Function App: $FunctionAppName" -ForegroundColor Cyan
Write-Host "📋 Resource Group: $ResourceGroup" -ForegroundColor Cyan

function Test-FunctionAppHealth {
    param([string]$AppName, [string]$RG)
    
    try {
        Write-Host "🩺 Verificando salud del Function App..." -ForegroundColor Yellow
        
        # Verificar estado general
        $appStatus = az functionapp show --name $AppName --resource-group $RG --query "state" -o tsv 2>$null
        if ($appStatus -ne "Running") {
            Write-Host "❌ Function App no está en estado 'Running': $appStatus" -ForegroundColor Red
            return $false
        }
        
        # Verificar endpoint de salud
        $healthUrl = "https://$AppName.azurewebsites.net/api/redis-cache-health"
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Endpoint de salud respondió correctamente" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "⚠️ Endpoint de salud no respondió: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        return $false
    }
    catch {
        Write-Host "❌ Error verificando salud: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Wait-ForStability {
    param([string]$AppName, [string]$RG, [int]$Seconds)
    
    Write-Host "⏱️ Esperando estabilidad del host por $Seconds segundos..." -ForegroundColor Yellow
    
    $healthChecks = 0
    $successfulChecks = 0
    $requiredSuccessful = 3
    
    for ($i = 0; $i -lt $Seconds; $i += 10) {
        Start-Sleep -Seconds 10
        $healthChecks++
        
        if (Test-FunctionAppHealth -AppName $AppName -RG $RG) {
            $successfulChecks++
            Write-Host "✅ Check $healthChecks/$([Math]::Ceiling($Seconds/10)): Estable ($successfulChecks/$requiredSuccessful)" -ForegroundColor Green
            
            if ($successfulChecks -ge $requiredSuccessful) {
                Write-Host "🎉 Host estable detectado después de $requiredSuccessful checks exitosos" -ForegroundColor Green
                return $true
            }
        }
        else {
            $successfulChecks = 0  # Reset counter si falla
            Write-Host "⚠️ Check $healthChecks/$([Math]::Ceiling($Seconds/10)): No estable (reiniciando contador)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "⏰ Tiempo de espera agotado, continuando con sync..." -ForegroundColor Yellow
    return $false
}

function Invoke-SyncFunctionTriggers {
    param([string]$AppName, [string]$RG)
    
    try {
        Write-Host "🔄 Ejecutando syncfunctiontriggers..." -ForegroundColor Cyan
        
        # Obtener información de la función app
        $appId = az functionapp show --name $AppName --resource-group $RG --query "id" -o tsv
        if (-not $appId) {
            throw "No se pudo obtener el ID de la Function App"
        }
        
        # Ejecutar sync
        $result = az rest --method POST --uri "https://management.azure.com$appId/syncfunctiontriggers?api-version=2022-03-01" --verbose 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ syncfunctiontriggers ejecutado exitosamente" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ syncfunctiontriggers falló con código: $LASTEXITCODE" -ForegroundColor Red
            Write-Host "📄 Salida: $result" -ForegroundColor Gray
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando sync: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Main {
    $attempt = 1
    
    while ($attempt -le $MaxRetries) {
        Write-Host "`n🔄 Intento $attempt de $MaxRetries" -ForegroundColor Magenta
        
        # Verificar salud inicial
        if (-not (Test-FunctionAppHealth -AppName $FunctionAppName -RG $ResourceGroup)) {
            Write-Host "⚠️ Function App no está saludable, esperando..." -ForegroundColor Yellow
            Wait-ForStability -AppName $FunctionAppName -RG $ResourceGroup -Seconds $StabilityCheckSeconds
        }
        else {
            Write-Host "✅ Function App está saludable, procediendo con sync..." -ForegroundColor Green
        }
        
        # Intentar sync
        if (Invoke-SyncFunctionTriggers -AppName $FunctionAppName -RG $ResourceGroup) {
            Write-Host "`n🎉 ¡Sincronización exitosa!" -ForegroundColor Green
            Write-Host "💡 Las funciones deberían aparecer ahora en el portal de Azure" -ForegroundColor Cyan
            return 0
        }
        
        Write-Host "`n⚠️ Intento $attempt falló" -ForegroundColor Yellow
        $attempt++
        
        if ($attempt -le $MaxRetries) {
            $waitTime = $attempt * 15
            Write-Host "⏱️ Esperando $waitTime segundos antes del siguiente intento..." -ForegroundColor Yellow
            Start-Sleep -Seconds $waitTime
        }
    }
    
    Write-Host "`n❌ Todos los intentos fallaron" -ForegroundColor Red
    Write-Host "💡 Posibles soluciones:" -ForegroundColor Cyan
    Write-Host "   1. Verificar que las correcciones de Cosmos DB se aplicaron correctamente" -ForegroundColor White
    Write-Host "   2. Revisar logs en Application Insights para errores de texto_semantico" -ForegroundColor White
    Write-Host "   3. Reiniciar manualmente: az functionapp restart -g $ResourceGroup -n $FunctionAppName" -ForegroundColor White
    
    return 1
}

# Ejecutar función principal
exit (Main)