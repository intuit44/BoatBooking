function Get-FoundryToken {
  param (
    [string]$TenantId = $env:AZURE_TENANT_ID,
    [string]$ClientId = $env:AZURE_CLIENT_ID,
    [string]$ClientSecret = $env:AZURE_CLIENT_SECRET,
    [string]$CacheFile = "$PSScriptRoot\generated_token.json"
  )

  if (Test-Path $CacheFile) {
    $json = Get-Content $CacheFile | ConvertFrom-Json
    $expires = [datetime]::Parse($json.expires_on)
    if ($expires -gt (Get-Date).ToUniversalTime().AddMinutes(1)) {
      return $json.access_token
    }
  }

  # Generar nuevo token
  Add-Type -AssemblyName System.Web
  $body = @{
    client_id     = $ClientId
    client_secret = $ClientSecret
    scope         = "https://ai.azure.com/.default"
    grant_type    = "client_credentials"
  }
  $formData = ($body.GetEnumerator() | ForEach-Object {
      "$($_.Key)=$([System.Web.HttpUtility]::UrlEncode($_.Value))"
    }) -join '&'

  $tokenResponse = Invoke-RestMethod `
    -Uri "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token" `
    -Method Post `
    -Body $formData `
    -ContentType "application/x-www-form-urlencoded"

  $token = $tokenResponse.access_token
  $expiresOn = (Get-Date).ToUniversalTime().AddSeconds($tokenResponse.expires_in)

  @{ access_token = $token; expires_on = $expiresOn.ToString("o") } |
  ConvertTo-Json | Set-Content -Path $CacheFile -Encoding utf8

  return $token
}
