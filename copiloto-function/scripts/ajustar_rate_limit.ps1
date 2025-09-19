# ======================
# fix_deployment.ps1 - ELIMINAR Y RECREAR
# ======================

$resourceGroup = "boat-rental-app-group"
$accountName = "boatRentalFoundry-dev"
$deploymentName = "gpt-4o"

Write-Host "`n[PASO 1] Verificando deployment actual..." -ForegroundColor Cyan
$currentDeployment = az cognitiveservices account deployment show `
  --resource-group $resourceGroup `
  --name $accountName `
  --deployment-name $deploymentName `
  --query "{Name:name, Capacity:sku.capacity, SKU:sku.name}" -o json | ConvertFrom-Json

Write-Host "Deployment actual:" -ForegroundColor Yellow
Write-Host "  - Nombre: $($currentDeployment.Name)" -ForegroundColor White
Write-Host "  - Capacidad: $($currentDeployment.Capacity) K TPM" -ForegroundColor White
Write-Host "  - SKU: $($currentDeployment.SKU)" -ForegroundColor White

Write-Host "`n[PASO 2] Eliminando deployment existente..." -ForegroundColor Cyan
$deleteResult = az cognitiveservices account deployment delete `
  --resource-group $resourceGroup `
  --name $accountName `
  --deployment-name $deploymentName `
  --yes 2>&1

if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] Deployment eliminado" -ForegroundColor Green
    
  Write-Host "`n[PASO 3] Esperando 10 segundos para que se libere la cuota..." -ForegroundColor Cyan
  Start-Sleep -Seconds 10
    
  Write-Host "`n[PASO 4] Recreando deployment con nueva capacidad..." -ForegroundColor Cyan
    
  # Opciones de capacidad
  Write-Host "`nSelecciona la capacidad deseada:" -ForegroundColor Magenta
  Write-Host "1. 40K TPM (máximo disponible)" -ForegroundColor White
  Write-Host "2. 30K TPM" -ForegroundColor White
  Write-Host "3. 20K TPM" -ForegroundColor White
  Write-Host "4. 10K TPM" -ForegroundColor White
    
  $choice = Read-Host "Opción (1-4)"
    
  switch ($choice) {
    "1" { $newCapacity = 40 }
    "2" { $newCapacity = 30 }
    "3" { $newCapacity = 20 }
    "4" { $newCapacity = 10 }
    default { $newCapacity = 20 }
  }
    
  Write-Host "`n[INFO] Creando deployment con $newCapacity K TPM..." -ForegroundColor Cyan
    
  $createResult = az cognitiveservices account deployment create `
    --resource-group $resourceGroup `
    --name $accountName `
    --deployment-name $deploymentName `
    --model-name "gpt-4o" `
    --model-version "2024-05-13" `
    --model-format "OpenAI" `
    --sku-capacity $newCapacity `
    --sku-name "Standard" 2>&1
    
  if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Deployment recreado con $newCapacity K TPM" -ForegroundColor Green
        
    # Verificar
    Write-Host "`n[PASO 5] Verificando nueva configuración..." -ForegroundColor Cyan
    az cognitiveservices account deployment show `
      --resource-group $resourceGroup `
      --name $accountName `
      --deployment-name $deploymentName `
      --query "{Name:name, Capacity:sku.capacity, SKU:sku.name, Status:properties.provisioningState}" -o table
          
  }
  else {
    Write-Host "`n[ERROR] Falló la creación:" -ForegroundColor Red
    Write-Host $createResult -ForegroundColor Red
  }
    
}
else {
  Write-Host "`n[ERROR] No se pudo eliminar el deployment:" -ForegroundColor Red
  Write-Host $deleteResult -ForegroundColor Red
}