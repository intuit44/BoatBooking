# Recuperar variables de entorno desde local.settings.json y subirlas al portal

$ErrorActionPreference = "Stop"

Write-Host "Recuperador de Variables de Entorno" -ForegroundColor Cyan
Write-Host "=" * 50

# Leer local.settings.json
try {
    $config = Get-Content "local.settings.json" -Raw | ConvertFrom-Json
    $settings = $config.Values
} catch {
    Write-Host "ERROR leyendo local.settings.json: $_" -ForegroundColor Red
    exit 1
}

$settingsCount = ($settings | Get-Member -MemberType NoteProperty).Count
Write-Host "Encontrados $settingsCount settings en local.settings.json" -ForegroundColor Green

# Configuración
$resourceGroup = "boat-rental-app-group"
$functionApp = "copiloto-semantico-func-us2"

Write-Host "`nSubiendo variables a $functionApp..." -ForegroundColor Yellow
Write-Host "Esto puede tardar 2-3 minutos...`n"

# Convertir a array de "KEY=VALUE"
$settingsArray = @()
$settings.PSObject.Properties | ForEach-Object {
    $key = $_.Name
    $value = $_.Value
    $settingsArray += "$key=$value"
}

# Subir en lotes de 10
$batchSize = 10
$totalBatches = [Math]::Ceiling($settingsArray.Count / $batchSize)

for ($i = 0; $i -lt $settingsArray.Count; $i += $batchSize) {
    $batch = $settingsArray[$i..[Math]::Min($i + $batchSize - 1, $settingsArray.Count - 1)]
    $batchNum = [Math]::Floor($i / $batchSize) + 1
    
    Write-Host "Lote $batchNum/$totalBatches ($($batch.Count) variables)..." -ForegroundColor Cyan
    
    try {
        az functionapp config appsettings set `
            -g $resourceGroup `
            -n $functionApp `
            --settings @batch `
            --output none
        
        Write-Host "  OK" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nTodas las variables recuperadas exitosamente" -ForegroundColor Green
Write-Host "Verifica en el portal: https://portal.azure.com" -ForegroundColor Cyan
