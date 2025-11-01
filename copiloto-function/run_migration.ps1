# Ejecutar migracion de embeddings
Write-Host "Iniciando migracion de embeddings..." -ForegroundColor Cyan

# 1) Cargar variables desde local.settings.json primero
if (Test-Path "local.settings.json") {
    Write-Host "Cargando variables desde local.settings.json..." -ForegroundColor Yellow
    $settings = Get-Content "local.settings.json" | ConvertFrom-Json
    
    foreach ($key in $settings.Values.PSObject.Properties.Name) {
        $value = $settings.Values.$key
        Set-Item -Path "env:$key" -Value $value
    }
    
    Write-Host "Variables cargadas desde local.settings.json" -ForegroundColor Green
}

# 2) IMPONER valores correctos (pisan lo anterior)
$env:COSMOSDB_ENDPOINT = "https://copiloto-cosmos.documents.azure.com:443/"
$env:COSMOSDB_DATABASE = "agentMemory"
$env:COSMOSDB_CONTAINER = "memory"

# Mapear a nombres heredados
$env:COSMOS_ENDPOINT = $env:COSMOSDB_ENDPOINT
$env:COSMOS_DATABASE_NAME = $env:COSMOSDB_DATABASE
$env:COSMOS_CONTAINER_NAME = $env:COSMOSDB_CONTAINER

# Azure OpenAI para embeddings
$env:AZURE_OPENAI_ENDPOINT = "https://boatrentalfoundry-openai.openai.azure.com/"
$env:AZURE_OPENAI_KEY = "FtrcUPizj8Tu9EEzbCeJwL4qtZbWNJ8SMwQTDfy0SF2AE7zfXoskJQQJ99BJACYeBjFXJ3w3AAABACOGin7P"

# Azure Search
$env:AZURE_SEARCH_ENDPOINT = "https://boatrentalfoundrysearch.search.windows.net"
$env:AZURE_SEARCH_KEY = "kyfYT1Proxvt9fT4ZBmWPcppUkvjK0rxBuEB7prkxYAzSeCmpM7L"

Write-Host "Variables corregidas aplicadas" -ForegroundColor Green

# Verificar configuracion final
Write-Host "Configuracion final:" -ForegroundColor Cyan
Write-Host "  COSMOSDB_ENDPOINT: $env:COSMOSDB_ENDPOINT" -ForegroundColor Yellow
Write-Host "  COSMOSDB_DATABASE: $env:COSMOSDB_DATABASE" -ForegroundColor Yellow
Write-Host "  COSMOSDB_CONTAINER: $env:COSMOSDB_CONTAINER" -ForegroundColor Yellow
Write-Host "  AZURE_OPENAI_ENDPOINT: $env:AZURE_OPENAI_ENDPOINT" -ForegroundColor Yellow

# Ejecutar migracion
python migrate_embeddings.py

Write-Host "`nMigracion completada" -ForegroundColor Green
Write-Host "Verifica los resultados en Azure AI Search" -ForegroundColor Cyan
