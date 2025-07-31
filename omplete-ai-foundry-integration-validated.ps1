# complete-ai-foundry-integration-validated.ps1
# Parte 1: Configuración inicial y generación de contexto

param(
  [string]$TargetPath = "C:\ProyectosSimbolicos\boat-rental-app\Multi-Agent-Custom-Automation-Engine-Solution-Accelerator",
  [string]$StorageAccountName = "boatrentalfoundrystorage",
  [string]$ContainerName = "agent-context",
  [switch]$SkipAzureUpload = $false
)

# Configuración de error handling
$ErrorActionPreference = "Stop"
$script:hasErrors = $false
$script:StartTime = Get-Date

Write-Host "=== Completando Integración AI Foundry con Contexto Automático ===" -ForegroundColor Cyan

# Validar path de destino
if (-not (Test-Path $TargetPath)) {
  Write-Host "❌ Error: No existe el directorio $TargetPath" -ForegroundColor Red
  exit 1
}

# 1. Generar archivo de contexto consolidado
Write-Host "`n1️⃣ Generando archivo de contexto consolidado..." -ForegroundColor Yellow

# Función para convertir YAML simple
function ConvertFrom-SimpleYaml {
  param([string]$YamlContent)
    
  if ([string]::IsNullOrWhiteSpace($YamlContent)) {
    return @{}
  }
    
  $result = @{}
  try {
    $lines = $YamlContent -split "`n"
        
    foreach ($line in $lines) {
      if ($line -match '^([^:]+):\s*(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($key -and $value) {
          $result[$key] = $value
        }
      }
    }
  }
  catch {
    Write-Host "  ⚠️ Advertencia: Error parseando YAML - $_" -ForegroundColor Yellow
  }
  return $result
}

# Crear directorio si no existe
$contextDir = "$TargetPath\.codegpt"
if (-not (Test-Path $contextDir)) {
  try {
    New-Item -ItemType Directory -Path $contextDir -Force | Out-Null
    Write-Host "  ✅ Creado directorio .codegpt" -ForegroundColor Green
  }
  catch {
    Write-Host "  ❌ Error creando directorio: $_" -ForegroundColor Red
    $script:hasErrors = $true
  }
}

$contextPath = "$contextDir\agents.context.json"

try {
  # Leer archivos con validación
  $agentsYaml = if (Test-Path "$contextDir\agents.yaml") {
    Get-Content "$contextDir\agents.yaml" -Raw -ErrorAction Stop
  }
  else {
    Write-Host "  ⚠️ No se encontró agents.yaml" -ForegroundColor Yellow
    ""
  }
    
  $envContent = if (Test-Path "$TargetPath\.env") {
    Get-Content "$TargetPath\.env" -Raw -ErrorAction Stop
  }
  else {
    Write-Host "  ⚠️ No se encontró .env" -ForegroundColor Yellow
    ""
  }
    
  $asyncGuide = if (Test-Path "$TargetPath\docs\ASYNC_GUIDE.md") {
    Get-Content "$TargetPath\docs\ASYNC_GUIDE.md" -Raw -ErrorAction Stop
  }
  else {
    Write-Host "  ⚠️ No se encontró ASYNC_GUIDE.md" -ForegroundColor Yellow
    "# Guía no disponible"
  }
    
  $integrationReadme = if (Test-Path "$TargetPath\INTEGRATION_README.md") {
    Get-Content "$TargetPath\INTEGRATION_README.md" -Raw -ErrorAction Stop
  }
  else {
    Write-Host "  ⚠️ No se encontró INTEGRATION_README.md" -ForegroundColor Yellow
    "# README no disponible"
  }
    
  # Parsear .env con validación
  $envVars = @{}
  if (-not [string]::IsNullOrWhiteSpace($envContent)) {
    $envContent -split "`n" | ForEach-Object {
      if ($_ -match '^([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($key -and $value) {
          $envVars[$key] = $value
        }
      }
    }
  }
    
  Write-Host "  📊 Archivos leídos:" -ForegroundColor Gray
  Write-Host "     - Variables de entorno: $($envVars.Count)" -ForegroundColor Gray
  Write-Host "     - YAML size: $($agentsYaml.Length) caracteres" -ForegroundColor Gray
    
  # Crear objeto de contexto
  $contextData = @{
    timestamp     = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    source        = "boat-rental-app-integration"
    version       = "1.0.0"
        
    configuration = @{
      project_id = "booking-agents"
      agent_name = "Agent975"
      endpoints  = @{
        ai_foundry      = "https://boatrentalfoundry-dev.services.ai.azure.com"
        agent975_invoke = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/booking-agents/agents/Agent975/invoke"
        azure_openai    = "https://boatrentalfoundry-dev.openai.azure.com"
      }
    }
        
    agents        = @{
      raw_yaml = if ($agentsYaml) { $agentsYaml } else { "# No YAML disponible" }
      parsed   = @{
        codex_agents      = @("Architect_BoatRental", "Mobile_App_Agent", "Backend_Agent", "AdminPanel_Agent")
        ai_foundry_agents = @("Agent975", "ReadTsxAgent", "RefactorAgent", "PerformanceOptimizer", "TestingExpert")
      }
    }
        
    environment   = @{
      variables     = $envVars
      required_keys = @(
        "FOUNDRY_AUTH_TOKEN",
        "FOUNDRY_API_BASE",
        "AZURE_OPENAI_API_KEY",
        "AI_FOUNDRY_PROJECT_ID"
      )
      missing_keys  = @()
    }
        
    documentation = @{
      async_guide        = if ($asyncGuide) { $asyncGuide } else { "# No disponible" }
      integration_readme = if ($integrationReadme) { $integrationReadme } else { "# No disponible" }
      quick_start        = "# Quick Start`n1. Load this context in AI Foundry Assistant`n2. Use Agent975 for TSX analysis`n3. Input format: {`"input`": {`"code`": `"your code here`"}}"
    }
        
    agent975      = @{
      description  = "Custom agent for BoatRental TSX analysis"
      file_info    = @{
        name     = "agent975.zip"
        size     = "862.8 KB"
        uploaded = $true
        handler  = "handler.js"
      }
      capabilities = @(
        "TSX component analysis",
        "Complexity calculation", 
        "Code quality feedback",
        "Boat rental specific logic"
      )
    }
        
    validation    = @{
      files_checked  = @{
        agents_yaml        = (Test-Path "$contextDir\agents.yaml")
        env_file           = (Test-Path "$TargetPath\.env")
        async_guide        = (Test-Path "$TargetPath\docs\ASYNC_GUIDE.md")
        integration_readme = (Test-Path "$TargetPath\INTEGRATION_README.md")
      }
      env_vars_count = $envVars.Count
      generated_at   = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
  }
    
  # Verificar claves requeridas
  $missingKeys = @()
  foreach ($key in $contextData.environment.required_keys) {
    if (-not $envVars.ContainsKey($key)) {
      $missingKeys += $key
    }
  }
  $contextData.environment.missing_keys = $missingKeys
    
  if ($missingKeys.Count -gt 0) {
    Write-Host "  ⚠️ Faltan variables de entorno: $($missingKeys -join ', ')" -ForegroundColor Yellow
  }
    
  # Convertir a JSON
  Write-Host "  🔄 Convirtiendo a JSON..." -ForegroundColor Gray
  $jsonContent = $null
  try {
    $jsonContent = $contextData | ConvertTo-Json -Depth 10 -ErrorAction Stop
  }
  catch {
    Write-Host "  ❌ Error convirtiendo a JSON: $_" -ForegroundColor Red
    throw
  }
    
  # Validar contenido
  if ([string]::IsNullOrWhiteSpace($jsonContent)) {
    throw "El contenido JSON está vacío"
  }
    
  if ($jsonContent.Length -lt 50) {
    throw "El contenido JSON es demasiado pequeño ($($jsonContent.Length) caracteres)"
  }
    
  Write-Host "  📝 JSON generado: $($jsonContent.Length) caracteres" -ForegroundColor Gray
    
  # Guardar archivo
  try {
    $jsonContent | Out-File -FilePath $contextPath -Encoding UTF8 -ErrorAction Stop
        
    if (-not (Test-Path $contextPath)) {
      throw "El archivo no se guardó correctamente"
    }
        
    $savedFile = Get-Item $contextPath
    if ($savedFile.Length -eq 0) {
      throw "El archivo se guardó pero está vacío"
    }
        
    Write-Host "  ✅ Archivo de contexto generado: $contextPath" -ForegroundColor Green
    Write-Host "     Tamaño: $([math]::Round($savedFile.Length / 1KB, 2)) KB" -ForegroundColor Gray
        
  }
  catch {
    Write-Host "  ❌ Error guardando archivo: $_" -ForegroundColor Red
    throw
  }
    
}
catch {
  Write-Host "❌ Error generando contexto: $_" -ForegroundColor Red
  $script:hasErrors = $true
    
  # Crear contexto mínimo
  try {
    $minimalContext = @{
      timestamp    = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
      error        = "Error generando contexto completo"
      message      = $_.ToString()
      basic_config = @{
        agent    = "Agent975"
        endpoint = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/booking-agents/agents/Agent975/invoke"
      }
    } | ConvertTo-Json -Depth 5
        
    $minimalContext | Out-File -FilePath $contextPath -Encoding UTF8
    Write-Host "  ⚠️ Generado contexto mínimo de emergencia" -ForegroundColor Yellow
  }
  catch {
    Write-Host "  ❌ No se pudo generar ni el contexto mínimo" -ForegroundColor Red
    exit 1
  }
}

Write-Host "`n✅ Parte 1 completada. Contexto generado." -ForegroundColor Green
Write-Host "Continúa con la Parte 2 para subir a Azure y generar scripts..." -ForegroundColor Cyan