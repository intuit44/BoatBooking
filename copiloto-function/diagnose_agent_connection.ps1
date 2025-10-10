function Test-AgentConnection {
    param(
        [string]$BaseUrl = "http://localhost:7071"
    )
    
    $endpoints = @(
        "/api/health",
        "/api/status", 
        "/api/listar-blobs"
    )
    
    $successCount = 0
    $results = @()
    
    foreach ($endpoint in $endpoints) {
        $url = "$BaseUrl$endpoint"
        try {
            $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
            $exists = $true
            $successCount++
        }
        catch {
            $exists = $false
        }
        
        # Usar símbolos ASCII en lugar de caracteres especiales
        $symbol = if ($exists) { "[OK]" } else { "[FAIL]" }
        $results += "$symbol $endpoint"
        Write-Host "$symbol $url"
    }
    
    # Resultado final
    Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
    $results | ForEach-Object { Write-Host $_ }
    
    if ($successCount -eq $endpoints.Count) {
        Write-Host "`n✅ TODOS los endpoints funcionan correctamente" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "`n❌ Solo $successCount de $($endpoints.Count) endpoints responden" -ForegroundColor Red
        return $false
    }
}

# Ejecutar diagnóstico
Test-AgentConnection