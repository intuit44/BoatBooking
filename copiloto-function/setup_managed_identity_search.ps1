# Configurar Managed Identity para Azure AI Search
$searchService = "boatrentalfoundrysearch"
$resourceGroup = "boat-rental-app-group"
$functionApp = "copiloto-semantico-func-us2"

Write-Host "`nCONFIGURACION MANAGED IDENTITY - AZURE AI SEARCH" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# 1. Obtener el Principal ID de la Function App
Write-Host "1. Obteniendo Managed Identity de Function App..." -ForegroundColor Yellow
$principalId = az functionapp identity show `
    --name $functionApp `
    --resource-group $resourceGroup `
    --query principalId -o tsv

if ($principalId) {
    Write-Host "   OK - Principal ID: $principalId" -ForegroundColor Green
} else {
    Write-Host "   ERROR - No se pudo obtener Managed Identity" -ForegroundColor Red
    exit 1
}

# 2. Obtener el Resource ID del servicio Azure Search
Write-Host "`n2. Obteniendo Resource ID de Azure Search..." -ForegroundColor Yellow
$searchResourceId = az search service show `
    --name $searchService `
    --resource-group $resourceGroup `
    --query id -o tsv

Write-Host "   OK - Resource ID obtenido" -ForegroundColor Green

# 3. Asignar rol "Search Index Data Contributor"
Write-Host "`n3. Asignando rol 'Search Index Data Contributor'..." -ForegroundColor Yellow
az role assignment create `
    --assignee $principalId `
    --role "Search Index Data Contributor" `
    --scope $searchResourceId

Write-Host "   OK - Rol asignado exitosamente" -ForegroundColor Green

# 4. Asignar rol "Search Service Contributor" (para operaciones de servicio)
Write-Host "`n4. Asignando rol 'Search Service Contributor'..." -ForegroundColor Yellow
az role assignment create `
    --assignee $principalId `
    --role "Search Service Contributor" `
    --scope $searchResourceId

Write-Host "   OK - Rol asignado exitosamente" -ForegroundColor Green

# 5. Remover AZURE_SEARCH_KEY de variables de entorno
Write-Host "`n5. Removiendo AZURE_SEARCH_KEY de Function App..." -ForegroundColor Yellow
az functionapp config appsettings delete `
    --name $functionApp `
    --resource-group $resourceGroup `
    --setting-names AZURE_SEARCH_KEY

Write-Host "   OK - Variable AZURE_SEARCH_KEY removida" -ForegroundColor Green

# 6. Actualizar local.settings.json
Write-Host "`n6. Actualizando local.settings.json..." -ForegroundColor Yellow
$localSettingsPath = Join-Path -Path $PSScriptRoot -ChildPath "local.settings.json"
if (Test-Path $localSettingsPath) {
    $localSettings = Get-Content -Raw -Path $localSettingsPath | ConvertFrom-Json
    
    # Remover AZURE_SEARCH_KEY si existe
    if ($localSettings.Values.PSObject.Properties.Name -contains "AZURE_SEARCH_KEY") {
        $localSettings.Values.PSObject.Properties.Remove("AZURE_SEARCH_KEY")
        Write-Host "   OK - AZURE_SEARCH_KEY removida de local.settings.json" -ForegroundColor Green
    }
    
    # Guardar cambios
    $localSettings | ConvertTo-Json -Depth 10 | Set-Content -Path $localSettingsPath
    Write-Host "   OK - local.settings.json actualizado" -ForegroundColor Green
} else {
    Write-Host "   AVISO - local.settings.json no encontrado" -ForegroundColor Yellow
}

# Resumen
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "CONFIGURACION COMPLETADA" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "`nCambios realizados:" -ForegroundColor Yellow
Write-Host "   [+] Managed Identity configurada" -ForegroundColor Green
Write-Host "   [+] Rol 'Search Index Data Contributor' asignado" -ForegroundColor Green
Write-Host "   [+] Rol 'Search Service Contributor' asignado" -ForegroundColor Green
Write-Host "   [-] AZURE_SEARCH_KEY removida" -ForegroundColor Red
Write-Host "`nProximo paso: Actualizar codigo Python para usar DefaultAzureCredential`n" -ForegroundColor Cyan
