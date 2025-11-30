#!/usr/bin/env pwsh
# Script para recrear la Function App con configuración correcta

Write-Host "Recreando Function App con configuración correcta..." -ForegroundColor Cyan

$functionAppName = "copiloto-semantico-func-us2"
$resourceGroup = "boat-rental-app-group"
$storageAccount = "boatrentalstorageacc"
$planName = "copiloto-plan"
$acrName = "boatrentalacr"
$imageName = "copiloto-func-azcli"
$tag = "v349"

# 1. Eliminar la Function App actual
Write-Host "1. Eliminando Function App actual..." -ForegroundColor Yellow
az functionapp delete --name $functionAppName --resource-group $resourceGroup --yes

# 2. Crear nueva Function App con contenedor personalizado
Write-Host "2. Creando nueva Function App con contenedor..." -ForegroundColor Yellow
$fullImageName = "$acrName.azurecr.io/$imageName`:$tag"

az functionapp create `
    --resource-group $resourceGroup `
    --plan $planName `
    --name $functionAppName `
    --storage-account $storageAccount `
    --deployment-container-image-name $fullImageName `
    --docker-registry-server-url "https://$acrName.azurecr.io" `
    --functions-version 4

Write-Host "3. Configurando credenciales ACR..." -ForegroundColor Yellow
$acrPassword = az acr credential show --name $acrName --query "passwords[0].value" --output tsv

az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings `
    "DOCKER_REGISTRY_SERVER_URL=https://$acrName.azurecr.io" `
    "DOCKER_REGISTRY_SERVER_USERNAME=$acrName" `
    "DOCKER_REGISTRY_SERVER_PASSWORD=$acrPassword"

# 4. Configurar variables esenciales
Write-Host "4. Configurando variables esenciales..." -ForegroundColor Yellow
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings `
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE=false" `
    "FUNCTIONS_WORKER_RUNTIME=python" `
    "FUNCTIONS_EXTENSION_VERSION=~4" `
    "WEBSITES_PORT=80" `
    "AzureWebJobsScriptRoot=/home/site/wwwroot"

# 5. Reiniciar
Write-Host "5. Reiniciando Function App..." -ForegroundColor Yellow
az functionapp restart --name $functionAppName --resource-group $resourceGroup

# 6. Esperar y verificar
Write-Host "6. Esperando 90 segundos para inicialización..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

Write-Host "7. Verificando endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "https://$functionAppName.azurewebsites.net/api/health" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: Function App responde correctamente" -ForegroundColor Green
    $response
}
catch {
    Write-Host "INFO: Probando endpoint alternativo..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "https://$functionAppName.azurewebsites.net/api/listar-blobs" -Method GET -TimeoutSec 30
        Write-Host "SUCCESS: Endpoint alternativo responde" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Function App no responde aún" -ForegroundColor Red
        Write-Host "Puede necesitar más tiempo para inicializar" -ForegroundColor Yellow
    }
}

Write-Host "Recreación completada." -ForegroundColor Cyan