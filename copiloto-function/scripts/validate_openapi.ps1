# Validacion OpenAPI sin endpoints legacy

Write-Host "Validando OpenAPI..." -ForegroundColor Cyan

$url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/openapi"

try {
    $openapi = Invoke-RestMethod -Uri $url -Method Get
    Write-Host "OK: OpenAPI descargado" -ForegroundColor Green
    Write-Host "Version: $($openapi.info.version)" -ForegroundColor Cyan
    
    # Verificar endpoints legacy NO existen
    $legacy = @("/api/probar-endpoint", "/api/invocar")
    $found = $false
    
    foreach ($ep in $legacy) {
        if ($openapi.paths.PSObject.Properties.Name -contains $ep) {
            Write-Host "ERROR: Encontrado $ep" -ForegroundColor Red
            $found = $true
        } else {
            Write-Host "OK: $ep no existe" -ForegroundColor Green
        }
    }
    
    # Verificar endpoints esperados
    $expected = @("/api/copiloto", "/api/diagnostico-recursos", "/api/ejecutar-cli")
    
    foreach ($ep in $expected) {
        if ($openapi.paths.PSObject.Properties.Name -contains $ep) {
            Write-Host "OK: $ep presente" -ForegroundColor Green
        } else {
            Write-Host "ERROR: $ep faltante" -ForegroundColor Red
        }
    }
    
    if (-not $found) {
        Write-Host "`nRESULTADO: OpenAPI esta limpio" -ForegroundColor Green
        Write-Host "ACCION: Actualiza Foundry (ver REFRESH_FOUNDRY_OPENAPI.md)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
