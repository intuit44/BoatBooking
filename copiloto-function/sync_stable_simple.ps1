#!/usr/bin/env pwsh

param(
    [string]$ResourceGroup = "boat-rental-app-group",
    [string]$FunctionAppName = "copiloto-semantico-func-us2",
    [int]$MaxRetries = 3
)

Write-Host "Iniciando sincronización estable de Azure Functions..." -ForegroundColor Green

function Test-FunctionAppHealth {
    param([string]$AppName)
    
    try {
        Write-Host "Verificando salud del Function App..." -ForegroundColor Yellow
        
        $healthUrl = "https://$AppName.azurewebsites.net/api/redis-cache-health"
        $response = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 15 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "Endpoint de salud OK" -ForegroundColor Green
            return $true
        }
        return $false
    }
    catch {
        Write-Host "Endpoint de salud no responde: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

function Invoke-SyncTriggers {
    param([string]$AppName, [string]$RG)
    
    try {
        Write-Host "Ejecutando syncfunctiontriggers..." -ForegroundColor Cyan
        
        $appId = az functionapp show --name $AppName --resource-group $RG --query "id" -o tsv
        $result = az rest --method POST --uri "https://management.azure.com$appId/syncfunctiontriggers?api-version=2022-03-01" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Sync exitoso!" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Sync falló: $result" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error en sync: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
    Write-Host "`nIntento $attempt de $MaxRetries" -ForegroundColor Magenta
    
    # Wait for stability
    Write-Host "Esperando 20 segundos para estabilidad..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    # Check health
    if (Test-FunctionAppHealth -AppName $FunctionAppName) {
        Write-Host "Function App saludable, ejecutando sync..." -ForegroundColor Green
        
        if (Invoke-SyncTriggers -AppName $FunctionAppName -RG $ResourceGroup) {
            Write-Host "`nSincronización exitosa!" -ForegroundColor Green
            Write-Host "Las funciones deberían aparecer en el portal" -ForegroundColor Cyan
            exit 0
        }
    }
    
    Write-Host "Intento $attempt falló, esperando..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

Write-Host "`nTodos los intentos fallaron" -ForegroundColor Red
Write-Host "Soluciones:" -ForegroundColor Cyan
Write-Host "1. Revisar logs de errores texto_semantico" -ForegroundColor White
Write-Host "2. Reiniciar function app manualmente" -ForegroundColor White
exit 1