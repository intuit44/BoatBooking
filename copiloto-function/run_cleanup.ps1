# Limpiar documentos antiguos de Azure AI Search
Write-Host "Limpiando documentos antiguos..." -ForegroundColor Cyan

# Cargar variables desde local.settings.json
if (Test-Path "local.settings.json") {
    $settings = Get-Content "local.settings.json" | ConvertFrom-Json
    
    foreach ($key in $settings.Values.PSObject.Properties.Name) {
        $value = $settings.Values.$key
        Set-Item -Path "env:$key" -Value $value
    }
    
    Write-Host "Variables cargadas" -ForegroundColor Green
}

# Ejecutar limpieza
python cleanup_old_documents.py

Write-Host "`nLimpieza completada" -ForegroundColor Green
Write-Host "Ahora puedes ejecutar la migracion incremental" -ForegroundColor Yellow
