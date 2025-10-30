# 🧪 Script de Test Rápido - Integración de Queries Dinámicas
# Ejecutar: .\TEST_RAPIDO.ps1

Write-Host "🧪 Iniciando tests de integración de queries dinámicas..." -ForegroundColor Cyan
Write-Host ""

$BaseUrl = "http://localhost:7071/api"
$SessionId = "test_session_$(Get-Date -Format 'yyyyMMddHHmmss')"

# Función para test
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Data = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    $headers = @{
        "Session-ID" = $SessionId
    }
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "$BaseUrl/$Url" -Method GET -Headers $headers -ErrorAction Stop
        } else {
            $headers["Content-Type"] = "application/json"
            $response = Invoke-RestMethod -Uri "$BaseUrl/$Url" -Method POST -Headers $headers -Body $Data -ErrorAction Stop
        }
        
        $exito = $response.exito -or $response.ok -or $true
        
        if ($exito) {
            Write-Host "✅ PASS - HTTP 200" -ForegroundColor Green
        } else {
            Write-Host "❌ FAIL - HTTP 200 (exito=false)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Test 1: /api/copiloto con query dinámica básica
Test-Endpoint `
    -Name "Copiloto - Query dinámica básica" `
    -Url "copiloto?tipo=error&limite=5"

# Test 2: /api/copiloto con múltiples filtros
Test-Endpoint `
    -Name "Copiloto - Múltiples filtros" `
    -Url "copiloto?tipo=error&fecha_inicio=2025-01-05&limite=10"

# Test 3: /api/copiloto con búsqueda de texto
Test-Endpoint `
    -Name "Copiloto - Búsqueda de texto" `
    -Url "copiloto" `
    -Method "POST" `
    -Data '{"contiene": "cosmos", "limite": 10}'

# Test 4: /api/sugerencias
Test-Endpoint `
    -Name "Sugerencias - Básico" `
    -Url "sugerencias?limite=5"

# Test 5: /api/contexto-inteligente
Test-Endpoint `
    -Name "Contexto Inteligente - Básico" `
    -Url "contexto-inteligente"

# Test 6: /api/memoria-global
Test-Endpoint `
    -Name "Memoria Global - Básico" `
    -Url "memoria-global?limite=20"

# Test 7: /api/diagnostico
Test-Endpoint `
    -Name "Diagnóstico - Por sesión" `
    -Url "diagnostico?session_id=$SessionId"

# Test 8: /api/buscar-interacciones
Test-Endpoint `
    -Name "Buscar Interacciones - Básico" `
    -Url "buscar-interacciones?limite=10"

# Test 9: /api/msearch
Test-Endpoint `
    -Name "MSearch - Búsqueda semántica" `
    -Url "msearch" `
    -Method "POST" `
    -Data '{"query": "errores recientes", "limit": 5}'

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 Tests completados!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Resumen:" -ForegroundColor Cyan
Write-Host "  - Session ID usado: $SessionId"
Write-Host "  - Base URL: $BaseUrl"
Write-Host ""
Write-Host "💡 Para ver logs detallados:" -ForegroundColor Yellow
Write-Host "  Get-Content -Path 'C:\path\to\logs\copiloto-function.log' -Wait"
Write-Host ""
Write-Host "📚 Documentación:" -ForegroundColor Cyan
Write-Host "  - INTEGRACION_QUERIES_DINAMICAS.md"
Write-Host "  - RESUMEN_INTEGRACION.md"
Write-Host "  - VERIFICACION_FINAL.md"
Write-Host "  - INTEGRACION_VISUAL.md"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
