# Setup Azure AI Search para Memoria Semántica
$searchService = "boatrental-search"
$resourceGroup = "boat-rental-app-group"
$location = "eastus"

# 1. Crear servicio Azure AI Search
Write-Host "🔍 Creando Azure AI Search..." -ForegroundColor Cyan
az search service create `
  --name $searchService `
  --resource-group $resourceGroup `
  --location $location `
  --sku basic

# 2. Obtener admin key
$adminKey = az search admin-key show `
  --service-name $searchService `
  --resource-group $resourceGroup `
  --query primaryKey -o tsv

# 3. Crear índice
Write-Host "📊 Creando índice..." -ForegroundColor Cyan
$endpoint = "https://$searchService.search.windows.net"

# Use Invoke-RestMethod instead of the 'curl' alias to avoid alias-related issues and ensure script portability.
$schemaPath = Join-Path -Path (Get-Location) -ChildPath "azure_search_schema.json"
if (-Not (Test-Path $schemaPath)) {
  Write-Error "Schema file not found at $schemaPath"
}
else {
  $body = Get-Content -Raw -Path $schemaPath
  $headers = @{
    "Content-Type" = "application/json"
    "api-key"      = $adminKey
  }
  try {
    Invoke-RestMethod -Uri "$endpoint/indexes/agent-memory-index?api-version=2023-11-01" -Method Put -Body $body -Headers $headers
    Write-Host "Índice creado o actualizado exitosamente." -ForegroundColor Green
  }
  catch {
    Write-Error "Error creating index: $_"
  }
}

# 4. Crear cola para indexación
Write-Host "📬 Creando cola..." -ForegroundColor Cyan
az storage queue create `
  --name memory-indexing-queue `
  --account-name boatrentalstorage

# 5. Configurar variables de entorno
Write-Host "⚙️ Configurando variables..." -ForegroundColor Cyan
az functionapp config appsettings set `
  --name copiloto-semantico-func-us2 `
  --resource-group $resourceGroup `
  --settings `
  AZURE_SEARCH_ENDPOINT=$endpoint `
  AZURE_SEARCH_KEY=$adminKey

Write-Host "✅ Setup completado" -ForegroundColor Green
Write-Host "🔗 Endpoint: $endpoint" -ForegroundColor Yellow
