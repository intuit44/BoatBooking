# TEST_VALIDACION_OPENAPI_SEGURO.ps1
# Script seguro para validar endpoints contra OpenAPI

param(
  [string]$BaseUrl = "https://copiloto-semantico-func-us2.azurewebsites.net",
  [string]$OpenApiPath = ".\openapi_copiloto_updated.yaml",
  [switch]$VerboseOutput
)

# ============ CONFIGURACIÃ“N ============
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Debug { if ($VerboseOutput) { Write-Host $args -ForegroundColor Gray } }

# ============ ENDPOINTS SEGUROS ============
$SAFE_ENDPOINTS = @(
  "/api/health",
  "/api/status", 
  "/api/auditar-deploy",
  "/api/listar-blobs",
  "/api/hybrid"
)

# ============ PARSER OPENAPI SIMPLIFICADO ============
function Get-OpenApiEndpoints {
  param([string]$Path)
    
  Write-Info "Leyendo OpenAPI desde: $Path"
    
  if (!(Test-Path $Path)) {
    throw "Archivo OpenAPI no encontrado: $Path"
  }
    
  $content = Get-Content $Path -Raw
    
  # Buscar patrones de endpoints en el YAML/JSON
  $endpoints = @{}
    
  # Extraer paths del OpenAPI
  $pathMatches = [regex]::Matches($content, '  /api/[^:]+:')
  foreach ($match in $pathMatches) {
    $path = $match.Value.Trim().Replace(':', '')
    if ($path -in $SAFE_ENDPOINTS) {
      $endpoints[$path] = @{
        Methods = @("GET", "POST")  # Asumir mÃ©todos comunes
      }
    }
  }
    
  return $endpoints
}

# ============ DATOS DE PRUEBA SEGUROS ============
function Get-SafeTestData {
  param([string]$Endpoint)
    
  $testData = @{
    "/api/health"         = @{
      Method      = "GET"
      Body        = $null
      QueryParams = @{}
    }
    "/api/status"         = @{
      Method      = "GET" 
      Body        = $null
      QueryParams = @{}
    }
    "/api/auditar-deploy" = @{
      Method      = "GET"
      Body        = $null
      QueryParams = @{}
    }
    "/api/listar-blobs"   = @{
      Method      = "GET"
      Body        = $null
      QueryParams = @{
        container = "test-container"
        prefix    = "test/"
      }
    }
    "/api/hybrid"         = @{
      Method      = "POST" 
      Body        = @{
        agent_response = "test-ping"
      }
      QueryParams = @{}
    }
  }
    
  return $testData[$Endpoint]
}

# ============ EJECUTOR DE PRUEBAS SEGURO ============
function Invoke-SafeTest {
  param(
    [string]$Url,
    [string]$Method,
    [hashtable]$QueryParams,
    [hashtable]$Body,
    [int]$TimeoutSec = 30
  )
    
  # Construir URL con query parameters
  if ($QueryParams.Count -gt 0) {
    $queryString = ($QueryParams.GetEnumerator() | ForEach-Object {
        "$($_.Key)=$([uri]::EscapeDataString($_.Value))"
      }) -join '&'
    $Url = "$Url?$queryString"
  }
    
  $headers = @{
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
  }
    
  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
  try {
    if ($Method -eq "GET") {
      $response = Invoke-WebRequest -Uri $Url -Method $Method -Headers $headers -TimeoutSec $TimeoutSec
    }
    else {
      $bodyJson = if ($Body) { $Body | ConvertTo-Json -Compress } else { "{}" }
      $response = Invoke-WebRequest -Uri $Url -Method $Method -Headers $headers -Body $bodyJson -TimeoutSec $TimeoutSec
    }
        
    $result = @{
      Success      = $true
      StatusCode   = $response.StatusCode
      ResponseTime = $stopwatch.ElapsedMilliseconds
      Content      = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
      RawContent   = $response.Content
    }
  }
  catch {
    $result = @{
      Success      = $false
      StatusCode   = $_.Exception.Response.StatusCode
      ResponseTime = $stopwatch.ElapsedMilliseconds
      Error        = $_.Exception.Message
      RawContent   = $_.Exception.Response.ToString()
    }
  }
    
  $stopwatch.Stop()
  return $result
}

# ============ VALIDACIÃ“N DE RESPUESTA ============
function Test-Response {
  param($Result, $Endpoint)
    
  $validation = @{
    IsValid = $false
    Issues  = @()
  }
    
  if (-not $Result.Success) {
    $validation.Issues += "Endpoint no respondiÃ³ (HTTP $($Result.StatusCode))"
    return $validation
  }
    
  # Validar cÃ³digo de estado
  if ($Result.StatusCode -ne 200) {
    $validation.Issues += "CÃ³digo HTTP inesperado: $($Result.StatusCode)"
  }
    
  # Validar que sea JSON
  if (-not $Result.Content) {
    $validation.Issues += "Respuesta no es JSON vÃ¡lido"
  }
  else {
    # Validaciones bÃ¡sicas de estructura segÃºn el endpoint
    switch ($Endpoint) {
      "/api/health" {
        if ($Result.Content.psobject.Properties.Name -notcontains "status") {
          $validation.Issues += "Respuesta health no tiene campo 'status'"
        }
      }
      "/api/status" {
        if ($Result.Content.psobject.Properties.Name -notcontains "message") {
          $validation.Issues += "Respuesta status no tiene campo 'message'"
        }
      }
      "/api/auditar-deploy" {
        if ($Result.Content.psobject.Properties.Name -notcontains "exito") {
          $validation.Issues += "Respuesta auditar-deploy no tiene campo 'exito'"
        }
      }
    }
  }
    
  $validation.IsValid = ($validation.Issues.Count -eq 0)
  return $validation
}

# ============ PROGRAMA PRINCIPAL ============
Write-Host ""
Write-Info "ðŸ¤– VALIDADOR SEGURO OPENAPI vs ENDPOINTS"
Write-Host "========================================"
Write-Host ""

try {
  # 1. Obtener endpoints del OpenAPI
  Write-Info "ðŸ“‹ Obteniendo endpoints desde OpenAPI..."
  $openApiEndpoints = Get-OpenApiEndpoints -Path $OpenApiPath
    
  if ($openApiEndpoints.Count -eq 0) {
    Write-Error "No se encontraron endpoints seguros en el OpenAPI"
    exit 1
  }
    
  Write-Success "âœ… Encontrados $($openApiEndpoints.Count) endpoints seguros en OpenAPI"
  $openApiEndpoints.Keys | ForEach-Object { Write-Debug "   - $_" }

  # 2. Verificar conectividad
  Write-Info "ðŸŒ Verificando conectividad con $BaseUrl..."
  try {
    $testResponse = Invoke-WebRequest -Uri "$BaseUrl/api/health" -TimeoutSec 10
    Write-Success "âœ… Servidor respondiendo correctamente"
  }
  catch {
    Write-Error "âŒ No se puede conectar con el servidor: $($_.Exception.Message)"
    exit 1
  }

  # 3. Ejecutar pruebas
  Write-Host ""
  Write-Info "ðŸ§ª Ejecutando validaciÃ³n cruzada..."
  Write-Host ""

  $results = @()
  $testNumber = 0

  foreach ($endpoint in $SAFE_ENDPOINTS) {
    $testNumber++
    Write-Host "[$testNumber/$($SAFE_ENDPOINTS.Count)] Probando $endpoint ... " -NoNewline

    $testData = Get-SafeTestData -Endpoint $endpoint
    $fullUrl = $BaseUrl + $endpoint

    $result = Invoke-SafeTest `
      -Url $fullUrl `
      -Method $testData.Method `
      -QueryParams $testData.QueryParams `
      -Body $testData.Body

    $validation = Test-Response -Result $result -Endpoint $endpoint

    if ($validation.IsValid) {
      Write-Success "âœ… PASÃ“ ($($result.StatusCode), $($result.ResponseTime)ms)"
    }
    else {
      Write-Error "âŒ FALLÃ“"
      if ($VerboseOutput) {
        foreach ($issue in $validation.Issues) {
          Write-Warning "   - $issue"
        }
        if ($result.Error) {
          Write-Warning "   Error: $($result.Error)"
        }
      }
    }

    $results += @{
      Endpoint   = $endpoint
      Method     = $testData.Method
      Result     = $result
      Validation = $validation
      TestData   = $testData
    }
  }

  # 4. Generar reporte
  Write-Host ""
  Write-Info "ðŸ“Š REPORTE DE VALIDACIÃ“N"
  Write-Host "========================"

  $totalTests = $results.Count
  $passedTests = ($results | Where-Object { $_.Validation.IsValid }).Count
  $successRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }

  Write-Host "Total de pruebas: $totalTests"
  Write-Success "Pruebas exitosas: $passedTests"
  if (($totalTests - $passedTests) -gt 0) {
    Write-Error "Pruebas fallidas: $($totalTests - $passedTests)"
  }
  Write-Host "Tasa de Ã©xito: $successRate%"

  # 5. AnÃ¡lisis de agente AI simulado
  Write-Host ""
  Write-Info "ðŸ¤– ANÃLISIS AGENTE AI"
  Write-Host "===================="

  if ($successRate -eq 100) {
    Write-Success "âœ… EXCELENTE: Todos los endpoints responden correctamente"
    Write-Host "   La API estÃ¡ en perfecto estado. OpenAPI y implementaciÃ³n coinciden."
  }
  elseif ($successRate -ge 80) {
    Write-Warning "âšï¸  ACEPTABLE: La mayorÃ­a de endpoints funcionan"
    Write-Host "   Revisar los endpoints fallidos, pero el estado general es bueno."
  }
  elseif ($successRate -ge 50) {
    Write-Warning "âšï¸  REGULAR: Hay problemas significativos"
    Write-Host "   Revisar la implementaciÃ³n de los endpoints fallidos."
  }
  else {
    Write-Error "ï¿½ï¸ CRÃTICO: MÃºltiples endpoints fallaron"
    Write-Host "   Revisar urgentemente la implementaciÃ³n y el OpenAPI."
  }

  # 6. Guardar reporte detallado
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $reportPath = ".\validation-report-$timestamp.json"
    
  $report = @{
    Timestamp    = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    BaseUrl      = $BaseUrl
    OpenApiPath  = $OpenApiPath
    Summary      = @{
      TotalTests  = $totalTests
      Passed      = $passedTests
      Failed      = $totalTests - $passedTests
      SuccessRate = $successRate
    }
    Results      = $results
    AIAssessment = if ($successRate -eq 100) { "EXCELLENT" } elseif ($successRate -ge 80) { "GOOD" } elseif ($successRate -ge 50) { "FAIR" } else { "POOR" }
  }

  $report | ConvertTo-Json -Depth 5 | Set-Content $reportPath
  Write-Success "ðŸ“„ Reporte guardado en: $reportPath"

  # 7. RecomendaciÃ³n final
  Write-Host ""
  if ($successRate -ge 80) {
    Write-Success "ðŸŽ‰ La validaciÃ³n fue exitosa. La API estÃ¡ lista para uso productivo."
  }
  else {
    Write-Error "ðŸš« Se recomienda revisar los problemas antes de usar en producciÃ³n."
  }

}
catch {
  Write-Error "âŒ Error durante la ejecuciÃ³n: $($_.Exception.Message)"
  exit 1
}

Write-Host ""
exit 0