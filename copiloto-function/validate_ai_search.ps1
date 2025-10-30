# Validacion Completa de Azure AI Search
$searchService = "boatrentalfoundrysearch"
$resourceGroup = "boat-rental-app-group"
$storageAccount = "boatrentalstorage"
$functionApp = "copiloto-semantico-func-us2"

Write-Host "`nVALIDACION DE AZURE AI SEARCH" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# 1. Validar servicio existe
Write-Host "1. Validando servicio Azure AI Search..." -ForegroundColor Yellow
$service = az search service show --name $searchService --resource-group $resourceGroup 2>$null
if ($service) {
    Write-Host "   OK - Servicio '$searchService' existe" -ForegroundColor Green
    $endpoint = "https://$searchService.search.windows.net"
}
else {
    Write-Host "   ERROR - Servicio no encontrado" -ForegroundColor Red
    exit 1
}

# 2. Obtener admin key
Write-Host "`n2. Obteniendo admin key..." -ForegroundColor Yellow
$adminKey = az search admin-key show `
    --service-name $searchService `
    --resource-group $resourceGroup `
    --query primaryKey -o tsv

if ($adminKey) {
    Write-Host "   OK - Admin key obtenida: $($adminKey.Substring(0,8))..." -ForegroundColor Green
}
else {
    Write-Host "   ERROR - No se pudo obtener admin key" -ForegroundColor Red
    exit 1
}

# 3. Validar indice existe
Write-Host "`n3. Validando indice 'agent-memory-index'..." -ForegroundColor Yellow
$headers = @{
    "api-key" = $adminKey
}
try {
    $index = Invoke-RestMethod -Uri "$endpoint/indexes/agent-memory-index?api-version=2023-11-01" -Headers $headers -Method Get
    Write-Host "   OK - Indice existe con $($index.fields.Count) campos" -ForegroundColor Green
    Write-Host "   Campos: id, agent_id, session_id, endpoint, timestamp, tipo, texto_semantico, vector, exito" -ForegroundColor Gray
}
catch {
    Write-Host "   AVISO - Indice NO existe - Necesita crearse" -ForegroundColor Red
    Write-Host "`n   Creando indice..." -ForegroundColor Cyan
    
    $schemaPath = Join-Path -Path $PSScriptRoot -ChildPath "azure_search_schema.json"
    if (Test-Path $schemaPath) {
        $body = Get-Content -Raw -Path $schemaPath
        $createHeaders = @{
            "Content-Type" = "application/json"
            "api-key"      = $adminKey
        }
        try {
            Invoke-RestMethod -Uri "$endpoint/indexes/agent-memory-index?api-version=2023-11-01" -Method Put -Body $body -Headers $createHeaders
            Write-Host "   OK - Indice creado exitosamente" -ForegroundColor Green
        }
        catch {
            Write-Host "   ERROR - Error creando indice: $_" -ForegroundColor Red
        }
    }
    else {
        Write-Host "   ERROR - Schema file no encontrado en $schemaPath" -ForegroundColor Red
    }
}

# 4. Validar cola de storage
Write-Host "`n4. Validando cola 'memory-indexing-queue'..." -ForegroundColor Yellow
try {
    $queue = az storage queue exists `
        --name memory-indexing-queue `
        --account-name $storageAccount `
        --query exists -o tsv 2>$null

    if ($queue -eq "true") {
        Write-Host "   OK - Cola existe" -ForegroundColor Green
    }
    else {
        Write-Host "   AVISO - Cola NO existe - Creando..." -ForegroundColor Yellow
        az storage queue create `
            --name memory-indexing-queue `
            --account-name $storageAccount
        Write-Host "   OK - Cola creada" -ForegroundColor Green
    }
}
catch {
    Write-Host "   AVISO - Error validando cola: $_" -ForegroundColor Yellow
}

# 5. Validar variables de entorno en Function App
Write-Host "`n5. Validando variables de entorno..." -ForegroundColor Yellow
try {
    $settings = az functionapp config appsettings list `
        --name $functionApp `
        --resource-group $resourceGroup | ConvertFrom-Json

    $searchEndpoint = ($settings | Where-Object { $_.name -eq "AZURE_SEARCH_ENDPOINT" }).value
    $searchKey = ($settings | Where-Object { $_.name -eq "AZURE_SEARCH_KEY" }).value

    if ($searchEndpoint) {
        Write-Host "   OK - AZURE_SEARCH_ENDPOINT: $searchEndpoint" -ForegroundColor Green
    }
    else {
        Write-Host "   AVISO - AZURE_SEARCH_ENDPOINT no configurado" -ForegroundColor Red
        Write-Host "   Configurando..." -ForegroundColor Cyan
        az functionapp config appsettings set `
            --name $functionApp `
            --resource-group $resourceGroup `
            --settings AZURE_SEARCH_ENDPOINT=$endpoint
    }

    if ($searchKey) {
        Write-Host "   OK - AZURE_SEARCH_KEY: $($searchKey.Substring(0,8))..." -ForegroundColor Green
    }
    else {
        Write-Host "   AVISO - AZURE_SEARCH_KEY no configurado" -ForegroundColor Red
        Write-Host "   Configurando..." -ForegroundColor Cyan
        az functionapp config appsettings set `
            --name $functionApp `
            --resource-group $resourceGroup `
            --settings AZURE_SEARCH_KEY=$adminKey
    }
}
catch {
    Write-Host "   AVISO - Error validando variables: $_" -ForegroundColor Yellow
}

# 6. Validar local.settings.json
Write-Host "`n6. Validando local.settings.json..." -ForegroundColor Yellow
$localSettingsPath = Join-Path -Path $PSScriptRoot -ChildPath "local.settings.json"
if (Test-Path $localSettingsPath) {
    $localSettings = Get-Content -Raw -Path $localSettingsPath | ConvertFrom-Json
    
    if ($localSettings.Values.AZURE_SEARCH_ENDPOINT) {
        Write-Host "   OK - AZURE_SEARCH_ENDPOINT en local.settings.json" -ForegroundColor Green
    }
    else {
        Write-Host "   AVISO - AZURE_SEARCH_ENDPOINT falta en local.settings.json" -ForegroundColor Yellow
        Write-Host "   Agregar: `"AZURE_SEARCH_ENDPOINT`": `"$endpoint`"" -ForegroundColor Gray
    }
    
    if ($localSettings.Values.AZURE_SEARCH_KEY) {
        Write-Host "   OK - AZURE_SEARCH_KEY en local.settings.json" -ForegroundColor Green
    }
    else {
        Write-Host "   AVISO - AZURE_SEARCH_KEY falta en local.settings.json" -ForegroundColor Yellow
        Write-Host "   Agregar: `"AZURE_SEARCH_KEY`": `"$adminKey`"" -ForegroundColor Gray
    }
}
else {
    Write-Host "   ERROR - local.settings.json no encontrado" -ForegroundColor Red
}

# Resumen final
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "VALIDACION COMPLETADA" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`nConfiguracion:" -ForegroundColor Yellow
Write-Host "   Servicio: $searchService" -ForegroundColor White
Write-Host "   Endpoint: $endpoint" -ForegroundColor White
Write-Host "   Indice: agent-memory-index" -ForegroundColor White
Write-Host "   Cola: memory-indexing-queue" -ForegroundColor White
Write-Host "`nProximo paso: Ejecutar funcion para probar indexacion`n" -ForegroundColor Cyan
