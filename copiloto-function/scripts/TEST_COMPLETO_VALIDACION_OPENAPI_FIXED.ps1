param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [string]$OutputFormat = "console",
    [switch]$Verbose
)

# ============ FUNCIONES DE UTILIDAD ============
function Write-Pass {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# ============ GENERADOR DE VALORES DE EJEMPLO ============
function Get-SampleValue {
    param($Schema, $ParamName)
    
    if ($Schema.example) {
        return $Schema.example
    }
    
    if ($Schema.enum) {
        return $Schema.enum[0]
    }
    
    if ($ParamName) {
        $commonValues = @{
            "ruta"         = "README.md"
            "path"         = "package.json"
            "archivo"      = "test.txt"
            "blob"         = "docs/API.md"
            "container"    = "boat-rental-project"
            "contenedor"   = "boat-rental-project"
            "nombre"       = "test-container-$(Get-Random -Maximum 9999)"
            "operacion"    = "agregar_final"
            "contenido"    = "Test content $(Get-Date)"
            "comando"      = "group list"
            "script"       = "test.py"
            "timeout"      = 30
            "publico"      = $false
            "overwrite"    = $true
        }
        
        if ($commonValues.ContainsKey($ParamName)) {
            return $commonValues[$ParamName]
        }
    }
    
    if ($Schema.type) {
        switch ($Schema.type) {
            "string" { return "test-value" }
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
        "/api/ejecutar-cli"            = @{
            comando = "group list"
        }
        "/api/hybrid"                  = @{
            agent_response = "ping"
        }
        "/api/ejecutar"                = @{
            intencion = "dashboard"
            parametros = @{}
        }
    }
    
    if ($specialCases.ContainsKey($Path)) {
        return $specialCases[$Path]
    }
    
    $body = @{}
    
    if ($Schema.properties) {
        foreach ($prop in $Schema.properties.PSObject.Properties) {
            $propName = $prop.Name
            $propSchema = $prop.Value
            
            if (!$Schema.required -or $propName -in $Schema.required) {
                $body[$propName] = Get-SampleValue -Schema $propSchema -ParamName $propName
            }
        }
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

# ============ DEFINICIÓN DE CASOS DE PRUEBA ============
$testCases = @(
    # Endpoints básicos
    @{
        Path = "/api/health"
        Method = "GET"
        ExpectedStatus = @(200)
        Description = "Health check endpoint"
    },
    @{
        Path = "/api/status"
        Method = "GET"
        ExpectedStatus = @(200)
        Description = "Status endpoint"
    },
    
    # Gestión de archivos - casos válidos
    @{
        Path = "/api/leer-archivo"
        Method = "GET"
        QueryParams = @{ ruta = "README.md" }
        ExpectedStatus = @(200, 404)
        Description = "Leer archivo existente"
    },
    @{
        Path = "/api/info-archivo"
        Method = "GET"
        QueryParams = @{ ruta = "package.json" }
        ExpectedStatus = @(200, 404)
        Description = "Información de archivo"
    },
    
    # Gestión de archivos - casos de error (validación)
    @{
        Path = "/api/leer-archivo"
        Method = "GET"
        QueryParams = @{}
        ExpectedStatus = @(400)
        Description = "Leer archivo sin parámetro ruta (debe fallar)"
    },
    @{
        Path = "/api/info-archivo"
        Method = "GET"
        QueryParams = @{}
        ExpectedStatus = @(400)
        Description = "Info archivo sin parámetro ruta (debe fallar)"
    },
    
    # Endpoints POST
    @{
        Path = "/api/escribir-archivo"
        Method = "POST"
        Body = @{
            ruta = "test/nuevo-archivo.txt"
            contenido = "Contenido de prueba"
        }
        ExpectedStatus = @(200, 201, 400)
        Description = "Escribir nuevo archivo"
    },
    @{
        Path = "/api/ejecutar"
        Method = "POST"
        Body = @{
            intencion = "dashboard"
            parametros = @{}
        }
        ExpectedStatus = @(200, 400)
        Description = "Ejecutar comando dashboard"
    },
    @{
        Path = "/api/hybrid"
        Method = "POST"
        Body = @{
            agent_response = "ping"
        }
        ExpectedStatus = @(200, 400)
        Description = "Endpoint hybrid con ping"
    },
    
    # Casos de error para validación
    @{
        Path = "/api/escribir-archivo"
        Method = "POST"
        Body = @{}
        ExpectedStatus = @(400)
        Description = "Escribir archivo sin parámetros (debe fallar)"
    },
    @{
        Path = "/api/ejecutar"
        Method = "POST"
        Body = @{}
        ExpectedStatus = @(400)
        Description = "Ejecutar sin intención (debe fallar)"
    }
)

# ============ PROGRAMA PRINCIPAL ============
Write-Host "🚀 INICIANDO VALIDACIÓN COMPLETA DE OPENAPI" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "Total de casos de prueba: $($testCases.Count)" -ForegroundColor Cyan
Write-Host ""

$results = @()
$passed = 0
$failed = 0

foreach ($testCase in $testCases) {
    Write-Host "Probando: $($testCase.Method) $($testCase.Path)" -ForegroundColor Yellow
    Write-Host "  Descripción: $($testCase.Description)" -ForegroundColor Gray
    
    $result = Invoke-TestCase -BaseUrl $BaseUrl -Path $testCase.Path -Method $testCase.Method -QueryParams $testCase.QueryParams -Body $testCase.Body -ExpectedStatus $testCase.ExpectedStatus
    
    if ($result.Success) {
        Write-Pass "PASS ($($result.StatusCode), $($result.ResponseTime) ms)"
        $passed++
    } else {
        Write-Fail "FAIL (esperado: $($testCase.ExpectedStatus -join ', '), obtenido: $($result.StatusCode))"
        $failed++
        
        if ($Verbose -and $result.ResponseBody) {
            Write-Host "  Respuesta: $($result.ResponseBody | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
        }
    }
    
    $results += @{
        TestCase = $testCase
        Result = $result
    }
    
    Write-Host ""
}

# ============ RESUMEN FINAL ============
Write-Host "===============================================" -ForegroundColor Green
Write-Host "📊 RESUMEN DE VALIDACIÓN" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Total de pruebas: $($testCases.Count)" -ForegroundColor Cyan
Write-Host "Exitosas: $passed" -ForegroundColor Green
Write-Host "Fallidas: $failed" -ForegroundColor Red

$successRate = if ($testCases.Count -gt 0) { [math]::Round(($passed / $testCases.Count) * 100, 2) } else { 0 }
Write-Host "Tasa de éxito: $successRate %" -ForegroundColor $(if ($successRate -ge 80) { "Green" } else { "Yellow" })

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "❌ PRUEBAS FALLIDAS:" -ForegroundColor Red
    $failedTests = $results | Where-Object { -not $_.Result.Success }
    foreach ($failedTest in $failedTests) {
        Write-Host "  • $($failedTest.TestCase.Method) $($failedTest.TestCase.Path) - Status: $($failedTest.Result.StatusCode)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Validación completada" -ForegroundColor Green

# Generar reporte JSON si se solicita
if ($OutputFormat -eq "json") {
    $reportPath = "./test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    $report = @{
        Summary = @{
            TotalTests = $testCases.Count
            Passed = $passed
            Failed = $failed
            SuccessRate = $successRate
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        Results = $results
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "📄 Reporte guardado en: $reportPath" -ForegroundColor Cyan
}