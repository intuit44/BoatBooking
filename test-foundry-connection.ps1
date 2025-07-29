# test-foundry-connection.ps1
# Script para probar la conexión con Azure AI Foundry (no Azure OpenAI)

param(
  [string]$SourcePath = "C:\ProyectosSimbolicos\boat-rental-app",
  [string]$TargetPath = "C:\ProyectosSimbolicos\boat-rental-app\Multi-Agent-Custom-Automation-Engine-Solution-Accelerator"
)

Write-Host "=== Probando conexión con Azure AI Foundry ===" -ForegroundColor Cyan
Write-Host "Origen: $SourcePath" -ForegroundColor White
Write-Host "Destino: $TargetPath" -ForegroundColor White

# Verificar que los paths existen
if (-not (Test-Path $SourcePath)) {
  Write-Host "❌ Error: No se encuentra el directorio origen: $SourcePath" -ForegroundColor Red
  exit 1
}
if (-not (Test-Path $TargetPath)) {
  Write-Host "❌ Error: No se encuentra el directorio destino: $TargetPath" -ForegroundColor Red
  exit 1
}

# Obtener token de acceso para AI Foundry
Write-Host "`nObteniendo token de acceso..." -ForegroundColor Yellow
try {
  $tokenResponse = az account get-access-token --resource https://ai.azure.com | ConvertFrom-Json
  $accessToken = $tokenResponse.accessToken
  Write-Host "✅ Token obtenido exitosamente" -ForegroundColor Green
}
catch {
  Write-Host "❌ Error al obtener token. Asegúrate de estar logueado con 'az login'" -ForegroundColor Red
  exit 1
}

# Headers para AI Foundry
$headers = @{
  "Authorization" = "Bearer $accessToken"
  "Content-Type"  = "application/json"
}

# Detectar automáticamente el ID del proyecto por displayName
Write-Host "`nBuscando ID de proyecto por displayName 'booking-agents'..." -ForegroundColor Yellow
$projectsUri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects"
$projectId = $null
try {
  $response = Invoke-RestMethod -Uri $projectsUri -Method Get -Headers $headers
  foreach ($proj in $response) {
    if ($proj.properties.displayName -eq "booking-agents") {
      $projectId = $proj.properties.internalId
      Write-Host "✅ Proyecto encontrado: $($proj.properties.displayName)" -ForegroundColor Green
      Write-Host "  - ID: $projectId" -ForegroundColor Gray
      break
    }
  }
  if (-not $projectId) {
    Write-Host "❌ No se encontró el proyecto con displayName 'booking-agents'" -ForegroundColor Red
    exit 1
  }
}
catch {
  Write-Host "❌ Error al listar proyectos:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  exit 1
}

# Usar $projectId en las siguientes llamadas en vez de hardcodear el ID
$projectUri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/$projectId"
$agentsUri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/$projectId/agents"
$agent975Uri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/$projectId/agents/Agent975/invoke"
$deploymentsUri = "https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/$projectId/deployments"

# Test 1: Verificar proyecto AI Foundry
Write-Host "`nTest 1: Verificar proyecto 'booking-agents'" -ForegroundColor Yellow

try {
  $response = Invoke-RestMethod -Uri $projectUri -Method Get -Headers $headers
  Write-Host "✅ Proyecto encontrado: $($response.properties.displayName)" -ForegroundColor Green
  Write-Host "  - ID: $($response.properties.internalId)" -ForegroundColor Gray
  Write-Host "  - Estado: $($response.properties.provisioningState)" -ForegroundColor Gray
}
catch {
  Write-Host "❌ Error al acceder al proyecto:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
}

# Test 2: Listar agentes disponibles
Write-Host "`nTest 2: Listar agentes disponibles" -ForegroundColor Yellow

try {
  $response = Invoke-RestMethod -Uri $agentsUri -Method Get -Headers $headers
  Write-Host "✅ Agentes encontrados:" -ForegroundColor Green
  $response | ForEach-Object {
    Write-Host "  - $($_.name): $($_.description)" -ForegroundColor Gray
  }
}
catch {
  Write-Host "⚠️  No se pudieron listar agentes (esto es normal si no hay agentes creados)" -ForegroundColor Yellow
}

# Test 3: Probar invocación del Agent975
Write-Host "`nTest 3: Probar invocación del Agent975" -ForegroundColor Yellow

$code = @'
const HomeScreen = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => setLoading(false), 1000);
  }, []);

  if (loading) return <Text>Loading...</Text>;

  return (
    <View>
      <Text>Welcome to Boat Rental</Text>
    </View>
  );
};
'@

$body = @{
  input = @{
    code = $code
  }
} | ConvertTo-Json -Depth 10 -Compress

try {
  $response = Invoke-RestMethod -Uri $agent975Uri -Method Post -Headers $headers -Body $body
  Write-Host "✅ Agent975 respondió exitosamente!" -ForegroundColor Green
  Write-Host "Respuesta:" -ForegroundColor Gray
  $response | ConvertTo-Json -Depth 10 | Write-Host
}
catch {
  Write-Host "❌ Error al invocar Agent975:" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $responseBody = $reader.ReadToEnd()
    Write-Host "Detalles: $responseBody" -ForegroundColor Red
  }
}

# Test 4: Verificar deployments de modelos
Write-Host "`nTest 4: Verificar deployments de modelos" -ForegroundColor Yellow

try {
  $response = Invoke-RestMethod -Uri $deploymentsUri -Method Get -Headers $headers
  Write-Host "✅ Deployments disponibles:" -ForegroundColor Green
  $response | ForEach-Object {
    Write-Host "  - $($_.name): $($_.model)" -ForegroundColor Gray
  }
}
catch {
  Write-Host "⚠️  No se pudieron listar deployments" -ForegroundColor Yellow
}

Write-Host "`n=== Resumen ===" -ForegroundColor Cyan
Write-Host "Endpoint AI Foundry: https://boatrentalfoundry-dev.services.ai.azure.com" -ForegroundColor White
Write-Host "Proyecto: booking-agents" -ForegroundColor White
Write-Host "Agente principal: Agent975" -ForegroundColor White
Write-Host "`nPara usar en tu aplicación:" -ForegroundColor Yellow
Write-Host "1. Usa 'az account get-access-token --resource https://ai.azure.com' para obtener token" -ForegroundColor White
Write-Host "2. Incluye el token en header 'Authorization: Bearer [token]'" -ForegroundColor White
Write-Host "3. POST a: https://boatrentalfoundry-dev.services.ai.azure.com/api/projects/booking-agents/agents/Agent975/invoke" -ForegroundColor White