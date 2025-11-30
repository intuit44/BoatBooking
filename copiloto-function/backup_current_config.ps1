# backup_current_config.ps1 - Respalda configuración actual ANTES de ejecutar fix_functionapp_final.ps1

param(
  [string]$ResourceGroup = "boat-rental-app-group",
  [string]$FunctionApp = "copiloto-semantico-func-us2"
)

Write-Host "📋 Respaldando configuración actual..." -ForegroundColor Cyan

# 1. Respaldar App Settings
Write-Host "💾 Respaldando App Settings..." -ForegroundColor Yellow
$currentSettings = az functionapp config appsettings list -n $FunctionApp -g $ResourceGroup | ConvertFrom-Json
$currentSettings | ConvertTo-Json -Depth 10 | Out-File "backup_appsettings_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# 2. Respaldar configuración de contenedor
Write-Host "🐳 Respaldando configuración de contenedor..." -ForegroundColor Yellow
$containerConfig = az functionapp config container show -n $FunctionApp -g $ResourceGroup | ConvertFrom-Json
$containerConfig | ConvertTo-Json -Depth 10 | Out-File "backup_container_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# 3. Respaldar configuración general
Write-Host "⚙️ Respaldando configuración general..." -ForegroundColor Yellow
$appConfig = az functionapp show -n $FunctionApp -g $ResourceGroup | ConvertFrom-Json
$appConfig | ConvertTo-Json -Depth 10 | Out-File "backup_app_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# 4. Mostrar configuración crítica actual
Write-Host "`n🔍 CONFIGURACIÓN CRÍTICA ACTUAL:" -ForegroundColor Green
Write-Host "Deployment Method: $($appConfig.siteConfig.linuxFxVersion)" -ForegroundColor White
Write-Host "Container Image: $($containerConfig.linuxFxVersion)" -ForegroundColor White
Write-Host "Plan: $($appConfig.appServicePlanId.Split('/')[-1])" -ForegroundColor White

# 5. Crear script de restauración
$restoreScript = @"
# restore_config.ps1 - Restaura configuración respaldada
param([string]`$BackupDate)

Write-Host "🔄 Restaurando configuración..." -ForegroundColor Cyan

# Restaurar App Settings
az functionapp config appsettings set -n $FunctionApp -g $ResourceGroup --settings @"backup_appsettings_`$BackupDate.json"

# Restaurar configuración de contenedor
`$containerBackup = Get-Content "backup_container_`$BackupDate.json" | ConvertFrom-Json
az functionapp config container set -n $FunctionApp -g $ResourceGroup --docker-custom-image-name `$containerBackup.linuxFxVersion

Write-Host "✅ Configuración restaurada" -ForegroundColor Green
"@

$restoreScript | Out-File "restore_config.ps1"

Write-Host "✅ Respaldo completado. Archivos creados:" -ForegroundColor Green
Write-Host "  - backup_appsettings_*.json" -ForegroundColor Gray
Write-Host "  - backup_container_*.json" -ForegroundColor Gray
Write-Host "  - backup_app_*.json" -ForegroundColor Gray
Write-Host "  - restore_config.ps1" -ForegroundColor Gray