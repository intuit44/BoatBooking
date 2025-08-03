# Cargar variables de entorno desde .env
Import-Module .\DotEnv.psm1
Import-DotEnv -Path "C:\ProyectosSimbolicos\boat-rental-app\Multi-Agent-Custom-Automation-Engine-Solution-Accelerator\.env"

# Validar que las variables de entorno estén configuradas
if (-not $env:AZURE_CLIENT_ID -or -not $env:AZURE_CLIENT_SECRET -or -not $env:AZURE_TENANT_ID -or -not $env:AZURE_AI_FOUNDRY_ENDPOINT -or -not $env:AZURE_AI_FOUNDRY_PROJECT) {
  Write-Host "⚠️ Faltan variables de entorno necesarias. Verifica tu archivo .env." -ForegroundColor Red
  return
}

# Generación de Token con scope corregido
$body = @{
  client_id     = $env:AZURE_CLIENT_ID
  client_secret = $env:AZURE_CLIENT_SECRET
  scope         = "https://ai.azure.com/.default"
  grant_type    = "client_credentials"
}

# Convertir a formato URL-encoded
$formData = ($body.GetEnumerator() | ForEach-Object {
    "$($_.Key)=$([System.Web.HttpUtility]::UrlEncode($_.Value))"
  }) -join '&'

# Obtener token
try {
  $tokenResponse = Invoke-RestMethod `
    -Uri "https://login.microsoftonline.com/$($env:AZURE_TENANT_ID)/oauth2/v2.0/token" `
    -Method Post `
    -Body $formData `
    -ContentType "application/x-www-form-urlencoded"

  $token = $tokenResponse.access_token
  Write-Host "✅ Token obtenido exitosamente." -ForegroundColor Green
}
catch {
  Write-Host "⚠️ Error al obtener el token: $($_.Exception.Message)" -ForegroundColor Red
  return
}

# Headers para la API
$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type"  = "application/json"
}

# Intento de conexión con Azure AI Foundry Runtime
$runtimeUrl = "$env:AZURE_AI_FOUNDRY_ENDPOINT/api/projects/$($env:AZURE_AI_FOUNDRY_PROJECT)/agents"

try {
  $response = Invoke-RestMethod -Uri $runtimeUrl -Method Get -Headers $headers
  Write-Host "✅ Conexión exitosa con Azure AI Foundry Runtime!" -ForegroundColor Green
  $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
}
catch {
  Write-Host "⚠️ Error en la solicitud al runtime:" -ForegroundColor Red
  Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Yellow

  # Mostrar respuesta completa del error
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errorResponse = $reader.ReadToEnd()
    $reader.Close()
    Write-Host "Respuesta del servidor:" -ForegroundColor Yellow
    Write-Host $errorResponse -ForegroundColor Yellow
  }
}