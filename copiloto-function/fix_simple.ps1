#!/usr/bin/env pwsh
# Script simple para corregir el despliegue

Write-Host "Corrigiendo despliegue de contenedor..." -ForegroundColor Yellow

$functionAppName = "copiloto-semantico-func-us2"
$resourceGroup = "boat-rental-app-group"

# Configurar WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
Write-Host "Configurando WEBSITES_ENABLE_APP_SERVICE_STORAGE=true..." -ForegroundColor Green
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "WEBSITES_ENABLE_APP_SERVICE_STORAGE=true"

# Configurar variables críticas
Write-Host "Configurando variables críticas..." -ForegroundColor Green
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "FUNCTIONS_WORKER_RUNTIME=python"
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "FUNCTIONS_EXTENSION_VERSION=~4"
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "AzureWebJobsScriptRoot=/home/site/wwwroot"

# Reiniciar
Write-Host "Reiniciando Function App..." -ForegroundColor Green
az functionapp restart --name $functionAppName --resource-group $resourceGroup

Write-Host "Esperando 60 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Verificar
Write-Host "Verificando endpoint..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/health" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: Endpoint responde" -ForegroundColor Green
    $response
}
catch {
    Write-Host "ERROR: Endpoint no responde" -ForegroundColor Red
    $_.Exception.Message
}

Write-Host "Correccion completada." -ForegroundColor Cyan