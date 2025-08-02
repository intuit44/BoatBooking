# Cargar el ensamblado necesario para UrlEncode
Add-Type -AssemblyName System.Web

# Configuración inicial
$tenantId = "978d9cc6-784c-4c98-8d90-a4a6344a65ff"
$clientId = "9b6082b6-0f95-4620-924a-c2e9232e9ac4"
$clientSecret = "uDk8Q~7cdlHkLf2plh-xUr1ukNYvhS4VDEaPIb5W"  # Considera usar Azure Key Vault para almacenar esto

# URL de autenticación
$tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"

# Crear el cuerpo de la solicitud
$body = @{
  client_id     = $clientId
  client_secret = $clientSecret
  scope         = "https://ai.azure.com/.default"
  grant_type    = "client_credentials"
}


# Convertir a formato x-www-form-urlencoded usando System.Web.HttpUtility
$formData = ($body.GetEnumerator() | ForEach-Object {
    "$($_.Key)=$([System.Web.HttpUtility]::UrlEncode($_.Value))"
  }) -join '&'

# Solicitud para obtener token
try {
  $response = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $formData -ContentType "application/x-www-form-urlencoded"
  $token = $response.access_token
    
  if (-not $token) {
    Write-Host "Error: No se recibió token en la respuesta" -ForegroundColor Red
    return $null
  }
    
  Write-Host "Token obtenido exitosamente (primeros caracteres): $($token.Substring(0,20))..." -ForegroundColor Green
  return $token
}
catch {
  Write-Host "Error al obtener token:" -ForegroundColor Red
  Write-Host "Código de estado: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
  Write-Host "Mensaje: $($_.Exception.Message)" -ForegroundColor Yellow
    
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errorResponse = $reader.ReadToEnd()
    $reader.Close()
    Write-Host "Respuesta del servidor:" -ForegroundColor Yellow
    Write-Host $errorResponse -ForegroundColor Yellow
  }
    
  return $null
}