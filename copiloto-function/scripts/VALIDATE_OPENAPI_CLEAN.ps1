# 🧪 Validación: OpenAPI sin endpoints legacy

Write-Host "🔍 Validando que OpenAPI esté limpio..." -ForegroundColor Cyan

$baseUrl = "https://copiloto-semantico-func-us2.azurewebsites.net"
$openApiUrl = "$baseUrl/api/openapi"

# 1. Obtener OpenAPI
Write-Host "`n📥 Descargando OpenAPI desde $openApiUrl..." -ForegroundColor Yellow
try {
    $openapi = Invoke-RestMethod -Uri $openApiUrl -Method Get
    Write-Host "✅ OpenAPI descargado correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al descargar OpenAPI: $_" -ForegroundColor Red
    exit 1
}

# 2. Verificar versión
Write-Host "`n📊 Versión del OpenAPI: $($openapi.info.version)" -ForegroundColor Cyan
if ($openapi.info.version -lt "3.5") {
    Write-Host "⚠️ Versión antigua detectada. Esperada: 3.5+" -ForegroundColor Yellow
}

# 3. Verificar que NO existan endpoints legacy
Write-Host "`n🔍 Verificando ausencia de endpoints legacy..." -ForegroundColor Yellow

$legacyEndpoints = @("/api/probar-endpoint", "/api/invocar")
$foundLegacy = $false

foreach ($endpoint in $legacyEndpoints) {
    if ($openapi.paths.PSObject.Properties.Name -contains $endpoint) {
        Write-Host "❌ ENCONTRADO endpoint legacy: $endpoint" -ForegroundColor Red
        $foundLegacy = $true
    } else {
        Write-Host "✅ Confirmado: $endpoint NO existe" -ForegroundColor Green
    }
}

# 4. Verificar endpoints esperados
Write-Host "`n✅ Verificando endpoints esperados..." -ForegroundColor Yellow

$expectedEndpoints = @(
    "/api/copiloto",
    "/api/diagnostico-recursos",
    "/api/crear-contenedor",
    "/api/ejecutar-cli",
    "/api/bridge-cli",
    "/api/agent-output"
)

$allPresent = $true
foreach ($endpoint in $expectedEndpoints) {
    if ($openapi.paths.PSObject.Properties.Name -contains $endpoint) {
        Write-Host "✅ $endpoint presente" -ForegroundColor Green
    } else {
        Write-Host "❌ $endpoint FALTANTE" -ForegroundColor Red
        $allPresent = $false
    }
}

# 5. Test funcional: diagnostico-recursos
Write-Host "`n🧪 Test funcional: /api/diagnostico-recursos..." -ForegroundColor Cyan
try {
    $diagnostico = Invoke-RestMethod -Uri "$baseUrl/api/diagnostico-recursos" -Method Get
    if ($diagnostico.timestamp) {
        Write-Host "✅ /api/diagnostico-recursos funciona correctamente" -ForegroundColor Green
        Write-Host "   Timestamp: $($diagnostico.timestamp)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Respuesta inesperada de diagnostico-recursos" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error al invocar diagnostico-recursos: $_" -ForegroundColor Red
}

# 6. Test funcional: copiloto router
Write-Host "`n🧪 Test funcional: /api/copiloto (router semántico)..." -ForegroundColor Cyan
$body = @{
    mensaje = "valida el estado del sistema"
    session_id = "test-validation-$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

try {
    $copiloto = Invoke-RestMethod -Uri "$baseUrl/api/copiloto" -Method Post -Body $body -ContentType "application/json"
    if ($copiloto.exito) {
        Write-Host "✅ /api/copiloto funciona correctamente" -ForegroundColor Green
        Write-Host "   Acción detectada: $($copiloto.accion)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Respuesta inesperada de copiloto" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error al invocar copiloto: $_" -ForegroundColor Red
}

# 7. Resumen final
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE VALIDACION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if (-not $foundLegacy -and $allPresent) {
    Write-Host "OK: OpenAPI esta LIMPIO y COMPLETO" -ForegroundColor Green
    Write-Host "OK: Todos los endpoints esperados estan presentes" -ForegroundColor Green
    Write-Host "OK: NO se encontraron endpoints legacy" -ForegroundColor Green
    Write-Host "`nACCION REQUERIDA:" -ForegroundColor Yellow
    Write-Host "   Actualiza el catalogo de herramientas en Azure AI Foundry" -ForegroundColor Yellow
    Write-Host "   Ver: REFRESH_FOUNDRY_OPENAPI.md" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "ERROR: Se encontraron problemas en el OpenAPI" -ForegroundColor Red
    if ($foundLegacy) {
        Write-Host "   - Endpoints legacy aun presentes" -ForegroundColor Red
    }
    if (-not $allPresent) {
        Write-Host "   - Faltan endpoints esperados" -ForegroundColor Red
    }
    exit 1
}
