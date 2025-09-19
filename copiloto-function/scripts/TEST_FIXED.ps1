# TEST_COMPLETO_VALIDACION_OPENAPI.ps1
# Script de validaciÃ³n completa que simula comportamiento del agente AI

param(
  [string]$BaseUrl = "http://localhost:7071",  # Para ngrok cambiar a tu URL
  [string]$OpenApiPath = "./openapi_copiloto_local.yaml",
  [switch]$StopOnFirstFail,
  [switch]$VerboseOutput,
  [switch]$AutoDeploy  # Si pasa todo, ejecuta fix_functionapp_final.ps1
)

# ============ CONFIGURACIÃ“N ============
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Colores para output
function Write-Pass { Write-Host $args -ForegroundColor Green }
function Write-Fail { Write-Host $args -ForegroundColor Red }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Debug { if ($VerboseOutput) { Write-Host $args -ForegroundColor Gray } }

# ============ PARSER OPENAPI ============
function Get-OpenApiObject {
  param([string]$Path)
    
  Write-Info "ðŸ“– Parseando OpenAPI desde: $Path"
    
  # Intentar parsear como YAML o JSON
  $content = Get-Content $Path -Raw
    
  try {
    # Primero intentar como JSON
    $spec = $content | ConvertFrom-Json
    Write-Debug "✓ Parseado como JSON"
  }
  catch {
    # Si falla, intentar como YAML (requiere mÃ³dulo powershell-yaml)
    $yamlParseSuccess = $false
    try {
      if (!(Get-Module -ListAvailable -Name powershell-yaml)) {
        Write-Warn "Instalando mÃ³dulo powershell-yaml..."
        Install-Module -Name powershell-yaml -Force -Scope CurrentUser
      }
      Import-Module powershell-yaml
      $spec = ConvertFrom-Yaml $content
      Write-Debug "✓ Parseado como YAML"
      $yamlParseSuccess = $true
    }
    catch {
      Write-Debug "Error parseando YAML: $_"
    }
    
    # Si YAML tambiÃ©n falla, intentar parsear JSON embebido
    if (-not $yamlParseSuccess) {
      Write-Debug "Intentando parsear JSON embebido..."
      $jsonMatch = [regex]::Match($content, '(?s)\{.*\}')
      if ($jsonMatch.Success) {
        $spec = $jsonMatch.Value | ConvertFrom-Json
        Write-Debug "✓ Parseado JSON embebido"
      }
      else {
        throw "No se pudo parsear el OpenAPI"
      }
    }
  }
    
  return $spec
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
                
        # Generar escenarios de prueba basados en el esquema
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
    
  # Escenario 1: Llamada vÃ¡lida con parÃ¡metros mÃ­nimos requeridos
  $validScenario = @{
    Name           = "Valid_MinimalRequired"
    Description    = "Llamada con parÃ¡metros mÃ­nimos requeridos"
    ExpectedStatus = @(200, 201)
    Body           = $null
    QueryParams    = @{}
  }
    
  # Analizar parÃ¡metros requeridos
  if ($Operation.parameters) {
    foreach ($param in $Operation.parameters) {
      if ($param.required) {
        $validScenario.QueryParams[$param.name] = Get-SampleValue -Schema $param.schema -ParamName $param.name
      }
    }
  }
    
  # Analizar request body requerido
  if ($Operation.requestBody -and $Operation.requestBody.required) {
    $content = $Operation.requestBody.content.'application/json'
    if ($content -and $content.schema) {
      $validScenario.Body = New-SampleBody -Schema $content.schema -Path $Path
    }
  }
    
  $scenarios += $validScenario
    
  # Escenario 2: Llamada sin parÃ¡metros requeridos (debe fallar)
  if ($Operation.parameters -or $Operation.requestBody) {
    $invalidScenario = @{
      Name           = "Invalid_MissingRequired"
      Description    = "Llamada sin parÃ¡metros requeridos"
      ExpectedStatus = @(400, 422)
      Body           = @{}
      QueryParams    = @{}
    }
    $scenarios += $invalidScenario
  }
    
  # Escenario 3: Llamada con parÃ¡metros invÃ¡lidos
  if ($Method -eq "POST" -or $Method -eq "PUT") {
    $malformedScenario = @{
      Name           = "Invalid_MalformedBody"
      Description    = "Llamada con body malformado"
      ExpectedStatus = @(400, 422)
      Body           = "invalid json {["
      QueryParams    = @{}
    }
    $scenarios += $malformedScenario
  }
    
  return $scenarios
}

# ============ GENERADOR DE VALORES DE EJEMPLO ============
function Get-SampleValue {
  param($Schema, $ParamName)
    
  # Valores especÃ­ficos por nombre de parÃ¡metro
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
    
  # Valores por tipo de esquema
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
    
  $body = @{}
    
  # Casos especiales por endpoint
  $specialCases = @{
    "/api/crear-contenedor"  = @{
      nombre   = "test-container-$(Get-Random -Maximum 9999)"
      publico  = $false
      metadata = @{ created_by = "test" }
    }
    "/api/escribir-archivo"  = @{
      ruta      = "test/file_$(Get-Random -Maximum 9999).txt"
      contenido = "Test content $(Get-Date)"
    }
    "/api/modificar-archivo" = @{
      ruta      = "test/existing.txt"
      operacion = "agregar_final"
      contenido = "New line"
    }
    "/api/ejecutar-cli"      = @{
      comando = "group list"
    }
    "/api/ejecutar-script"   = @{
      script    = "scripts/test.py"
      args      = @()
      timeout_s = 30
    }
    "/api/hybrid"            = @{
      agent_response = "ping"
    }
    "/api/deploy"            = @{
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
    
  # Generar body basado en esquema
  if ($Schema.properties) {
    foreach ($prop in $Schema.properties.PSObject.Properties) {
      $propName = $prop.Name
      $propSchema = $prop.Value
            
      # Si es requerido o no hay lista de requeridos, incluirlo
      if (!$Schema.required -or $propName -in $Schema.required) {
        $body[$propName] = Get-SampleValue -Schema $propSchema -ParamName $propName
      }
    }
  }
  elseif ($Schema.oneOf -or $Schema.anyOf) {
    # Tomar el primer esquema de oneOf/anyOf
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
    
  # Agregar query parameters
  if ($QueryParams -and $QueryParams.Count -gt 0) {
    $queryString = ($QueryParams.GetEnumerator() | ForEach-Object {
        "$($_.Key)=$([uri]::EscapeDataString($_.Value))"
      }) -join "&"
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

# ============ VALIDADOR DE RESPUESTA ============
function Test-Response {
  param(
    $Response,
    $ExpectedSchema,
    $OperationId
  )
    
  $validationErrors = @()
    
  # Validar status code
  if ($ExpectedSchema) {
    $statusKey = $Response.StatusCode.ToString()
    if (!$ExpectedSchema.PSObject.Properties[$statusKey]) {
      $validationErrors += "Status code $($Response.StatusCode) no estÃ¡ documentado en OpenAPI"
    }
    else {
      $expectedResponse = $ExpectedSchema.$statusKey
            
      # Validar schema de respuesta si existe
      if ($expectedResponse.content -and $expectedResponse.content.'application/json') {
        $responseSchema = $expectedResponse.content.'application/json'.schema
                
        if ($responseSchema) {
          $schemaErrors = Test-Schema -Data $Response.ResponseBody -Schema $responseSchema -Path "response"
          $validationErrors += $schemaErrors
        }
      }
    }
  }
    
  # Validaciones especÃ­ficas por operaciÃ³n
  $specificValidations = @{
    "leerArchivo" = {
      param($resp)
      $errors = @()
      if ($resp.StatusCode -eq 200) {
        # Debe tener estructura especÃ­fica
        if (!$resp.ResponseBody.ok -and !$resp.ResponseBody.archivo) {
          $errors += "Respuesta exitosa debe tener 'ok' o estructura 'archivo'"
        }
      }
      return $errors
    }
    "ejecutarCLI" = {
      param($resp)
      $errors = @()
      if ($resp.StatusCode -eq 200) {
        if (!$resp.ResponseBody.exito -and !$resp.ResponseBody.stdout) {
          $errors += "Respuesta debe tener 'exito' o 'stdout'"
        }
      }
      return $errors
    }
  }
    
  if ($specificValidations.ContainsKey($OperationId)) {
    $customErrors = & $specificValidations[$OperationId] $Response
    $validationErrors += $customErrors
  }
    
  return $validationErrors
}

# ============ VALIDADOR DE ESQUEMA ============
function Test-Schema {
  param(
    $Data,
    $Schema,
    [string]$Path = "root"
  )
    
  $errors = @()
    
  if (!$Schema) { return $errors }
    
  # Validar tipo
  if ($Schema.type) {
    $actualType = Get-JsonType -Value $Data
    $expectedType = $Schema.type
        
    if ($expectedType -ne $actualType -and $actualType -ne "null") {
      $errors += "[$Path] Tipo esperado: $expectedType, recibido: $actualType"
    }
  }
    
  # Validar propiedades requeridas
  if ($Schema.required -and $Data -is [PSCustomObject]) {
    foreach ($reqProp in $Schema.required) {
      if (!$Data.PSObject.Properties[$reqProp]) {
        $errors += "[$Path] Propiedad requerida faltante: $reqProp"
      }
    }
  }
    
  # Validar propiedades del objeto
  if ($Schema.properties -and $Data -is [PSCustomObject]) {
    foreach ($prop in $Schema.properties.PSObject.Properties) {
      $propName = $prop.Name
      $propSchema = $prop.Value
            
      if ($Data.PSObject.Properties[$propName]) {
        $propErrors = Test-Schema -Data $Data.$propName -Schema $propSchema -Path "$Path.$propName"
        $errors += $propErrors
      }
    }
  }
    
  # Validar items del array
  if ($Schema.items -and $Data -is [array]) {
    for ($i = 0; $i -lt $Data.Length; $i++) {
      $itemErrors = Test-Schema -Data $Data[$i] -Schema $Schema.items -Path "$Path[$i]"
      $errors += $itemErrors
    }
  }
    
  return $errors
}

# ============ HELPER: OBTENER TIPO JSON ============
function Get-JsonType {
  param($Value)
    
  if ($null -eq $Value) { return "null" }
  if ($Value -is [bool]) { return "boolean" }
  if ($Value -is [int] -or $Value -is [long]) { return "integer" }
  if ($Value -is [double] -or $Value -is [decimal]) { return "number" }
  if ($Value -is [string]) { return "string" }
  if ($Value -is [array]) { return "array" }
  if ($Value -is [PSCustomObject] -or $Value -is [hashtable]) { return "object" }
    
  return "unknown"
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
    
  # Agrupar por tag
  $tags = $Results | ForEach-Object { $_.Tags } | Select-Object -Unique
  foreach ($tag in $tags) {
    if ($tag) {
      $tagTests = $Results | Where-Object { $tag -in $_.Tags }
      $tagPassed = ($tagTests | Where-Object { $_.TestResult.Success }).Count
      $report.ByTag[$tag] = @{
        Total  = $tagTests.Count
        Passed = $tagPassed
        Failed = $tagTests.Count - $tagPassed
      }
    }
  }
    
  # Agrupar por mÃ©todo
  $methods = $Results | Select-Object -ExpandProperty Method -Unique
  foreach ($method in $methods) {
    $methodTests = $Results | Where-Object { $_.Method -eq $method }
    $methodPassed = ($methodTests | Where-Object { $_.TestResult.Success }).Count
    $report.ByMethod[$method] = @{
      Total  = $methodTests.Count
      Passed = $methodPassed
      Failed = $methodTests.Count - $methodPassed
    }
  }
    
  # Detallar tests fallidos
  $failedResults = $Results | Where-Object { -not $_.TestResult.Success }
  foreach ($failed in $failedResults) {
    $report.FailedTests += @{
      Path           = $failed.Path
      Method         = $failed.Method
      OperationId    = $failed.OperationId
      Scenario       = $failed.ScenarioName
      StatusCode     = $failed.TestResult.StatusCode
      ExpectedStatus = $failed.ExpectedStatus
      ResponseTime   = $failed.TestResult.ResponseTime
      Error          = $failed.TestResult.ResponseBody
    }
  }
    
  # Detallar errores de validaciÃ³n
  $validationResults = $Results | Where-Object { $_.ValidationErrors.Count -gt 0 }
  foreach ($validation in $validationResults) {
    $report.ValidationErrors += @{
      Path        = $validation.Path
      Method      = $validation.Method
      OperationId = $validation.OperationId
      Errors      = $validation.ValidationErrors
    }
  }
    
  return $report
}

# ============ PROGRAMA PRINCIPAL ============
Write-Host "`n" -NoNewline
Write-Info "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"
Write-Info "â•‘     VALIDADOR COMPLETO DE OPENAPI PARA FUNCTION APP      â•‘"
Write-Info "â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
Write-Host ""

# Paso 1: Parsear OpenAPI
try {
  $openApiSpec = Get-OpenApiObject -Path $OpenApiPath
  Write-Pass "✓ OpenAPI parseado correctamente"
  Write-Info "  TÃ­tulo: $($openApiSpec.info.title)"
  Write-Info "  VersiÃ³n: $($openApiSpec.info.version)"
  Write-Host ""
}
catch {
  Write-Fail "âœ— Error parseando OpenAPI: $_"
  exit 1
}

# Paso 2: Generar casos de prueba
Write-Info "ðŸ”§ Generando casos de prueba desde OpenAPI..."
$testCases = New-TestCases -OpenApiSpec $openApiSpec
Write-Pass "✓ Generados $($testCases.Count) endpoints para probar"

$totalScenarios = ($testCases | ForEach-Object { $_.TestScenarios.Count } | Measure-Object -Sum).Sum
Write-Info "  Total de escenarios: $totalScenarios"
Write-Host ""

# Paso 3: Verificar conectividad
Write-Info "ðŸ”Œ Verificando conectividad con $BaseUrl..."
try {
  $null = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
  Write-Pass "✓ Servidor respondiendo correctamente"
  Write-Host ""
}
catch {
  Write-Fail "âœ— No se puede conectar con $BaseUrl"
  Write-Warn "  AsegÃºrate de que 'func start' estÃ© ejecutÃ¡ndose"
  exit 1
}

# Paso 4: Ejecutar pruebas
Write-Info "ðŸš€ Ejecutando pruebas..."
Write-Host ""

$allResults = @()
$testNumber = 0
$totalTests = $totalScenarios

foreach ($testCase in $testCases) {
  foreach ($scenario in $testCase.TestScenarios) {
    $testNumber++
        
    Write-Host -NoNewline "[$testNumber/$totalTests] "
    $progressPercent = [math]::Round(($testNumber / $totalTests) * 100, 1)
    Write-Host -NoNewline "[$testNumber/$totalTests] ($progressPercent%) $($testCase.Method) $($testCase.Path) "
    Write-Host -NoNewline "($($scenario.Name)) ... "
        
    # Ejecutar test
    $result = Invoke-TestCase `
      -BaseUrl $BaseUrl `
      -Path $testCase.Path `
      -Method $testCase.Method `
      -QueryParams $scenario.QueryParams `
      -Body $scenario.Body `
      -ExpectedStatus $scenario.ExpectedStatus `
      -TimeoutSec 30
        
    # Validar respuesta contra esquema
    $validationErrors = @()
    if ($result.Success -and $testCase.Responses) {
      $validationErrors = Test-Response `
        -Response $result `
        -ExpectedSchema $testCase.Responses `
        -OperationId $testCase.OperationId
    }
        
    # Guardar resultado
    $testResult = @{
      Path                = $testCase.Path
      Method              = $testCase.Method
      OperationId         = $testCase.OperationId
      Summary             = $testCase.Summary
      Tags                = $testCase.Tags
      ScenarioName        = $scenario.Name
      ScenarioDescription = $scenario.Description
      ExpectedStatus      = $scenario.ExpectedStatus
      TestResult          = $result
      ValidationErrors    = $validationErrors
    }
        
    $allResults += $testResult
        
    # Mostrar resultado
    if ($result.Success -and $validationErrors.Count -eq 0) {
      Write-Pass "✓ PASS ($($result.StatusCode), $($result.ResponseTime)ms)"
    }
    elseif ($result.Success -and $validationErrors.Count -gt 0) {
      Write-Warn "âš  PASS con advertencias ($($result.StatusCode), $($validationErrors.Count) errores de validaciÃ³n)"
      if ($VerboseOutput) {
        foreach ($err in $validationErrors) {
          Write-Warn "    - $err"
        }
      }
    }
    else {
      Write-Fail "âœ— FAIL (esperado: $($scenario.ExpectedStatus -join ','), recibido: $($result.StatusCode))"
      if ($VerboseOutput -and $result.ResponseBody) {
        Write-Debug "    Response: $($result.ResponseBody | ConvertTo-Json -Compress)"
      }
            
      if ($StopOnFirstFail) {
        Write-Host ""
        Write-Fail "Deteniendo en el primer fallo (usar -StopOnFirstFail:$false para continuar)"
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
Write-Info "ðŸ“Š Generando reporte de pruebas..."
$report = New-TestReport -Results $allResults

# Mostrar resumen
Write-Host ""
Write-Info "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
Write-Info "                RESUMEN DE PRUEBAS          "
Write-Info "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
Write-Host ""

Write-Host "Total de pruebas:    $($report.Summary.TotalTests)"
Write-Pass "Pruebas exitosas:    $($report.Summary.Passed)"
if ($report.Summary.Failed -gt 0) {
  Write-Fail "Pruebas fallidas:    $($report.Summary.Failed)"
}
else {
  Write-Host "Pruebas fallidas:    0"
}
Write-Host "Tasa de Ã©xito:       $($report.Summary.SuccessRate)%"
Write-Host ""

# Resumen por tag
if ($report.ByTag.Count -gt 0) {
  Write-Info "Por categorÃ­a (Tags):"
  foreach ($tag in $report.ByTag.Keys | Sort-Object) {
    $tagData = $report.ByTag[$tag]
    $tagSuccess = if ($tagData.Total -gt 0) { [math]::Round(($tagData.Passed / $tagData.Total) * 100, 0) } else { 0 }
    Write-Host "  $tag : $($tagData.Passed)/$($tagData.Total) ($tagSuccess%)"
  }
  Write-Host ""
}

# Resumen por mÃ©todo
Write-Info "Por mÃ©todo HTTP:"
foreach ($method in $report.ByMethod.Keys | Sort-Object) {
  $methodData = $report.ByMethod[$method]
  $methodSuccess = if ($methodData.Total -gt 0) { [math]::Round(($methodData.Passed / $methodData.Total) * 100, 0) } else { 0 }
  Write-Host "  $method : $($methodData.Passed)/$($methodData.Total) ($methodSuccess%)"
}
Write-Host ""

# Mostrar tests fallidos
if ($report.FailedTests.Count -gt 0) {
  Write-Fail "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Fail "           PRUEBAS FALLIDAS                 "
  Write-Fail "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Host ""
    
  foreach ($failed in $report.FailedTests) {
    Write-Fail "âŒ $($failed.Method) $($failed.Path)"
    Write-Host "   Escenario: $($failed.Scenario)"
    Write-Host "   Esperado: $($failed.ExpectedStatus -join ', '), Recibido: $($failed.StatusCode)"
    if ($VerboseOutput -and $failed.Error) {
      Write-Host "   Error: $($failed.Error | ConvertTo-Json -Compress)"
    }
    Write-Host ""
  }
}

# Mostrar errores de validaciÃ³n
if ($report.ValidationErrors.Count -gt 0) {
  Write-Warn "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Warn "      ERRORES DE VALIDACIÃ“N DE ESQUEMA     "
  Write-Warn "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Host ""
    
  foreach ($validation in $report.ValidationErrors) {
    Write-Warn "âš  $($validation.Method) $($validation.Path)"
    foreach ($err in $validation.Errors) {
      Write-Host "   - $err"
    }
    Write-Host ""
  }
}

# Guardar reporte en archivo
$reportPath = "./test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$report | ConvertTo-Json -Depth 10 | Set-Content $reportPath
Write-Info "ðŸ“ Reporte guardado en: $reportPath"

# Paso 6: DecisiÃ³n de despliegue automÃ¡tico
Write-Host ""
if ($report.Summary.Failed -eq 0 -and $report.ValidationErrors.Count -eq 0) {
  Write-Pass "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Pass "     âœ… TODAS LAS PRUEBAS PASARON âœ…       "
  Write-Pass "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Host ""
    
  if ($AutoDeploy) {
    Write-Info "ðŸš€ Iniciando despliegue automÃ¡tico..."
    Write-Warn "   Ejecutando: fix_functionapp_final.ps1"
        
    if (Test-Path "./fix_functionapp_final.ps1") {
      & ./fix_functionapp_final.ps1
    }
    else {
      Write-Fail "   No se encontrÃ³ fix_functionapp_final.ps1"
    }
  }
  else {
    Write-Info "ðŸ’¡ Todas las pruebas pasaron. Puedes ejecutar el despliegue:"
    Write-Host "   ./fix_functionapp_final.ps1"
    Write-Host ""
    Write-Host "   O ejecuta este script con -AutoDeploy para desplegar automÃ¡ticamente"
  }
    
  exit 0
}
else {
  Write-Fail "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Fail "     âŒ HAY PRUEBAS FALLIDAS âŒ            "
  Write-Fail "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
  Write-Host ""
  Write-Warn "No se puede proceder con el despliegue hasta que todas las pruebas pasen."
  Write-Host ""
  Write-Info "Sugerencias:"
  Write-Host "  1. Revisa los logs de la Function App"
  Write-Host "  2. Verifica que todas las variables de entorno estÃ©n configuradas"
  Write-Host "  3. AsegÃºrate de que los servicios de Azure estÃ©n activos"
  Write-Host "  4. Ejecuta con -VerboseOutput para mÃ¡s detalles"
    
  exit 1
}
