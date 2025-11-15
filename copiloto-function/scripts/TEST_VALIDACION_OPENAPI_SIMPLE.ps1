# TEST_VALIDACION_OPENAPI_SIMPLE.ps1
# Script simplificado para validar endpoints contra OpenAPI

param(
  [string]$BaseUrl = "http://localhost:7071",
  [string]$OpenApiPath = "./openapi_copiloto_local.yaml",
  [switch]$StopOnFirstFail,
  [switch]$VerboseOutput,
  [switch]$AutoDeploy
)

$ErrorActionPreference = "Continue"

# Funciones de output
function Write-Pass { Write-Host $args -ForegroundColor Green }
function Write-Fail { Write-Host $args -ForegroundColor Red }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

Write-Info "`n=========================================="
Write-Info "   VALIDADOR DE ENDPOINTS FUNCTION APP"
Write-Info "==========================================`n"

# Leer y parsear OpenAPI (como JSON simple)
Write-Info "Leyendo OpenAPI..."
$openApiContent = Get-Content $OpenApiPath -Raw

# Extraer JSON del YAML
$jsonMatch = [regex]::Match($openApiContent, '(?s)\{.*\}')
if ($jsonMatch.Success) {
  $openApi = $jsonMatch.Value | ConvertFrom-Json
  Write-Pass "OpenAPI cargado: $($openApi.info.title) v$($openApi.info.version)"
}
else {
  Write-Fail "No se pudo parsear OpenAPI"
  exit 1
}

# Verificar conectividad
Write-Info "`nVerificando conectividad con $BaseUrl..."
try {
  $testHealth = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
  Write-Pass "Servidor activo y respondiendo"
}
catch {
  Write-Fail "No se puede conectar. Asegurate que 'func start' este ejecutandose"
  exit 1
}

# Definir casos de prueba manualmente (más simple y directo)
$testCases = @(
  # Endpoints básicos
  @{Name = "Health"; Method = "GET"; Path = "/api/health"; Body = $null; ExpectedStatus = @(200) },
  @{Name = "Status"; Method = "GET"; Path = "/api/status"; Body = $null; ExpectedStatus = @(200) },
  @{Name = "Copiloto"; Method = "GET"; Path = "/api/copiloto"; Body = $null; ExpectedStatus = @(200) },
    
  # Storage operations
  @{Name = "ListarBlobs"; Method = "GET"; Path = "/api/listar-blobs?prefix=test"; Body = $null; ExpectedStatus = @(200, 404) },
  @{Name = "EscribirArchivo"; Method = "POST"; Path = "/api/escribir-archivo"; 
    Body = @{ruta = "test/prueba.txt"; contenido = "test" }; ExpectedStatus = @(201, 200)
  },
  @{Name = "LeerArchivo"; Method = "GET"; Path = "/api/leer-archivo?ruta=test/prueba.txt"; Body = $null; ExpectedStatus = @(200, 404) },
  @{Name = "InfoArchivo"; Method = "GET"; Path = "/api/info-archivo?ruta=test/prueba.txt"; Body = $null; ExpectedStatus = @(200, 404) },
  @{Name = "EliminarArchivo"; Method = "POST"; Path = "/api/eliminar-archivo"; 
    Body = @{ruta = "test/prueba.txt" }; ExpectedStatus = @(200, 404)
  },
    
  # CLI operations
  @{Name = "EjecutarCLI"; Method = "POST"; Path = "/api/ejecutar-cli"; 
    Body = @{comando = "group list" }; ExpectedStatus = @(200, 401, 403)
  },
    
  # Container operations
  @{Name = "CrearContenedor-Invalid"; Method = "POST"; Path = "/api/crear-contenedor"; 
    Body = @{nombre = "INVALID NAME" }; ExpectedStatus = @(400)
  },
    
  # Hybrid endpoint
  @{Name = "Hybrid"; Method = "POST"; Path = "/api/hybrid"; 
    Body = @{agent_response = "ping" }; ExpectedStatus = @(200)
  },
    
  # Diagnostic endpoints
  @{Name = "DiagnosticoRecursos"; Method = "GET"; Path = "/api/diagnostico-recursos"; Body = $null; ExpectedStatus = @(200, 401) },
  @{Name = "AuditarDeploy"; Method = "GET"; Path = "/api/auditar-deploy"; Body = $null; ExpectedStatus = @(200, 401, 403, 500) },
    
  # Router principal
  @{Name = "CopilotoRouter"; Method = "POST"; Path = "/api/copiloto"; 
    Body = @{mensaje = "resumen"}; ExpectedStatus = @(200)
  },
    
  # Deploy validation
  @{Name = "Deploy-Validate"; Method = "POST"; Path = "/api/deploy"; 
    Body = @{
      resourceGroup = "test-rg"
      location      = "eastus"
      validate_only = $true
      template      = @{
        '$schema'      = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
        contentVersion = '1.0.0.0'
        resources      = @()
      }
    }; ExpectedStatus = @(200, 400, 401, 403)
  }
)

Write-Info "`nEjecutando $($testCases.Count) casos de prueba...`n"

$results = @()
$passed = 0
$failed = 0

foreach ($test in $testCases) {
  Write-Host -NoNewline "[$($results.Count + 1)/$($testCases.Count)] $($test.Name) ... "
    
  $url = $BaseUrl + $test.Path
  $headers = @{"Content-Type" = "application/json"; "Accept" = "application/json" }
    
  try {
    if ($test.Method -eq "GET") {
      $response = Invoke-WebRequest -Uri $url -Method $test.Method -Headers $headers -TimeoutSec 30 -ErrorAction Stop
    }
    else {
      $bodyJson = if ($test.Body) { $test.Body | ConvertTo-Json -Depth 10 } else { "{}" }
      $response = Invoke-WebRequest -Uri $url -Method $test.Method -Headers $headers -Body $bodyJson -TimeoutSec 30 -ErrorAction Stop
    }
        
    $statusCode = [int]$response.StatusCode
    $success = $statusCode -in $test.ExpectedStatus
        
  }
  catch {
    $errorDetail = $_.Exception
    if ($errorDetail.Response) {
      $statusCode = [int]$errorDetail.Response.StatusCode
    }
    else {
      $statusCode = 0
    }
    $success = $statusCode -in $test.ExpectedStatus
  }
    
  $result = @{
    Name           = $test.Name
    Method         = $test.Method
    Path           = $test.Path
    StatusCode     = $statusCode
    ExpectedStatus = $test.ExpectedStatus
    Success        = $success
  }
    
  $results += $result
    
  if ($success) {
    Write-Pass "PASS ($statusCode)"
    $passed++
  }
  else {
    Write-Fail "FAIL (esperado: $($test.ExpectedStatus -join ','), recibido: $statusCode)"
    $failed++
        
    if ($StopOnFirstFail) {
      Write-Warn "`nDeteniendo en primer fallo"
      break
    }
  }
}

# Resumen
Write-Info "`n=========================================="
Write-Info "              RESUMEN"
Write-Info "=========================================="
Write-Host "Total:    $($results.Count)"
Write-Pass "Exitosas: $passed"
if ($failed -gt 0) {
  Write-Fail "Fallidas: $failed"
}
else {
  Write-Host "Fallidas: 0"
}

$successRate = if ($results.Count -gt 0) { [math]::Round(($passed / $results.Count) * 100, 1) } else { 0 }
Write-Host "Tasa de exito: $successRate%`n"

# Mostrar detalles de fallidas
if ($failed -gt 0) {
  Write-Warn "Pruebas fallidas:"
  $results | Where-Object { -not $_.Success } | ForEach-Object {
    Write-Host "  - $($_.Name): esperado $($_.ExpectedStatus -join ','), recibido $($_.StatusCode)"
  }
  Write-Host ""
}

# Guardar reporte
$reportFile = ".\test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$results | ConvertTo-Json -Depth 5 | Set-Content $reportFile
Write-Info "Reporte guardado: $reportFile"

# Decision de deploy
if ($failed -eq 0) {
  Write-Pass "`n=========================================="
  Write-Pass "     TODAS LAS PRUEBAS PASARON"
  Write-Pass "==========================================`n"
    
  if ($AutoDeploy) {
    Write-Info "Iniciando deploy automatico..."
    if (Test-Path ".\fix_functionapp_final.ps1") {
      & .\fix_functionapp_final.ps1
    }
    else {
      Write-Fail "No se encontro fix_functionapp_final.ps1"
    }
  }
  else {
    Write-Info "Ejecuta el deploy con:"
    Write-Host "  .\fix_functionapp_final.ps1`n"
  }
  exit 0
}
else {
  Write-Fail "`n=========================================="
  Write-Fail "       HAY PRUEBAS FALLIDAS"
  Write-Fail "==========================================`n"
  Write-Warn "Corrige los errores antes de desplegar"
  exit 1
}
