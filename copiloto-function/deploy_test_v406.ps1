#!/usr/bin/env pwsh

# Deploy quick test v406 - Solo para verificar que syncfunctiontriggers funciona
Write-Host "Deploying quick fix validation..." -ForegroundColor Green

# Configuración
$resourceGroup = "boat-rental-app-group"
$functionAppName = "copiloto-semantico-func-us2"
$registryName = "boatrentalacr"
$imageName = "copiloto-func-azcli"
$tag = "v406"

try {
    Write-Host "Building container image..." -ForegroundColor Cyan
    $buildResult = docker build -t "${registryName}.azurecr.io/${imageName}:${tag}" .
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }
    
    Write-Host "Pushing to ACR..." -ForegroundColor Cyan
    $pushResult = docker push "${registryName}.azurecr.io/${imageName}:${tag}"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed"
    }
    
    Write-Host "Updating Function App container..." -ForegroundColor Cyan
    $updateResult = az functionapp config container set `
        --name $functionAppName `
        --resource-group $resourceGroup `
        --docker-custom-image-name "${registryName}.azurecr.io/${imageName}:${tag}"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Function App update failed"
    }
    
    Write-Host "Deployment completed! Container v406 deployed." -ForegroundColor Green
    Write-Host "Waiting 30 seconds for container to fully start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Test endpoint
    Write-Host "Testing endpoint..." -ForegroundColor Cyan
    try {
        $testUrl = "https://$functionAppName.azurewebsites.net/api/redis-cache-health"
        $response = Invoke-WebRequest -Uri $testUrl -Method GET -TimeoutSec 15 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Endpoint test PASSED" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️ Endpoint test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "`n🚀 Ready to test syncfunctiontriggers!" -ForegroundColor Green
    
}
catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}