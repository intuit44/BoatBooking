# Actualizar local.settings.json con configuracion de Azure AI Search
$searchService = "boatrentalfoundrysearch"
$resourceGroup = "boat-rental-app-group"

Write-Host "Actualizando local.settings.json..." -ForegroundColor Cyan

# Obtener admin key
$adminKey = az search admin-key show `
    --service-name $searchService `
    --resource-group $resourceGroup `
    --query primaryKey -o tsv

$endpoint = "https://$searchService.search.windows.net"

# Leer local.settings.json
$localSettingsPath = Join-Path -Path $PSScriptRoot -ChildPath "local.settings.json"
$localSettings = Get-Content -Raw -Path $localSettingsPath | ConvertFrom-Json

# Agregar o actualizar variables
$localSettings.Values | Add-Member -NotePropertyName "AZURE_SEARCH_ENDPOINT" -NotePropertyValue $endpoint -Force
$localSettings.Values | Add-Member -NotePropertyName "AZURE_SEARCH_KEY" -NotePropertyValue $adminKey -Force

# Guardar
$localSettings | ConvertTo-Json -Depth 10 | Set-Content -Path $localSettingsPath

Write-Host "OK - local.settings.json actualizado" -ForegroundColor Green
Write-Host "   AZURE_SEARCH_ENDPOINT: $endpoint" -ForegroundColor Gray
Write-Host "   AZURE_SEARCH_KEY: $($adminKey.Substring(0,8))..." -ForegroundColor Gray
