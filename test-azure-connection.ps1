# test-azure-connection.ps1
# Script para probar la conexión con Azure OpenAI y AI Foundry

# Cargar variables de entorno desde .env
$envPath = "C:\ProyectosSimbolicos\boat-rental-app\.env"
Get-Content $envPath | ForEach-Object {
  if ($_ -match '^([^=]+)=(.*)$') {
    [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
  }
}

Write-Host "=== Probando conexión con Azure OpenAI ===" -ForegroundColor Cyan

# Test 1: Probar el deployment ReadTsxAgent directamente
Write-Host "`nTest 1: ReadTsxAgent deployment (GPT-4o)" -ForegroundColor Yellow

$headers = @{
  "api-key"      = $env:AZURE_OPENAI_API_KEY
  "Content-Type" = "application/json"
}

$body = @{
  messages    = @(
    @{
      role    = "system"
      content = "You are an expert at analyzing React TSX components."
    },
    @{
      role    = "user"
      content = "Analyze this simple component: const Button = () => <button>Click me</button>"
    }
  )
  max_tokens  = 100
  temperature = 0.2
} | ConvertTo-Json -Depth 10

$uri = "https://boatrentalfoundry-dev.openai.azure.com/openai/deployments/ReadTsxAgent/chat/completions?api-version=2024-08-01-preview"

try {
  $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
  Write-Host "✅ Conexión exitosa con ReadTsxAgent!" -ForegroundColor Green
  Write-Host "Respuesta: $($response.choices[0].message.content)" -ForegroundColor Gray
}
catch {
  Write-Host "❌ Error al conectar con ReadTsxAgent:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $responseBody = $reader.ReadToEnd()
    Write-Host "Detalles del error: $responseBody" -ForegroundColor Red
  }
}

# Test 2: Verificar el proyecto AI Foundry
Write-Host "`n`nTest 2: AI Foundry Project API" -ForegroundColor Yellow

$foundryHeaders = @{
  "Authorization" = "Bearer $($env:FOUNDRY_AUTH_TOKEN)"
  "Content-Type"  = "application/json"
}

$foundryUri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/booking-agents"

try {
  $response = Invoke-RestMethod -Uri $foundryUri -Method Get -Headers $foundryHeaders
  Write-Host "✅ Conexión exitosa con AI Foundry Project!" -ForegroundColor Green
  Write-Host "Proyecto: $($response.properties.displayName)" -ForegroundColor Gray
}
catch {
  Write-Host "❌ Error al conectar con AI Foundry:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
}

# Test 3: Listar deployments disponibles
Write-Host "`n`nTest 3: Listar deployments disponibles" -ForegroundColor Yellow

$deploymentsUri = "https://boatrentalfoundry-dev.openai.azure.com/openai/deployments?api-version=2024-08-01-preview"

try {
  $response = Invoke-RestMethod -Uri $deploymentsUri -Method Get -Headers $headers
  Write-Host "✅ Deployments disponibles:" -ForegroundColor Green
  $response.data | ForEach-Object {
    Write-Host "  - $($_.id): $($_.model) (v$($_.model_version))" -ForegroundColor Gray
  }
}
catch {
  Write-Host "❌ Error al listar deployments:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`n=== Resumen ===" -ForegroundColor Cyan
Write-Host "Endpoint Azure OpenAI: https://boatrentalfoundry-dev.openai.azure.com" -ForegroundColor White
Write-Host "Deployment activo: ReadTsxAgent (gpt-4o)" -ForegroundColor White
Write-Host "API Version: 2024-08-01-preview" -ForegroundColor White
Write-Host "`nPara usar en Postman:" -ForegroundColor Yellow
Write-Host "URL: https://boatrentalfoundry-dev.openai.azure.com/openai/deployments/ReadTsxAgent/chat/completions?api-version=2024-08-01-preview" -ForegroundColor White
Write-Host "Header: api-key = $($env:AZURE_OPENAI_API_KEY)" -ForegroundColor White