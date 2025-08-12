param(
  [switch]$Apply,                       # sin -Apply solo valida
  [string]$SubscriptionId = "380fa841-83f3-42fe-adc4-582a5ebe139b",
  [string]$RG = "boat-rental-app-group",
  [string]$Site = "copiloto-semantico-func",
  [string]$Workflow = "invocar-copiloto",

  # Storage / Cosmos: **PON AQUÍ TUS NOMBRES REALES**
  [string]$StorageAcct = "boatrentalstorage",
  [string]$BlobContainer = "contexto-agentes",
  [string]$BlobPrefix = "supervisor",
  [string]$CosmosAcct = "boatrentalcosmos",
  [string]$CosmosDBName = "contexto-agentes",
  [string]$CosmosColl = "ejecuciones",
  [string]$CosmosPK = "/id",

  [string]$AppInsightsPreferred = "boatRentalInsights",
  [string]$SPName = "CopilotoSemantico-SP"
)

$ErrorActionPreference = "Stop"
chcp 65001 | Out-Null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function info($m) { Write-Host $m -ForegroundColor Cyan }
function ok($m) { Write-Host $m -ForegroundColor Green }
function warn($m) { Write-Host "ADVERTENCIA: $m" -ForegroundColor Yellow }
function fail($m) { Write-Host "ERROR: $m" -ForegroundColor Red }

# ---- Mode banner (PS 5.1 safe) ----
$mode = if ($Apply) { 'APPLY' } else { 'VALIDATE' }
Write-Host ">>> Script Supervisor-Ejecutor INICIADO (modo: $mode)" -ForegroundColor Cyan

# --- PRE-FLIGHT ---
$subOK = az account show --query id -o tsv 2>$null
if (-not $subOK) { fail "No hay sesión de az login"; exit 1 }
if ($subOK -ne $SubscriptionId) { warn "Suscripción activa: $subOK; esperada: $SubscriptionId" }

$rgOK = az group exists -n $RG -o tsv
if ($rgOK -ne "true") {
  if (-not $Apply) { fail "No existe RG '$RG'"; exit 1 }
  az group create -n $RG -l eastus | Out-Null
  ok "RG creado: $RG"
}

$funcOK = az functionapp show -g $RG -n $Site --query name -o tsv 2>$null
if (-not $funcOK) { fail "Function App '$Site' no existe"; if (-not $Apply) { exit 1 } }

$wfOK = az resource show -g $RG -n $Workflow --resource-type "Microsoft.Logic/workflows" --query name -o tsv 2>$null
if (-not $wfOK) { fail "Logic App '$Workflow' no existe"; if (-not $Apply) { exit 1 } }

# Storage
$stOK = az storage account show -g $RG -n $StorageAcct --query name -o tsv 2>$null
if (-not $stOK) { warn "Storage '$StorageAcct' no existe" }
else {
  $storKey = az storage account keys list -g $RG -n $StorageAcct --query [0].value -o tsv
  $cntExists = az storage container exists --name $BlobContainer --account-name $StorageAcct --account-key $storKey --query exists -o tsv
  if ($cntExists -ne "true") {
    warn "No existe contenedor '$BlobContainer'"
    if ($Apply) {
      az storage container create --name $BlobContainer --account-name $StorageAcct --account-key $storKey | Out-Null
      ok "Contenedor creado: $BlobContainer"
    }
  }
  else { ok "Blob container OK: $BlobContainer" }
}

# Cosmos
$cosmosOK = az cosmosdb show -g $RG -n $CosmosAcct --query name -o tsv 2>$null
if (-not $cosmosOK) {
  warn "CosmosDB '$CosmosAcct' no existe"
  if ($Apply) {
    info "Creando Cosmos (SQL) + DB + Container..."
    az cosmosdb create -g $RG -n $CosmosAcct --kind GlobalDocumentDB --default-consistency-level Session --enable-free-tier true | Out-Null
    az cosmosdb sql database create -g $RG -a $CosmosAcct -n $CosmosDBName | Out-Null
    az cosmosdb sql container create -g $RG -a $CosmosAcct -d $CosmosDBName -n $CosmosColl --partition-key-path $CosmosPK | Out-Null
    ok "Cosmos listo: $CosmosAcct/$CosmosDBName/$CosmosColl"
  }
}
else {
  ok "Cosmos OK: $CosmosAcct"
}

# App Insights
$aiName = $null; $aiRG = $null
$aiPrefOK = az monitor app-insights component show -g $RG -a $AppInsightsPreferred --query name -o tsv 2>$null
if ($aiPrefOK) { $aiName = $AppInsightsPreferred; $aiRG = $RG; ok "Application Insights: $aiName" }
else {
  $fallback = az resource list --resource-type Microsoft.Insights/components --query "[0].{Name:name,RG:resourceGroup}" -o json | ConvertFrom-Json
  if ($fallback) { $aiName = $fallback.Name; $aiRG = $fallback.RG; warn "Usando App Insights existente: $aiName (RG=$aiRG)" }
  else { warn "No se encontró Application Insights" }
}

# --- PERMISOS (SP + MI) ---
$spObjId = az ad sp list --display-name $SPName --query "[0].id" -o tsv
if (-not $spObjId -and $Apply) {
  warn "Creando SP $SPName..."
  $sp = az ad sp create-for-rbac --name $SPName --skip-assignment -o json | ConvertFrom-Json
  $spObjId = az ad sp show --id $sp.appId --query id -o tsv
  ok "SP creado: objectId=$spObjId"
}
if (-not $spObjId) { warn "SP no disponible (ejecuta con -Apply para crearlo)" }

function Set-RoleAssignment($role, $scope, $objId) {
  if (-not $objId -or [string]::IsNullOrEmpty($scope)) { return }
  $exists = az role assignment list --assignee-object-id $objId --scope $scope --role $role --query "[0].id" -o tsv
  if ($exists) { ok "✓ $role @ $scope" }
  elseif ($Apply) {
    az role assignment create --assignee-object-id $objId --assignee-principal-type ServicePrincipal --role $role --scope $scope | Out-Null
    ok "Asignado $role @ $scope"
  }
  else { warn "Falta $role @ $scope" }
}

$subScope = "/subscriptions/$SubscriptionId"
$stScope = if ([string]::IsNullOrEmpty($StorageAcct)) { "" } else { "$subScope/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$StorageAcct" }
$faScope = "$subScope/resourceGroups/$RG/providers/Microsoft.Web/sites/$Site"
$wfScope = "$subScope/resourceGroups/$RG/providers/Microsoft.Logic/workflows/$Workflow"
$aiScope = if ($aiName -and $aiRG) { "$subScope/resourceGroups/$aiRG/providers/Microsoft.Insights/components/$aiName" } else { "" }
$cosmosScope = if ([string]::IsNullOrEmpty($CosmosAcct)) { "" } else { "$subScope/resourceGroups/$RG/providers/Microsoft.DocumentDB/databaseAccounts/$CosmosAcct" }

Set-RoleAssignment "Reader"                        $subScope  $spObjId
Set-RoleAssignment "Storage Blob Data Contributor" $stScope   $spObjId
Set-RoleAssignment "Logic App Contributor"         $wfScope   $spObjId
Set-RoleAssignment "Contributor"                   $faScope   $spObjId
if (-not [string]::IsNullOrEmpty($aiScope)) { Set-RoleAssignment "Application Insights Component Contributor" $aiScope $spObjId }
if (-not [string]::IsNullOrEmpty($cosmosScope)) { Set-RoleAssignment "Contributor" $cosmosScope $spObjId }

# Managed Identity (Function)
$miPrincipal = az functionapp identity show -g $RG -n $Site --query principalId -o tsv 2>$null
if (-not $miPrincipal -and $Apply) {
  az functionapp identity assign -g $RG -n $Site | Out-Null
  $miPrincipal = az functionapp identity show -g $RG -n $Site --query principalId -o tsv
  ok ("MI asignada a ${Site}: $miPrincipal")
}
if ($miPrincipal) {
  Set-RoleAssignment "Storage Blob Data Reader" $stScope $miPrincipal
  if (-not [string]::IsNullOrEmpty($aiScope)) { Set-RoleAssignment "Reader" $aiScope $miPrincipal }
}

# App settings de observabilidad (solo si tenemos AI)
if ($aiName) {
  $aiConn = az monitor app-insights component show -g $aiRG -a $aiName --query connectionString -o tsv 2>$null
  if ($aiConn -and $Apply) {
    az functionapp config appsettings set -g $RG -n $Site --settings "APPLICATIONINSIGHTS_CONNECTION_STRING=$aiConn" | Out-Null
    ok "Set APPLICATIONINSIGHTS_CONNECTION_STRING"
  }
  elseif ($aiConn) { ok "AI connectionString detectado (no aplicado sin -Apply)" }
}

# --- Unificar MasterKey en Logic App ---
$hostKeys = az rest --method post --uri "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$RG/providers/Microsoft.Web/sites/$Site/host/default/listKeys?api-version=2022-03-01" -o json | ConvertFrom-Json
$unicaKey = $hostKeys.functionKeys.default
if ([string]::IsNullOrEmpty($unicaKey)) {
  warn "No pude leer host default key (saltando reemplazo MasterKey)."
}
else {
  $defRaw = az resource show -g $RG --resource-type "Microsoft.Logic/workflows" -n $Workflow --api-version 2019-05-01 --query "properties.definition" -o json
  $def = $defRaw | ConvertFrom-Json

  $hits = 0
  function Patch-MasterKeys($node) {
    if ($null -eq $node) { return }
    if ($node.type -eq "SetVariable" -and $node.inputs -and $node.inputs.name -eq "MasterKey") {
      $node.inputs.value = $unicaKey; $script:hits++
    }
    foreach ($p in $node.PSObject.Properties) {
      $v = $p.Value
      if ($v -is [System.Collections.IDictionary] -or $v -is [System.Management.Automation.PSObject]) { Patch-MasterKeys $v }
      elseif ($v -is [System.Collections.IEnumerable]) { foreach ($i in $v) { Patch-MasterKeys $i } }
    }
  }
  Patch-MasterKeys $def

  if ($hits -gt 0) {
    if ($Apply) {
      $bodyObject = @{ properties = @{ definition = $def } }
      $bodyJson = ($bodyObject | ConvertTo-Json -Depth 100)
      az rest --method patch `
        --uri "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$RG/providers/Microsoft.Logic/workflows/$Workflow?api-version=2019-05-01" `
        --headers "Content-Type=application/json" `
        --body $bodyJson | Out-Null
      ok "Reemplazadas $hits asignaciones de MasterKey por la host default key."
    }
    else {
      warn "Encontradas $hits asignaciones MasterKey. Reemplazo SIMULADO (ejecuta con -Apply para aplicar)."
    }
  }
  else { ok "No se encontraron SetVariable('MasterKey')." }
}

# --- Smoke tests Function App ---
try {
  $h = Invoke-RestMethod "https://$Site.azurewebsites.net/api/health"
  if ($h.status -eq "healthy") { ok "Health OK" } else { warn "Health responde pero no 'healthy'" }
}
catch { warn "Health falló: $($_.Exception.Message)" }

if (-not [string]::IsNullOrEmpty($unicaKey)) {
  try { Invoke-RestMethod "https://$Site.azurewebsites.net/api/status?code=$unicaKey" | Out-Null; ok "Status 200" }catch { warn "Status 401/403" }
  try {
    $body = @{ intencion = "dashboard"; modo = "normal"; parametros = @{} } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://$Site.azurewebsites.net/api/ejecutar?code=$unicaKey" -Method POST -Body $body -ContentType "application/json" | Out-Null
    ok "Ejecutar 200"
  }
  catch { warn "Ejecutar falló" }
}

$mode = if ($Apply) { 'APPLY' } else { 'VALIDATE' }
ok "✅ FIN (modo: $mode)"

