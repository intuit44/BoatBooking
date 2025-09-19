# ajustar_mi.ps1
# Verifica y asigna rol a la Managed Identity (MI) de la Function App

# ========= PARÁMETROS =========
$subscriptionId = "380fa841-83f3-42fe-adc4-582a5ebe139b"
$resourceGroup = "boat-rental-app-group"
$functionApp = "copiloto-semantico-func-us2"
$roleName = "Cognitive Services Contributor"

# ========= PASO 1: Establecer suscripción =========
Write-Host "`n[INFO] Estableciendo suscripción activa..." -ForegroundColor Cyan
az account set --subscription $subscriptionId

# ========= PASO 2: Obtener principalId de la MI =========
Write-Host "[INFO] Obteniendo Managed Identity de $functionApp..." -ForegroundColor Cyan
$principalId = az functionapp identity show `
  -g $resourceGroup `
  -n $functionApp `
  --query principalId -o tsv

if (-not $principalId) {
  Write-Host "[ERROR] No se pudo obtener el principalId de la MI." -ForegroundColor Red
  exit 1
}

Write-Host "[OK] Principal ID de la MI: $principalId" -ForegroundColor Green

# ========= PASO 3: Verificar si ya tiene el rol =========
Write-Host "[INFO] Verificando rol asignado sobre $resourceGroup..." -ForegroundColor Cyan
$rolAsignado = az role assignment list `
  --assignee $principalId `
  --scope "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup" `
  --query "[?roleDefinitionName=='$roleName']" -o tsv

if ($rolAsignado) {
  Write-Host ("[OK] La MI ya tiene el rol '{0}' sobre el grupo de recursos." -f $roleName) -ForegroundColor Green
}
else {
  Write-Host ("[WARN] La MI no tiene el rol '{0}'. Asignando..." -f $roleName) -ForegroundColor Yellow

  az role assignment create `
    --assignee $principalId `
    --role "$roleName" `
    --scope "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup" | Out-Null

  Write-Host ("[OK] Rol '{0}' asignado exitosamente a la MI." -f $roleName) -ForegroundColor Green
}
