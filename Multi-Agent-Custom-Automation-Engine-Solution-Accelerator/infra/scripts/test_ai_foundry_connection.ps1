# Generación de Token con scope corregido
$body = @{
  client_id     = "9b6082b6-0f95-4620-924a-c2e9232e9ac4"
  client_secret = "uDk8Q~7cdlHkLf2plh-xUr1ukNYvhS4VDEaPIb5W"
  scope         = "https://ai.azure.com/.default"
  grant_type    = "client_credentials"
}

# Convertir a formato URL-encoded
$formData = ($body.GetEnumerator() | ForEach-Object {
    "$($_.Key)=$([System.Web.HttpUtility]::UrlEncode($_.Value))"
  }) -join '&'

# Obtener token
$tokenResponse = Invoke-RestMethod `
  -Uri "https://login.microsoftonline.com/978d9cc6-784c-4c98-8d90-a4a6344a65ff/oauth2/v2.0/token" `
  -Method Post `
  -Body $formData `
  -ContentType "application/x-www-form-urlencoded"

$token = $tokenResponse.access_token

# Headers para la API
$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type"  = "application/json"
  "api-version"   = "2023-10-01"
}

# Intento de conexión con endpoint de management
$managementUrl = "https://management.azure.com/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.CognitiveServices/accounts/boatRentalFoundry-dev/projects/booking-agents?api-version=2023-10-01"

try {
  $response = Invoke-RestMethod -Uri $managementUrl -Method Get -Headers $headers
  Write-Host "Conexión exitosa!" -ForegroundColor Green
  $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
}
catch {
  Write-Host "Error en la solicitud:" -ForegroundColor Red
  Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
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