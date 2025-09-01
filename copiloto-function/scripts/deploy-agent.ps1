# deploy-agent.ps1
param(
  [string]$Action = "check"
)

$RG = "boat-rental-app-group"
$APPN = "copiloto-semantico-func-us2"
$ACR = "boatrentalacr"

function Get-NextVersion {
  $tags = az acr repository show-tags -n $ACR --repository copiloto-func-azcli --orderby time_desc --top 1 | ConvertFrom-Json
  if ($tags) {
    $lastTag = $tags[0]
    if ($lastTag -match 'v(\d+)') {
      return "v$([int]$matches[1] + 1)"
    }
  }
  return "v1"
}

function Deploy-NewVersion {
  param([string]$Version)
    
  Write-Host "🔨 Building Docker image $Version..."
  docker build -t copiloto-func-azcli:$Version .
    
  Write-Host "🏷️ Tagging image..."
  docker tag copiloto-func-azcli:$Version $ACR.azurecr.io/copiloto-func-azcli:$Version
    
  Write-Host "🔐 Logging into ACR..."
  az acr login -n $ACR
    
  Write-Host "📤 Pushing to ACR..."
  docker push $ACR.azurecr.io/copiloto-func-azcli:$Version
    
  Write-Host "🔄 Updating Function App..."
  az functionapp config container set -g $RG -n $APPN --docker-custom-image-name "$ACR.azurecr.io/copiloto-func-azcli:$Version"
    
  Write-Host "♻️ Restarting Function App..."
  az functionapp restart -g $RG -n $APPN
    
  return @{
    version   = $Version
    success   = $true
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  }
}

# Servidor HTTP local simple
if ($Action -eq "serve") {
  $listener = New-Object System.Net.HttpListener
  $listener.Prefixes.Add("http://localhost:8081/")
  $listener.Start()
    
  Write-Host "Deploy agent listening on http://localhost:8081/"
    
  while ($true) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response
        
    if ($request.Url.LocalPath -eq "/deploy") {
      $version = Get-NextVersion
      Write-Host "Deploying version $version..."
      $result = Deploy-NewVersion -Version $version
            
      $json = $result | ConvertTo-Json
      $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
      $response.ContentLength64 = $buffer.Length
      $response.OutputStream.Write($buffer, 0, $buffer.Length)
    }
        
    $response.Close()
  }
}