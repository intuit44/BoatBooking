# invoke-orchestrator.ps1
# Sistema completo de comunicación entre AI Foundry, Copiloto y Agentes
# Versión 3.0 - Comunicación Bidireccional Real

param(
  [Parameter(Position = 0)]
  [string]$Action = "test",
  [Parameter()]
  [string]$Message = "",
  [Parameter()]
  [string]$Agent = "Architect_BoatRental",
  [Parameter()]
  [switch]$EnableDebug,
  [switch]$Setup,
  [switch]$TestAll
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============= CONFIGURACIÓN GLOBAL =============
$Global:Config = @{
  # Azure Resources
  FunctionApp     = "copiloto-semantico-func"
  ResourceGroup   = "boat-rental-app-group"
  KeyVault        = "boatrental-kv-prod"
  LogicApp        = "invocar-copiloto"
    
  # Endpoints
  LogicAppUrl     = "https://prod-15.eastus.logic.azure.com:443/workflows/4711b810bb5f478aa4d8dc5662c61c53/triggers/When_a_HTTP_request_is_received/paths/invoke"
  LogicAppParams  = "?api-version=2019-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=IUqo-n0TnqdRiQF7qSGSBnofI5LZPmuzdYHCdmsahss"
    
  # AI Foundry
  FoundryEndpoint = "https://boatRentalFoundry-dev.services.ai.azure.com"
  FoundryProject  = "booking-agents"
    
  # Paths
  ProjectRoot     = "C:\ProyectosSimbolicos\boat-rental-app"
  CopilotoPath    = "C:\ProyectosSimbolicos\boat-rental-app\copiloto-function"
}

# ============= FUNCIONES HELPER =============

function Write-Status {
  param($Message, $Type = "Info")
  $colors = @{
    "Info"    = "Cyan"
    "Success" = "Green"
    "Warning" = "Yellow"
    "Error"   = "Red"
    "Debug"   = "Gray"
  }
  $icons = @{
    "Info"    = "ℹ️"
    "Success" = "✅"
    "Warning" = "⚠️"
    "Error"   = "❌"
    "Debug"   = "🔍"
  }
  Write-Host "$($icons[$Type]) $Message" -ForegroundColor $colors[$Type]
}

function Get-MasterKey {
  try {
    $key = az functionapp keys list `
      -n $Global:Config.FunctionApp `
      -g $Global:Config.ResourceGroup `
      --query masterKey -o tsv
    return $key.Trim()
  }
  catch {
    Write-Status "Error obteniendo MasterKey: $_" "Error"
    return $null
  }
}

# ============= COMUNICACIÓN DIRECTA CON COPILOTO =============

function Invoke-CopilotoDirect {
  param(
    [string]$Endpoint = "status",
    [string]$Method = "GET",
    [hashtable]$Body = @{},
    [string]$Mensaje = ""
  )
    
  Write-Status "Invocando Copiloto directamente: $Endpoint" "Info"
    
  $masterKey = Get-MasterKey
  if (-not $masterKey) {
    Write-Status "No se pudo obtener la MasterKey" "Error"
    return $null
  }
    
  $headers = @{
    "x-functions-key" = $masterKey
    "Content-Type"    = "application/json"
  }
    
  $baseUrl = "https://$($Global:Config.FunctionApp).azurewebsites.net/api"
    
  try {
    switch ($Endpoint) {
      "health" {
        $uri = "$baseUrl/health"
        $response = Invoke-RestMethod -Uri $uri -Method GET
      }
      "status" {
        $uri = "$baseUrl/status"
        $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers
      }
      "copiloto" {
        $uri = "$baseUrl/copiloto"
        if ($Mensaje) { $uri += "?mensaje=$([System.Uri]::EscapeDataString($Mensaje))" }
        $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers
      }
      "ejecutar" {
        $uri = "$baseUrl/ejecutar"
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10)
      }
      "invocar" {
        $uri = "$baseUrl/invocar"
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10)
      }
      default {
        throw "Endpoint no reconocido: $Endpoint"
      }
    }
        
    Write-Status "Respuesta recibida exitosamente" "Success"
    return $response
  }
  catch {
    Write-Status "Error en invocación: $_" "Error"
    return $null
  }
}

# ============= COMUNICACIÓN VIA LOGIC APP =============

function Invoke-ViaLogicApp {
  param(
    [hashtable]$Command
  )
    
  Write-Status "Invocando via Logic App" "Info"
    
  $uri = $Global:Config.LogicAppUrl + $Global:Config.LogicAppParams
    
  try {
    $response = Invoke-RestMethod `
      -Uri $uri `
      -Method POST `
      -ContentType "application/json" `
      -Body ($Command | ConvertTo-Json -Depth 10)
        
    Write-Status "Respuesta de Logic App recibida" "Success"
    return $response
  }
  catch {
    Write-Status "Error con Logic App: $_" "Error"
    return $null
  }
}

# ============= SIMULACIÓN DE ARCHITECT_BOATRENTAL =============

function Invoke-ArchitectAgent {
  param(
    [string]$UserIntent
  )
    
  Write-Status "Procesando intención con Architect_BoatRental: $UserIntent" "Info"
    
  # Mapeo de intenciones (simula lo que haría el GPT)
  $intentMap = @{
    "estado del sistema"       = @{
      endpoint = "status"
      method   = "GET"
    }
    "muéstrame el dashboard"   = @{
      endpoint  = "ejecutar"
      method    = "POST"
      intencion = "dashboard"
      modo      = "normal"
    }
    "diagnóstico completo"     = @{
      endpoint   = "ejecutar"
      method     = "POST"
      intencion  = "diagnosticar:completo"
      parametros = @{ incluir_logs = $true }
    }
    "lee function_app.py"      = @{
      endpoint = "copiloto"
      method   = "GET"
      mensaje  = "leer:function_app.py"
    }
    "busca archivos python"    = @{
      endpoint = "copiloto"
      method   = "GET"
      mensaje  = "buscar:*.py"
    }
    "lista las function apps"  = @{
      endpoint   = "ejecutar"
      method     = "POST"
      intencion  = "ejecutar:azure"
      parametros = @{
        comando = "az functionapp list --resource-group boat-rental-app-group"
      }
    }
    "ayúdame con blob storage" = @{
      endpoint  = "ejecutar"
      method    = "POST"
      intencion = "guia:configurar_blob"
      modo      = "guiado"
    }
    "despliega el proyecto"    = @{
      endpoint  = "ejecutar"
      method    = "POST"
      intencion = "orquestar:deployment"
      modo      = "orquestador"
    }
  }
    
  # Buscar coincidencia
  $command = $null
  foreach ($key in $intentMap.Keys) {
    if ($UserIntent -like "*$key*") {
      $command = $intentMap[$key]
      break
    }
  }
    
  if (-not $command) {
    # Intención no mapeada - intentar interpretación básica
    if ($UserIntent -match "lee|leer|archivo") {
      $command = @{
        endpoint = "copiloto"
        method   = "GET"
        mensaje  = "buscar:archivo"
      }
    }
    elseif ($UserIntent -match "busca|buscar") {
      $command = @{
        endpoint = "copiloto"
        method   = "GET"
        mensaje  = "buscar:*"
      }
    }
    else {
      $command = @{
        endpoint   = "ejecutar"
        method     = "POST"
        intencion  = "sugerir"
        parametros = @{ consulta = $UserIntent }
      }
    }
  }
    
  Write-Status "Comando generado:" "Debug"
  if ($EnableDebug) {
    $command | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
  }
    
  return $command
}

# ============= INVOCACIÓN COMPLETA END-TO-END =============

function Invoke-FullPipeline {
  param(
    [string]$UserMessage,
    [switch]$UseLogicApp
  )
    
  Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
  Write-Status "PIPELINE COMPLETO: $UserMessage" "Info"
  Write-Host ("=" * 60) -ForegroundColor Cyan
    
  # Paso 1: Procesar con Architect
  $command = Invoke-ArchitectAgent -UserIntent $UserMessage
    
  if (-not $command) {
    Write-Status "No se pudo generar comando" "Error"
    return
  }
    
  # Paso 2: Ejecutar comando
  $response = $null
    
  if ($UseLogicApp) {
    # Via Logic App
    $response = Invoke-ViaLogicApp -Command $command
  }
  else {
    # Directo al Function App
    switch ($command.endpoint) {
      "copiloto" {
        $response = Invoke-CopilotoDirect -Endpoint "copiloto" -Mensaje $command.mensaje
      }
      "ejecutar" {
        $body = @{
          intencion  = $command.intencion
          parametros = $command.parametros
          modo       = $command.modo
        }
        $response = Invoke-CopilotoDirect -Endpoint "ejecutar" -Method "POST" -Body $body
      }
      "status" {
        $response = Invoke-CopilotoDirect -Endpoint "status"
      }
      "health" {
        $response = Invoke-CopilotoDirect -Endpoint "health"
      }
      default {
        $body = $command
        $response = Invoke-CopilotoDirect -Endpoint "invocar" -Method "POST" -Body $body
      }
    }
  }
    
  # Paso 3: Mostrar respuesta
  if ($response) {
    Write-Host "`n📋 RESPUESTA:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor White
        
    # Procesar próximas acciones si existen
    if ($response.proximas_acciones) {
      Write-Host "`n💡 PRÓXIMAS ACCIONES SUGERIDAS:" -ForegroundColor Yellow
      $response.proximas_acciones | ForEach-Object {
        Write-Host "  • $_" -ForegroundColor Yellow
      }
    }
  }
  else {
    Write-Status "No se recibió respuesta" "Warning"
  }
    
  return $response
}

# ============= SETUP Y VERIFICACIÓN =============

function Test-Setup {
  Write-Host "`n🔧 VERIFICACIÓN DEL SISTEMA" -ForegroundColor Cyan
  Write-Host ("=" * 60) -ForegroundColor Cyan
    
  $checks = @()
    
  # 1. Verificar Azure CLI
  Write-Status "Verificando Azure CLI..." "Info"
  $azAccount = az account show --query id -o tsv 2>$null
  if ($azAccount) {
    $checks += @{ Component = "Azure CLI"; Status = "OK"; Details = "Sesión activa" }
    Write-Status "Azure CLI OK" "Success"
  }
  else {
    $checks += @{ Component = "Azure CLI"; Status = "ERROR"; Details = "No hay sesión" }
    Write-Status "Azure CLI sin sesión" "Error"
  }
    
  # 2. Verificar Function App
  Write-Status "Verificando Function App..." "Info"
  $health = Invoke-CopilotoDirect -Endpoint "health"
  if ($health.status -eq "healthy") {
    $checks += @{ Component = "Function App"; Status = "OK"; Details = $health.version }
    Write-Status "Function App OK" "Success"
  }
  else {
    $checks += @{ Component = "Function App"; Status = "ERROR"; Details = "No responde" }
    Write-Status "Function App no responde" "Error"
  }
    
  # 3. Verificar Logic App
  Write-Status "Verificando Logic App..." "Info"
  $testCommand = @{ endpoint = "health"; method = "GET" }
  $logicResponse = Invoke-ViaLogicApp -Command $testCommand
  if ($logicResponse) {
    $checks += @{ Component = "Logic App"; Status = "OK"; Details = "Responde" }
    Write-Status "Logic App OK" "Success"
  }
  else {
    $checks += @{ Component = "Logic App"; Status = "WARNING"; Details = "No verificado" }
    Write-Status "Logic App no verificado" "Warning"
  }
    
  # 4. Verificar Key Vault
  Write-Status "Verificando Key Vault..." "Info"
  $kvSecret = az keyvault secret show `
    --vault-name $Global:Config.KeyVault `
    --name CopilotoMasterKey `
    --query value -o tsv 2>$null
    
  if ($kvSecret) {
    $funcKey = Get-MasterKey
    if ($kvSecret -eq $funcKey) {
      $checks += @{ Component = "Key Vault"; Status = "OK"; Details = "Sincronizado" }
      Write-Status "Key Vault sincronizado" "Success"
    }
    else {
      $checks += @{ Component = "Key Vault"; Status = "WARNING"; Details = "Desincronizado" }
      Write-Status "Key Vault desincronizado - ejecuta Setup para corregir" "Warning"
    }
  }
  else {
    $checks += @{ Component = "Key Vault"; Status = "ERROR"; Details = "No accesible" }
    Write-Status "Key Vault no accesible" "Error"
  }
    
  # Mostrar resumen
  Write-Host "`n📊 RESUMEN DE VERIFICACIÓN:" -ForegroundColor Cyan
  $checks | Format-Table -AutoSize
    
  return $checks
}

function Initialize-Setup {
  Write-Host "`n🚀 CONFIGURACIÓN INICIAL" -ForegroundColor Cyan
  Write-Host ("=" * 60) -ForegroundColor Cyan
    
  # 1. Sincronizar Key Vault
  Write-Status "Sincronizando Key Vault con Function App..." "Info"
  $funcKey = Get-MasterKey
  if ($funcKey) {
    az keyvault secret set `
      --vault-name $Global:Config.KeyVault `
      --name CopilotoMasterKey `
      --value $funcKey `
      --output none
    Write-Status "Key Vault sincronizado" "Success"
  }
    
  # 2. Verificar Logic App
  Write-Status "Verificando configuración de Logic App..." "Info"
  # Aquí podrías agregar verificación/actualización de Logic App si es necesario
    
  Write-Status "Setup completado" "Success"
}

# ============= PRUEBAS END-TO-END =============

function Test-AllScenarios {
  Write-Host "`n🧪 EJECUTANDO PRUEBAS COMPLETAS" -ForegroundColor Cyan
  Write-Host ("=" * 60) -ForegroundColor Cyan
    
  $scenarios = @(
    "estado del sistema"
    "muéstrame el dashboard"
    "lee function_app.py"
    "busca archivos python"
    "ayúdame con blob storage"
    "diagnóstico completo"
  )
    
  $results = @()
    
  foreach ($scenario in $scenarios) {
    Write-Host "`n📝 Escenario: $scenario" -ForegroundColor Yellow
        
    try {
      $response = Invoke-FullPipeline -UserMessage $scenario
      if ($response) {
        $results += @{
          Scenario     = $scenario
          Status       = "✅ OK"
          ResponseType = $response.GetType().Name
        }
      }
      else {
        $results += @{
          Scenario     = $scenario
          Status       = "⚠️ Sin respuesta"
          ResponseType = "null"
        }
      }
    }
    catch {
      $results += @{
        Scenario     = $scenario
        Status       = "❌ Error"
        ResponseType = $_.Exception.Message
      }
    }
        
    Start-Sleep -Seconds 1  # Evitar rate limiting
  }
    
  Write-Host "`n📊 RESULTADOS DE PRUEBAS:" -ForegroundColor Cyan
  $results | Format-Table -AutoSize
}

# ============= FUNCIÓN PRINCIPAL =============

function Main {
  Write-Host @"
╔══════════════════════════════════════════════════════════╗
║     🤖 ORQUESTADOR DE COMUNICACIÓN COPILOTO-FOUNDRY     ║
║                    Versión 3.0                           ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

  switch ($Action) {
    "setup" {
      Initialize-Setup
      Test-Setup
    }
        
    "test" {
      if ($Message) {
        Invoke-FullPipeline -UserMessage $Message
      }
      else {
        Test-Setup
      }
    }
        
    "test-all" {
      Test-Setup
      Test-AllScenarios
    }
        
    "direct" {
      if (-not $Message) { $Message = "estado del sistema" }
      Invoke-FullPipeline -UserMessage $Message
    }
        
    "logic" {
      if (-not $Message) { $Message = "estado del sistema" }
      Invoke-FullPipeline -UserMessage $Message -UseLogicApp
    }
        
    "health" {
      Invoke-CopilotoDirect -Endpoint "health"
    }
        
    "status" {
      Invoke-CopilotoDirect -Endpoint "status"
    }
        
    "dashboard" {
      $body = @{
        intencion  = "dashboard"
        parametros = @{}
        modo       = "normal"
      }
      Invoke-CopilotoDirect -Endpoint "ejecutar" -Method "POST" -Body $body
    }
        
    default {
      Write-Host @"
            
USO:
    .\invoke-orchestrator.ps1 [Action] [-Message "texto"] [-Debug]

ACCIONES:
    setup       - Configurar y sincronizar el sistema
    test        - Verificar configuración o probar mensaje
    test-all    - Ejecutar todas las pruebas
    direct      - Invocar directamente al Function App
    logic       - Invocar via Logic App
    health      - Check de salud
    status      - Estado del sistema
    dashboard   - Ver dashboard

EJEMPLOS:
    .\invoke-orchestrator.ps1 setup
    .\invoke-orchestrator.ps1 test -Message "lee function_app.py"
    .\invoke-orchestrator.ps1 direct -Message "busca archivos python"
    .\invoke-orchestrator.ps1 test-all -EnableDebug

"@ -ForegroundColor Gray
    }
  }
}

# ============= EJECUTAR =============

if ($Setup) {
  Initialize-Setup
  Test-Setup
}
elseif ($TestAll) {
  Test-Setup
  Test-AllScenarios
}
else {
  Main
}

# Exportar funciones para uso interactivo
Export-ModuleMember -Function @(
  'Invoke-CopilotoDirect',
  'Invoke-ViaLogicApp',
  'Invoke-ArchitectAgent',
  'Invoke-FullPipeline',
  'Test-Setup',
  'Test-AllScenarios'
)