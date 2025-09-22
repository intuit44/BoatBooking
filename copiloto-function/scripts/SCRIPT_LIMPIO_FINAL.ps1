# TEST_COMPLETO_VALIDACION_OPENAPI.ps1
# Script de validacin completa que simula comportamiento del agente AI

param(
  [string]$BaseUrl = "http://localhost:7071",
  [string]$OpenApiPath = "../openapi_copiloto_local.yaml",
  [switch]$StopOnFirstFail,
  [switch]$VerboseOutput,
  [switch]$AutoDeploy
)

# ============ CONFIGURACIN ============
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Colores para output
function Write-Pass { Write-Host $args -ForegroundColor Green }
function Write-Fail { Write-Host $args -ForegroundColor Red }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Debug { if ($VerboseOutput) { Write-Host $args -ForegroundColor Gray } }

# ============ PARSER OPENAPI ============
function ConvertFrom-OpenApi {
  param([string]$Path)
    
  Write-Info "Parseando OpenAPI desde: $Path"
    
  $content = Get-Content $Path -Raw
    
  try {
    $spec = $content | ConvertFrom-Json
    Write-Debug "Parseado como JSON"
    return $spec
  }
  catch {
    try {
      if (!(Get-Module -ListAvailable -Name powershell-yaml)) {
        Write-Warn "Instalando mdulo powershell-yaml..."
        Install-Module -Name powershell-yaml -Force -Scope CurrentUser
      }
      Import-Module powershell-yaml
      $spec = ConvertFrom-Yaml $content
      Write-Debug "Parseado como YAML"
      return $spec
    }
    catch {
      Write-Debug "Intentando parsear JSON embebido..."
      $jsonMatch = [regex]::Match($content, '(?s)\{.*\}')
      if ($jsonMatch.Success) {
        $spec = $jsonMatch.Value | ConvertFrom-Json
        Write-Debug "Parseado JSON embebido"
        return $spec
      }
      else {
        throw "No se pudo parsear el OpenAPI"
      }
    }
  }
}

# ============ GENERADOR DE CASOS DE PRUEBA ============
function New-TestCases {
  param($OpenApiSpec)
    
  $testCases = @()
  $paths = $OpenApiSpec.paths
    
  foreach ($path in $paths.PSObject.Properties) {
    $pathUrl = $path.Name
    $methods = $path.Value
        
    foreach ($method in $methods.PSObject.Properties) {
      $methodName = $method.Name.ToUpper()
      $operation = $method.Value
            
      if ($methodName -in @("GET", "POST", "PUT", "DELETE", "PATCH")) {
        $testCase = @{
          Path          = $pathUrl
          Method        = $methodName
          OperationId   = $operation.operationId
          Summary       = $operation.summary
          Tags          = $operation.tags
          Security      = $operation.security
          Parameters    = $operation.parameters
          RequestBody   = $operation.requestBody
          Responses     = $operation.responses
          TestScenarios = @()
        }
                
        $testCase.TestScenarios += New-TestScenarios -Operation $operation -Path $pathUrl -Method $methodName
        $testCases += $testCase
      }
    }
  }
    
  return $testCases
}

# ============ GENERADOR DE ESCENARIOS ============
function New-TestScenarios {
  param($Operation, $Path, $Method)
    
  $scenarios = @()
    
  $validScenario = @{
    Name           = "Valid_MinimalRequired"
    Description    = "Llamada con parmetros mnimos requeridos"
    ExpectedStatus = @(200, 201)
    Body           = $null
    QueryParams    = @{}
  }
    
  if ($Operation.parameters) {
    foreach ($param in $Operation.parameters) {
      if ($param.required) {
        $validScenario.QueryParams[$param.name] = Get-SampleValue -Schema $param.schema -ParamName $param.name
      }
    }
  }
    
  if ($Operation.requestBody -and $Operation.requestBody.required) {
    $content = $Operation.requestBody.content.'application/json'
    if ($content -and $content.schema) {
      $validScenario.Body = New-SampleBody -Schema $content.schema -Path $Path
    }
  }
    
  $scenarios += $validScenario
    
  if ($Operation.parameters -or $Operation.requestBody) {
    $invalidScenario = @{
      Name           = "Invalid_MissingRequired"
      Description    = "Llamada sin parmetros requeridos"
      ExpectedStatus = @(200, 400, 422)
      Body           = @{}
      QueryParams    = @{}
    }
    $scenarios += $invalidScenario
  }
    
  if ($Method -eq "POST" -or $Method -eq "PUT") {
    $malformedScenario = @{
      Name           = "Invalid_MalformedBody"
      Description    = "Llamada con body malformado"
      ExpectedStatus = @(400, 422, 500)
      Body           = "invalid json {["
      QueryParams    = @{}
    }
    $scenarios += $malformedScenario
  }
    
  # Inicializar archivos necesarios para cada escenario
  foreach ($scenario in $scenarios) {
    Initialize-TestFiles -TestCase @{ Path = $Path } -Scenario $scenario
  }
    
  return $scenarios
}

# ============ CASOS ESPECIALES PARA PATHS ESPECFICOS ============
function Get-SpecialCaseBody {
  param($Path, $Schema)
    
  $specialBodyCases = @{
    "/api/mover-archivo"  = @{
      origen  = "test/archivo-origen_$(Get-Random -Maximum 9999).txt"
      destino = "test/archivo-destino_$(Get-Random -Maximum 9999).txt"
    }
    "/api/copiar-archivo" = @{
      origen  = "test/archivo1_$(Get-Random -Maximum 9999).txt"
      destino = "test/archivo2_$(Get-Random -Maximum 9999).txt"
    }
  }
    
  if ($specialBodyCases.ContainsKey($Path)) {
    return $specialBodyCases[$Path]
  }
    
  return $null
}

# ============ PREPARACIN DE ARCHIVOS PARA PRUEBAS ============
function Initialize-TestFiles {
  param($TestCase, $Scenario)
  
  # Variable global para la raz del proyecto (ajusta segn tu estructura)
  if (-not $global:PROYECTO_RAIZ) {
    $global:PROYECTO_RAIZ = "."
  }
  
  # Crear archivo origen para /api/copiar-archivo
  if ($TestCase.Path -eq "/api/copiar-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $origen = $Scenario.Body.origen
    if ($origen) {
      $origenPath = Join-Path $global:PROYECTO_RAIZ $origen
      $origenDir = Split-Path $origenPath -Parent
      if (!(Test-Path $origenDir)) {
        New-Item -ItemType Directory -Path $origenDir -Force | Out-Null
      }
      if (!(Test-Path $origenPath)) {
        New-Item -ItemType File -Path $origenPath -Force | Out-Null
        Set-Content -Path $origenPath -Value "Contenido generado automticamente para pruebas - $(Get-Date)"
      }
      Write-Debug "Archivo origen creado: $origenPath"
    }
  }
  
  # Crear archivo origen para /api/mover-archivo
  if ($TestCase.Path -eq "/api/mover-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $origen = $Scenario.Body.origen
    if ($origen) {
      $origenPath = Join-Path $global:PROYECTO_RAIZ $origen
      $origenDir = Split-Path $origenPath -Parent
      if (!(Test-Path $origenDir)) {
        New-Item -ItemType Directory -Path $origenDir -Force | Out-Null
      }
      if (!(Test-Path $origenPath)) {
        New-Item -ItemType File -Path $origenPath -Force | Out-Null
        Set-Content -Path $origenPath -Value "Contenido generado automticamente para pruebas - $(Get-Date)"
      }
      Write-Debug "Archivo origen creado: $origenPath"
    }
  }

  # Crear archivo para /api/leer-archivo
  if ($TestCase.Path -eq "/api/leer-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    Write-Host " Initialize-TestFiles: Procesando /api/leer-archivo" -ForegroundColor Yellow
    $ruta = $Scenario.QueryParams["ruta"]
    Write-Host " Ruta inicial: '$ruta'" -ForegroundColor Yellow
    if (-not $ruta) {
      # Fallback: generar ruta si no existe
      $ruta = "test/sample_$(Get-Random -Maximum 9999).txt"
      $Scenario.QueryParams["ruta"] = $ruta
      Write-Host " Ruta generada: '$ruta'" -ForegroundColor Yellow
    }  #  CIERRE FALTANTE AQU
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      Write-Host " Creando directorio: '$rutaDir'" -ForegroundColor Yellow
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      Write-Host " Creando archivo: '$rutaPath'" -ForegroundColor Yellow
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "Archivo de lectura para prueba - $(Get-Date)"
      }
      Write-Host "  Archivo de lectura creado: $rutaPath" -ForegroundColor Green
      Write-Host " QueryParams final: $($Scenario.QueryParams | ConvertTo-Json -Compress)" -ForegroundColor Yellow
    }
  }

  # Crear archivo para /api/info-archivo
  if ($TestCase.Path -eq "/api/info-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $ruta = $Scenario.QueryParams["ruta"]
    if (-not $ruta) {
      # Fallback: generar ruta si no existe
      $ruta = "test/info_$(Get-Random -Maximum 9999).txt"
      $Scenario.QueryParams["ruta"] = $ruta
    }
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "Archivo para info - $(Get-Date)"
      }
      Write-Debug "Archivo para info creado: $rutaPath"
    }
  }

  # Crear archivo para /api/preparar-script
  if ($TestCase.Path -eq "/api/preparar-script" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $ruta = $Scenario.Body["ruta"]
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "#!/usr/bin/env python3`nprint('Preparar script $(Get-Date)')"
      }
      Write-Debug "Script preparado: $rutaPath"
      # Poblar campos adicionales requeridos
      $Scenario.Body["scriptName"] = [System.IO.Path]::GetFileNameWithoutExtension($ruta)
      $Scenario.Body["tipo"] = "python"
    }
  }

  # Crear archivo para /api/ejecutar-script
  if ($TestCase.Path -eq "/api/ejecutar-script" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $script = $Scenario.Body["script"]
    if ($script) {
      $scriptPath = Join-Path $global:PROYECTO_RAIZ $script
      $scriptDir = Split-Path $scriptPath -Parent
      if (!(Test-Path $scriptDir)) {
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
      }
      if (!(Test-Path $scriptPath)) {
        New-Item -ItemType File -Path $scriptPath -Force | Out-Null
        Set-Content -Path $scriptPath -Value "print('Test script ejecutado - $(Get-Date)')"
      }
      Write-Debug "Script creado: $scriptPath"
    }
  }

  # Crear archivo para /api/ejecutar-script-local
  if ($TestCase.Path -eq "/api/ejecutar-script-local" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $script = $Scenario.Body["script"]
    if ($script) {
      $scriptPath = Join-Path $global:PROYECTO_RAIZ $script
      $scriptDir = Split-Path $scriptPath -Parent
      if (!(Test-Path $scriptDir)) {
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
      }
      if (!(Test-Path $scriptPath)) {
        New-Item -ItemType File -Path $scriptPath -Force | Out-Null
        Set-Content -Path $scriptPath -Value "print('Script ejecutado')"
      }
      Write-Debug "Script local creado: $scriptPath"
    }
  }
}
# ============ GENERADOR DE VALORES DE EJEMPLO ============
function Get-SampleValue {

  param($Schema, $ParamName)
    
  $knownValues = @{
    "ruta"        = "test/sample_$(Get-Random -Maximum 9999).txt"
    "path"        = "test/sample_$(Get-Random -Maximum 9999).txt"
    "container"   = "boat-rental-project"
    "contenedor"  = "boat-rental-project"
    "prefix"      = "test/"
    "nombre"      = "test-container-$(Get-Random -Maximum 9999)"
    "comando"     = "group list"
    "servicio"    = "storage"
    "endpoint"    = "/api/status"
    "method"      = "GET"
    "recurso"     = "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app"
    "resourceId"  = "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app"
    "workspaceId" = "/subscriptions/test/resourceGroups/test-rg/providers/microsoft.operationalinsights/workspaces/test-ws"
  }
    
  if ($knownValues.ContainsKey($ParamName)) {
    return $knownValues[$ParamName]
  }
    
  if ($Schema) {
    switch ($Schema.type) {
      "string" { 
        if ($Schema.enum) { return $Schema.enum[0] }
        if ($Schema.pattern) { return "test-value" }
        return "test-string"
      }
      "integer" { return 1 }
      "number" { return 1.0 }
      "boolean" { return $true }
      "array" { return @("item1", "item2") }
      "object" { return @{} }
      default { return "test-value" }
    }
  }
    
  return "test-value"
}

# ============ GENERADOR DE BODY DE EJEMPLO ============
function New-SampleBody {
  param($Schema, $Path)

  $fromSpecial = Get-SpecialCaseBody -Path $Path -Schema $Schema
  if ($fromSpecial) {
    return $fromSpecial
  }
    
  $body = @{}
    
  $specialCases = @{
    "/api/crear-contenedor"        = @{
      nombre   = "test-container-$(Get-Random -Maximum 9999)"
      publico  = $false
      metadata = @{ created_by = "test" }
    }
    "/api/escribir-archivo"        = @{
      ruta      = "test/archivo-escribir_$(Get-Random -Maximum 9999).txt"
      contenido = "Test content $(Get-Date)"
    }
    "/api/modificar-archivo"       = @{
      ruta      = "test/archivo-modificar_$(Get-Random -Maximum 9999).txt"
      operacion = "agregar_final"
      contenido = "New line"
    }
    "/api/copiar-archivo"          = @{
      origen  = "test/archivo-origen_$(Get-Random -Maximum 9999).txt"
      destino = "test/archivo-destino_$(Get-Random -Maximum 9999).txt"
    }
    "/api/desplegar-funcion"       = @{
      function_app   = "copiloto-semantico-func-us2"
      resource_group = "boat-rental-app-group"
      zip_path       = "deployment.zip"
    }
    "/api/mover-archivo"           = @{
      origen  = "test/archivo-origen_$(Get-Random -Maximum 9999).txt"
      destino = "test/archivo-destino_$(Get-Random -Maximum 9999).txt"
    }
    "/api/ejecutar-cli"            = @{
      comando = "group list"
    }
    "/api/ejecutar-script"         = @{
      script    = "scripts/test_$(Get-Random -Maximum 9999).py"
      args      = @()
      timeout_s = 30
    }
    "/api/preparar-script"         = @{
      ruta = "scripts/setup_$(Get-Random -Maximum 9999).py"
    }
    "/api/ejecutar-script-local"   = @{
      script = "scripts/test_$(Get-Random -Maximum 9999).py"
      args   = @()
    }
    "/api/hybrid"                  = @{
      agent_response = "ping"
    }
    "/api/render-error"            = @{
      status_code = 400
      payload     = @{
        error = "Test error message"
      }
    }
    "/api/escalar-plan"            = @{
      plan_name      = "copiloto-linux-premium"
      resource_group = "boat-rental-app-group"
      sku            = "EP1"
    }
    "/api/auditar-deploy"          = @{
      function_app   = "copiloto-semantico-func-us2"
      resource_group = "boat-rental-app-group"
    }
    "/api/actualizar-contenedor"   = @{
      tag = "v12"
    }
    "/api/configurar-app-settings" = @{
      function_app   = "copiloto-semantico-func-us2"
      resource_group = "boat-rental-app-group"
      settings       = @{
        TEST_SETTING = "test-value"
        DEBUG_MODE   = "false"
      }
    }
    "/api/proxy-local"             = @{
      comando = "docker build -t mi-imagen ."
    }
    "/api/deploy"                  = @{
      resourceGroup = "test-rg"
      location      = "eastus"
      validate_only = $true
      template      = @{
        '$schema'      = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
        contentVersion = '1.0.0.0'
        resources      = @()
      }
    }
  }
    
  if ($specialCases.ContainsKey($Path)) {
    return $specialCases[$Path]
  }
    
  if ($Schema.properties) {
    foreach ($prop in $Schema.properties.PSObject.Properties) {
      $propName = $prop.Name
      $propSchema = $prop.Value
            
      if (!$Schema.required -or $propName -in $Schema.required) {
        $body[$propName] = Get-SampleValue -Schema $propSchema -ParamName $propName
      }
    }
  }
  elseif ($Schema.oneOf -or $Schema.anyOf) {
    $selectedSchema = if ($Schema.oneOf) { $Schema.oneOf[0] } else { $Schema.anyOf[0] }
    return New-SampleBody -Schema $selectedSchema -Path $Path
  }
    
  return $body
}

# ============ EJECUTOR DE PRUEBAS ============
function Invoke-TestCase {
  param(
    [string]$BaseUrl,
    [string]$Path,
    [string]$Method,
    [hashtable]$QueryParams,
    $Body,
    [int[]]$ExpectedStatus,
    [int]$TimeoutSec = 30
  )
    
  $url = $BaseUrl + $Path
    
  if ($QueryParams -and $QueryParams.Count -gt 0) {
    $queryString = ($QueryParams.GetEnumerator() | ForEach-Object {
        "$($_.Key)=$([uri]::EscapeDataString($_.Value))"
      }) -join '&'
    $url = "$url?$queryString"
  }
    
  $headers = @{
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
  }
    
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
    
  try {
    if ($Method -in @("GET", "DELETE")) {
      $response = Invoke-WebRequest -Uri $url -Method $Method -Headers $headers -TimeoutSec $TimeoutSec -ErrorAction Stop
    }
    else {
      if ($Body -is [string]) {
        $bodyJson = $Body
      }
      elseif ($Body) {
        $bodyJson = $Body | ConvertTo-Json -Depth 20 -Compress
      }
      else {
        $bodyJson = "{}"
      }
            
      Write-Debug "Request Body: $bodyJson"
      $response = Invoke-WebRequest -Uri $url -Method $Method -Headers $headers -Body $bodyJson -TimeoutSec $TimeoutSec -ErrorAction Stop
    }
        
    $statusCode = $response.StatusCode
    $responseBody = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    if (!$responseBody) { $responseBody = $response.Content }
        
    $success = $statusCode -in $ExpectedStatus
  }
  catch {
    $errorResponse = $_.Exception.Response
    $statusCode = if ($errorResponse) { [int]$errorResponse.StatusCode } else { 0 }
        
    try {
      $stream = $errorResponse.GetResponseStream()
      $reader = New-Object System.IO.StreamReader($stream)
      $responseText = $reader.ReadToEnd()
      $responseBody = $responseText | ConvertFrom-Json -ErrorAction SilentlyContinue
      if (!$responseBody) { $responseBody = $responseText }
    }
    catch {
      $responseBody = @{ error = $_.ToString() }
    }
        
    $success = $statusCode -in $ExpectedStatus
  }
    
  $sw.Stop()
    
  return @{
    Success      = $success
    StatusCode   = $statusCode
    ResponseBody = $responseBody
    ResponseTime = $sw.ElapsedMilliseconds
    Url          = $url
    Method       = $Method
  }
}

# ============ GENERADOR DE REPORTE ============
function New-TestReport {
  param($Results)
    
  $totalTests = $Results.Count
  $passedTests = ($Results | Where-Object { $_.TestResult.Success }).Count
  $failedTests = $totalTests - $passedTests
    
  $report = @{
    Summary          = @{
      TotalTests  = $totalTests
      Passed      = $passedTests
      Failed      = $failedTests
      SuccessRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
      Timestamp   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    ByTag            = @{}
    ByMethod         = @{}
    FailedTests      = @()
    ValidationErrors = @()
  }
    
  $tags = $Results | Where-Object { $_.Tags } | ForEach-Object { $_.Tags } | Where-Object { $_ } | Select-Object -Unique
  foreach ($tag in $tags) {
    if ($tag) {
      $tagTests = $Results | Where-Object { $_.Tags -and ($tag -in $_.Tags) }
      $tagPassed = ($tagTests | Where-Object { $_.TestResult.Success }).Count
      $report.ByTag[$tag] = @{
        Total  = $tagTests.Count
        Passed = $tagPassed
        Failed = $tagTests.Count - $tagPassed
      }
    }
  }
    
  $methods = $Results | Where-Object { $_.PSObject.Properties.Name -contains "Method" } | Select-Object -ExpandProperty Method -Unique

  foreach ($method in $methods) {
    $methodTests = $Results | Where-Object { $_.Method -eq $method }
    $methodPassed = ($methodTests | Where-Object { $_.TestResult.Success }).Count
    $report.ByMethod[$method] = @{
      Total  = $methodTests.Count
      Passed = $methodPassed
      Failed = $methodTests.Count - $methodPassed
    }
  }
    
  $failedResults = $Results | Where-Object { $_.TestResult -and -not $_.TestResult.Success }
  foreach ($failed in $failedResults) {
    $report.FailedTests += @{
      Path           = if ($failed.Path) { $failed.Path } else { "unknown" }
      Method         = if ($failed.Method) { $failed.Method } else { "unknown" }
      OperationId    = if ($failed.OperationId) { $failed.OperationId } else { "unknown" }
      Scenario       = if ($failed.ScenarioName) { $failed.ScenarioName } else { "unknown" }
      StatusCode     = if ($failed.TestResult.StatusCode) { $failed.TestResult.StatusCode } else { 0 }
      ExpectedStatus = if ($failed.ExpectedStatus) { $failed.ExpectedStatus } else { @() }
      ResponseTime   = if ($failed.TestResult.ResponseTime) { $failed.TestResult.ResponseTime } else { 0 }
      Error          = if ($failed.TestResult.ResponseBody) { $failed.TestResult.ResponseBody } else { "No response" }
    }
  }
    
  return $report
}

# ============ PROGRAMA PRINCIPAL ============
Write-Host ""
Write-Info "VALIDADOR COMPLETO DE OPENAPI PARA FUNCTION APP"
Write-Host ""

# Paso 1: Parsear OpenAPI
try {
  $openApiSpec = ConvertFrom-OpenApi -Path $OpenApiPath
  Write-Pass "OpenAPI parseado correctamente"
  Write-Info "  Titulo: $($openApiSpec.info.title)"
  Write-Info "  Version: $($openApiSpec.info.version)"
  Write-Host ""
}
catch {
  Write-Fail "Error parseando OpenAPI: $_"
  exit 1
}

# Paso 2: Generar casos de prueba
Write-Info "Generando casos de prueba desde OpenAPI..."
$testCases = New-TestCases -OpenApiSpec $openApiSpec
Write-Pass "Generados $($testCases.Count) endpoints para probar"

$totalScenarios = ($testCases | ForEach-Object { $_.TestScenarios.Count } | Measure-Object -Sum).Sum
Write-Info "  Total de escenarios: $totalScenarios"
Write-Host ""

# Paso 3: Verificar conectividad
Write-Info "Verificando conectividad con $BaseUrl..."
try {
  $null = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
  Write-Pass "Servidor respondiendo correctamente"
  Write-Host ""
}
catch {
  Write-Fail "No se puede conectar con $BaseUrl"
  Write-Warn "  Asegurate de que 'func start' este ejecutandose"
  exit 1
}

# Paso 4: Ejecutar pruebas
Write-Info "Ejecutando pruebas..."
Write-Host ""

$allResults = @()
$testNumber = 0
$totalTests = $totalScenarios

foreach ($testCase in $testCases) {
  foreach ($scenario in $testCase.TestScenarios) {
    $testNumber++
        
    Write-Host -NoNewline "[$testNumber/$totalTests] "
    Write-Host -NoNewline "$($testCase.Method) $($testCase.Path) "
    Write-Host -NoNewline "($($scenario.Name)) ... "
        
    $result = Invoke-TestCase `
      -BaseUrl $BaseUrl `
      -Path $testCase.Path `
      -Method $testCase.Method `
      -QueryParams $scenario.QueryParams `
      -Body $scenario.Body `
      -ExpectedStatus $scenario.ExpectedStatus `
      -TimeoutSec 30
        
    $testResult = @{
      Path                = $testCase.Path
      Method              = $testCase.Method
      OperationId         = if ($testCase.OperationId) { $testCase.OperationId } else { "unknown" }
      Summary             = if ($testCase.Summary) { $testCase.Summary } else { "" }
      Tags                = if ($testCase.Tags) { $testCase.Tags } else { @() }
      ScenarioName        = $scenario.Name
      ScenarioDescription = $scenario.Description
      ExpectedStatus      = $scenario.ExpectedStatus
      TestResult          = $result
    }
        
    $allResults += $testResult
        
    if ($result.Success) {
      Write-Pass ("PASS ({0}, {1}ms)" -f $result.StatusCode, $result.ResponseTime)
    }
    else {
      Write-Fail ("FAIL (esperado: {0}, recibido: {1})" -f ($scenario.ExpectedStatus -join ','), $result.StatusCode)
      if ($VerboseOutput -and $result.ResponseBody) {
        Write-Debug ("    Response: { 0 }" -f ($result.ResponseBody | ConvertTo-Json -Compress))
      }
            
      if ($StopOnFirstFail) {
        Write-Host ""
        Write-Fail "Deteniendo en el primer fallo"
        break
      }
    }
  }
    
  if ($StopOnFirstFail -and -not $result.Success) {
    break
  }
}

Write-Host ""

# Paso 5: Generar reporte
Write-Info "Generando reporte de pruebas..."
$report = New-TestReport -Results $allResults

# Mostrar resumen
Write-Host ""
Write-Info "RESUMEN DE PRUEBAS"
Write-Host ""

Write-Host "Total de pruebas:    $($report['Summary']['TotalTests'])"
Write-Pass "Pruebas exitosas:    $($report['Summary']['Passed'])"
if ($report['Summary']['Failed'] -gt 0) {
  Write-Fail "Pruebas fallidas:    $($report['Summary']['Failed'])"
}
else {
  Write-Host "Pruebas fallidas:    0"
}
Write-Host "Tasa de exito:       $($report['Summary']['SuccessRate'])%"
Write-Host ""

# Resumen por metodo
Write-Info "Por metodo HTTP:"
foreach ($method in $report.ByMethod.Keys | Sort-Object) {
  $methodData = $report.ByMethod[$method]
  $methodSuccess = if ($methodData.Total -gt 0) { [math]::Round(($methodData.Passed / $methodData.Total) * 100, 0) } else { 0 }
  $percentStr = "$methodSuccess%"
  Write-Host "  ${method}: $($methodData.Passed)/$($methodData.Total) ($percentStr)" -ForegroundColor Cyan


}
Write-Host ""

# Mostrar tests fallidos
if ($report.FailedTests.Count -gt 0) {
  Write-Fail "PRUEBAS FALLIDAS"
  Write-Host ""
    
  foreach ($failed in $report.FailedTests) {
    Write-Fail "$($failed.Method) $($failed.Path)"
    Write-Host "   Escenario: $($failed.Scenario)"
    Write-Host "   Esperado: $($failed.ExpectedStatus -join ', '), Recibido: $($failed.StatusCode)"
    if ($VerboseOutput -and $failed.Error) {
      Write-Host "   Error: $($failed.Error | ConvertTo-Json -Compress)"
    }
    Write-Host ""
  }
}

# Guardar reporte en archivo
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportPath = "./test-report-$timestamp.json"
$report | ConvertTo-Json -Depth 10 | Set-Content $reportPath
Write-Info "Reporte guardado en: $reportPath"

# Paso 6: Decision de despliegue automatico
Write-Host ""
if ($report.Summary.Failed -eq 0) {
  Write-Pass "TODAS LAS PRUEBAS PASARON"
  Write-Host ""
    
  if ($AutoDeploy) {
    Write-Info "Iniciando despliegue automatico..."
    Write-Warn "   Ejecutando: fix_functionapp_final.ps1"
        
    if (Test-Path "./fix_functionapp_final.ps1") {
      & ./fix_functionapp_final.ps1
    }
    else {
      Write-Fail "   No se encontro fix_functionapp_final.ps1"
    }
  }
  else {
    Write-Info "Todas las pruebas pasaron. Puedes ejecutar el despliegue:"
    Write-Host "   ./fix_functionapp_final.ps1"
    Write-Host ""
    Write-Host "   O ejecuta este script con -AutoDeploy para desplegar automaticamente"
  }
    
  exit 0
}
else {
  Write-Fail "HAY PRUEBAS FALLIDAS"
  Write-Host ""
  Write-Warn "No se puede proceder con el despliegue hasta que todas las pruebas pasen."
  Write-Host ""
  Write-Info "Sugerencias:"
  Write-Host "  1. Revisa los logs de la Function App"
  Write-Host "  2. Verifica que todas las variables de entorno esten configuradas"
  Write-Host "  3. Asegurate de que los servicios de Azure esten activos"
  Write-Host "  4. Ejecuta con -VerboseOutput para mas detalles"
    
  exit 1
}



