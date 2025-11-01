# Recrear indice Azure AI Search con dimensiones 3072
Write-Host "Recreando indice Azure AI Search..." -ForegroundColor Cyan

# Cargar variables desde local.settings.json
if (Test-Path "local.settings.json") {
    $settings = Get-Content "local.settings.json" | ConvertFrom-Json
    
    foreach ($key in $settings.Values.PSObject.Properties.Name) {
        $value = $settings.Values.$key
        Set-Item -Path "env:$key" -Value $value
    }
    
    Write-Host "Variables cargadas" -ForegroundColor Green
}

# Ejecutar script
python recreate_search_index.py

Write-Host "`nIndice recreado" -ForegroundColor Green
