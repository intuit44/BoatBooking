#!/usr/bin/env pwsh
# Script para corregir el despliegue del contenedor de la Function App

Write-Host "🔧 CORRECCIÓN DE DESPLIEGUE DE CONTENEDOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$functionAppName = "copiloto-semantico-func-us2"
$resourceGroup = "boat-rental-app-group"
$acrName = "boatrentalacr"
$imageName = "copiloto-func-azcli"
$tag = "v349"

# 1. Verificar estado actual
Write-Host "[1] Verificando estado actual..." -ForegroundColor Yellow
$currentConfig = az functionapp config container show --name $functionAppName --resource-group $resourceGroup | ConvertFrom-Json
Write-Host "Imagen actual: $($currentConfig.linuxFxVersion)" -ForegroundColor Green

# 2. Configurar correctamente WEBSITES_ENABLE_APP_SERVICE_STORAGE
Write-Host "[2] Configurando WEBSITES_ENABLE_APP_SERVICE_STORAGE=true..." -ForegroundColor Yellow
az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "WEBSITES_ENABLE_APP_SERVICE_STORAGE=true" | Out-Null
Write-Host "✅ WEBSITES_ENABLE_APP_SERVICE_STORAGE configurado" -ForegroundColor Green

# 3. Configurar la imagen del contenedor correctamente
Write-Host "[3] Configurando imagen del contenedor..." -ForegroundColor Yellow
$fullImageName = "$acrName.azurecr.io/$imageName`:$tag"
az functionapp config container set --name $functionAppName --resource-group $resourceGroup --docker-custom-image-name $fullImageName | Out-Null
Write-Host "✅ Imagen configurada: $fullImageName" -ForegroundColor Green

# 4. Configurar variables críticas para el runtime
Write-Host "[4] Configurando variables críticas..." -ForegroundColor Yellow
$criticalSettings = @{
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "FUNCTIONS_EXTENSION_VERSION" = "~4"
    "AzureWebJobsScriptRoot" = "/home/site/wwwroot"
    "AzureWebJobsDisableHomepage" = "true"
    "WEBSITES_PORT" = "80"
    "DOCKER_ENABLE_CI" = "true"
}

foreach ($setting in $criticalSettings.GetEnumerator()) {
    Write-Host "  Configurando: $($setting.Key) = $($setting.Value)" -ForegroundColor Gray
    az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings "$($setting.Key)=$($setting.Value)" | Out-Null
}
Write-Host "✅ Variables críticas configuradas" -ForegroundColor Green

# 5. Reiniciar la Function App
Write-Host "[5] Reiniciando Function App..." -ForegroundColor Yellow
az functionapp restart --name $functionAppName --resource-group $resourceGroup | Out-Null
Write-Host "✅ Function App reiniciada" -ForegroundColor Green

# 6. Esperar y verificar
Write-Host "[6] Esperando 60 segundos para que el contenedor inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# 7. Verificar endpoints
Write-Host "[7] Verificando endpoints..." -ForegroundColor Yellow
$baseUrl = "https://$functionAppName.azurewebsites.net"
$endpoints = @("/api/health", "/api/status", "/api/listar-blobs")

foreach ($endpoint in $endpoints) {
    try {
        $url = "$baseUrl$endpoint"
        Write-Host "  Probando: $endpoint" -ForegroundColor Gray
        $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 30
        Write-Host "  ✅ $endpoint - Responde correctamente" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ $endpoint - No responde: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 8. Verificar archivos en el contenedor usando Kudu
Write-Host "[8] Verificando archivos en el contenedor..." -ForegroundColor Yellow
try {
    $kuduUrl = "https://$functionAppName.scm.azurewebsites.net/api/vfs/site/wwwroot/"
    $files = Invoke-RestMethod -Uri $kuduUrl -Method GET -TimeoutSec 30
    Write-Host "✅ Archivos encontrados en /home/site/wwwroot: $($files.Count)" -ForegroundColor Green
    
    # Mostrar algunos archivos importantes
    $importantFiles = $files | Where-Object { $_.name -in @("function_app.py", "requirements.txt", "host.json", "openapi.yaml") }
    foreach ($file in $importantFiles) {
        Write-Host "  - $($file.name) ($($file.size) bytes)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "❌ No se pudieron verificar los archivos: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 CORRECCIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "URL de la Function App: $baseUrl" -ForegroundColor Green