# Reset completo y migración de documentos recientes
Write-Host "Reseteando indice y migrando documentos recientes..." -ForegroundColor Cyan

# Cargar variables
if (Test-Path "local.settings.json") {
    $settings = Get-Content "local.settings.json" | ConvertFrom-Json
    
    foreach ($key in $settings.Values.PSObject.Properties.Name) {
        $value = $settings.Values.$key
        Set-Item -Path "env:$key" -Value $value
    }
    
    Write-Host "Variables cargadas" -ForegroundColor Green
}

# Imponer valores correctos
$env:COSMOSDB_ENDPOINT = "https://copiloto-cosmos.documents.azure.com:443/"
$env:COSMOSDB_DATABASE = "agentMemory"
$env:COSMOSDB_CONTAINER = "memory"
$env:AZURE_OPENAI_ENDPOINT = "https://boatrentalfoundry-openai.openai.azure.com/"

# Ejecutar reset y migración
python reset_index_and_migrate_recent.py

Write-Host "`nProceso completado" -ForegroundColor Green
Write-Host "Ahora ejecuta: python test_memoria_semantica_completa.py" -ForegroundColor Yellow
