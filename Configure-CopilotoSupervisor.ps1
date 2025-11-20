param(
  [switch]$Apply,                       # Sin esto, solo valida
  [string]$SubscriptionId = "380fa841-83f3-42fe-adc4-582a5ebe139b",
  [string]$RG = "boat-rental-app-group",
  [string]$Site = "copiloto-semantico-func",
  [string]$Workflow = "invocar-copiloto",

  # Storage de contexto
  [string]$StorageAcct = "boatrentalstorage",
  [string]$BlobContainer = "contexto-agentes",
  [string]$BlobPrefix = "supervisor",

  # Cosmos (SQL/Core)
  [string]$CosmosAcct = "boatrentalcosmos",
  [string]$CosmosDBName = "contexto-agentes",
  [string]$CosmosColl = "ejecuciones",
  [string]$CosmosPK = "/id",

  # App Insights (preferido). Si no existe, cae al encontrado en rg-DEV.
  [string]$AppInsightsPreferred = "boatRentalInsights",

  # Service Principal
  [string]$SPName = "CopilotoSemantico-SP"
)

$ErrorActionPreference = "Stop"
chcp 65001 | Out-Null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function info($m) { Write-Host $m -ForegroundColor Cyan }
function ok($m) { Write-Host $m -ForegroundColor Green }
function warn($m) { Write-Host "ADVERTENCIA: $m" -ForegroundColor Yellow }
function fail($m) { Write-Host "ERROR: $m" -ForegroundColor Red }

# ---------- PRE-FLIGHT: recursos ----------
info "`n[PRE-FLIGHT] Validando recursos base..."
$subOK = az account show --query id -o tsv 2>$null
if (-not $subOK) { fail "No hay sesiÃ³n de az login"; return }
if ($subOK -ne $SubscriptionId) { warn "La suscripciÃ³n activa es $subOK; esperada $SubscriptionId. Continuo pero verifica." }

$rgOK = az group exists -n $RG -o tsv
if (-not $rgOK) { fail "No existe RG '$RG'"; if (-not $Apply) { return } else { az group create -n $RG -l eastus | Out-Null; ok "RG creado" } }

# Function App
$funcOK = az functionapp show -g $RG -n $Site --query "name" -o tsv 2>$null
if ($funcOK) { ok "Function App: $Site" } else { fail "Function App '$Site' no existe"; if (-not $Apply) { return } }

# Logic App
$wfOK = az resource show -g $RG -n $Workflow --resource-type "Microsoft.Logic/workflows" --query name -o tsv 2>$null
if ($wfOK) { ok "Logic App: $Workflow" } else { fail "Logic App '$Workflow' no existe"; if (-not $Apply) { return } }

# Storage account
$stOK = az storage account show -g $RG -n $StorageAcct --query name -o tsv 2>$null
if ($stOK) { ok "Storage: $StorageAcct" } else { fail "Storage '$StorageAcct' no existe"; if (-not $Apply) { return } }

# Blob container
if ($stOK) {
  $storKey = az storage account keys list -g $RG -n $StorageAcct --query [0].value -o tsv
  $cntExists = az storage container exists --name $BlobContainer --account-name $StorageAcct --account-key $storKey --query exists -o tsv
  if ($cntExists -eq "true") { ok "Blob container: $BlobContainer" } else {
    warn "No existe contenedor '$BlobContainer'"
    if ($Apply) {
      az storage container create --name $BlobContainer --account-name $StorageAcct --account-key $storKey | Out-Null
      ok "Contenedor creado"
    }
  }
}

# Cosmos DB account (SQL)
$cosmosOK = az cosmosdb show -g $RG -n $CosmosAcct --query name -o tsv 2>$null
if ($cosmosOK) { ok "CosmosDB: $CosmosAcct" } else { warn "CosmosDB '$CosmosAcct' no existe" }

# App Insights (preferido)
$aiName = $null
$aiRG = $null
$aiPrefOK = az monitor app-insights component show -g $RG -a $AppInsightsPreferred --query name -o tsv 2>$null
if ($aiPrefOK) {
  $aiName = $AppInsightsPreferred; $aiRG = $RG; ok "Application Insights: $aiName"
}
else {
  # fallback: busca uno en la suscripciÃ³n con 'insight' y lista 1
  $fallback = az resource list --resource-type Microsoft.Insights/components --query "[0].{Name:name,RG:resourceGroup}" -o json | ConvertFrom-Json
  if ($fallback) {
    $aiName = $fallback.Name; $aiRG = $fallback.RG
    warn "Usando App Insights existente: $aiName (RG=$aiRG). Recomendado crear/usar $AppInsightsPreferred en $RG."
  }
  else {
    warn "No se encontrÃ³ Application Insights."
  }
}

# ---------- PERMISOS ----------
info "`n[PERMISOS] Service Principal + Role Assignments"
$spObjId = az ad sp list --display-name $SPName --query "[0].id" -o tsv
if (-not $spObjId -and $Apply) {
  warn "Creando SP $SPName..."
  $sp = az ad sp create-for-rbac --name $SPName --skip-assignment -o json | ConvertFrom-Json
  $spObjId = az ad sp show --id $sp.appId --query id -o tsv
  ok "SP creado: objectId=$spObjId"
}
if (-not $spObjId) { warn "SP no disponible (ejecuta con -Apply para crearlo)"; }

function Ensure-Role($role, $scope, $objId) {
  if (-not $objId) { return }
  $exists = az role assignment list --assignee-object-id $objId --scope $scope --role $role --query "[0].id" -o tsv
  if ($exists) {
    ok "âœ“ $role @ $scope" }
  elseif($Apply){
    az role assignment create --assignee-object-id $objId --assignee-principal-type ServicePrincipal --role $role --scope $scope | Out-Null
    ok "Asignado $role @ $scope"
  } else { warn "Falta $role @ $scope" }
}

# Scopes
$subScope = "/subscriptions/$SubscriptionId"
$stScope  = "$subScope/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$StorageAcct"
$faScope  = "$subScope/resourceGroups/$RG/providers/Microsoft.Web/sites/$Site"
$wfScope  = "$subScope/resourceGroups/$RG/providers/Microsoft.Logic/workflows/$Workflow"
$aiScope  = ($aiName -and $aiRG) ? "$subScope/resourceGroups/$aiRG/providers/Microsoft.Insights/components/$aiName" : $null
$cosmosScope = "$subScope/resourceGroups/$RG/providers/Microsoft.DocumentDB/databaseAccounts/$CosmosAcct"

# Asignaciones al SP (supervisiÃ³n/ejecuciÃ³n)
Ensure-Role "Reader"                         $subScope  $spObjId
Ensure-Role "Storage Blob Data Contributor"  $stScope   $spObjId
Ensure-Role "Logic App Contributor"          $wfScope   $spObjId
Ensure-Role "Contributor"                    $faScope   $spObjId
if($aiScope){ Ensure-Role "Application Insights Component Contributor" $aiScope $spObjId }
# Cosmos: permisos de plano de control (Contributor al account, opcional)
if($cosmosOK){ Ensure-Role "Contributor" $cosmosScope $spObjId }

# Managed Identity (Function App)
info "`n[PERMISOS] Managed Identity de la Function"
$miPrincipal = az functionapp identity show -g $RG -n $Site --query principalId -o tsv 2>$null
if(-not $miPrincipal -and $Apply){
  az functionapp identity assign -g $RG -n $Site | Out-Null
  $miPrincipal = az functionapp identity show -g $RG -n $Site --query principalId -o tsv
  ok "MI asignada a $Site: $miPrincipal"
}
if($miPrincipal){
  Ensure-Role "Storage Blob Data Reader" $stScope $miPrincipal
  if($aiScope){ Ensure-Role "Reader" $aiScope $miPrincipal }
  # Cosmos (RBAC de plano de datos) â€“ si estÃ¡ habilitado en tu cuenta:
    if ($cosmosOK -and $Apply) {
      try {
        $roleDefId = az cosmosdb sql role definition list -g $RG -a $CosmosAcct --query "[?roleName=='Cosmos DB Built-in Data Contributor'].id | [0]" -o tsv
        if ($roleDefId) {
          $raScope = "/subscriptions/$SubscriptionId/resourceGroups/$RG/providers/Microsoft.DocumentDB/databaseAccounts/$CosmosAcct"
          az cosmosdb sql role assignment create -g $RG -a $CosmosAcct --principal-id $miPrincipal --role-definition-id $roleDefId --scope $raScope | Out-Null
          ok "Cosmos DB data-plane role para la MI"
        }
        else {
          warn "No hallÃ© 'Cosmos DB Built-in Data Contributor'. Verifica RBAC de Cosmos habilitado."
        }
      }
      catch { warn "AsignaciÃ³n RBAC Cosmos saltada: $($_.Exception.Message)" }
    }
  }

  # ---------- APP SETTINGS (Function) ----------
  info "`n[APP SETTINGS] Ajustes de conexiÃ³n/observabilidad"
  # App Insights connection string
  if ($aiName) {
    $aiConn = az monitor app-insights component show -g $aiRG -a $aiName --query connectionString -o tsv 2>$null
    if ($aiConn -and $Apply) {
      az functionapp config appsettings set -g $RG -n $Site --settings "APPLICATIONINSIGHTS_CONNECTION_STRING=$aiConn" | Out-Null
      ok "Set APPLICATIONINSIGHTS_CONNECTION_STRING"
    }
    elseif ($aiConn) { ok "AI connectionString detectado (no aplicado sin -Apply)" }
  }

  # Storage contexto
  if ($Apply) {
    az functionapp config appsettings set -g $RG -n $Site --settings `
      "CONTEXT_STORAGE_ACCOUNT=$StorageAcct" `
      "CONTEXT_CONTAINER=$BlobContainer" `
      "CONTEXT_PREFIX=$BlobPrefix" `
      "ENABLE_SUPERVISOR_MODE=true" | Out-Null
    ok "Set appsettings de contexto"
  }

  # ---------- COSMOS (crear si falta) ----------
  if (-not $cosmosOK) {
    warn "CosmosDB no existe."
    if ($Apply) {
      info "Creando CosmosDB (SQL) + DB + Container..."
      az cosmosdb create -g $RG -n $CosmosAcct --kind GlobalDocumentDB --default-consistency-level Session --enable-free-tier true | Out-Null
      az cosmosdb sql database create -g $RG -a $CosmosAcct -n $CosmosDBName | Out-Null
      az cosmosdb sql container create -g $RG -a $CosmosAcct -d $CosmosDBName -n $CosmosColl --partition-key-path $CosmosPK | Out-Null
      ok "Cosmos preparado: $CosmosAcct/$CosmosDBName/$CosmosColl"
    }
  }
  else {
    ok "Cosmos OK. Verificando DB/Container..."
    $dbOK = az cosmosdb sql database show  -g $RG -a $CosmosAcct -n $CosmosDBName --query name -o tsv 2>$null
    $colOK = az cosmosdb sql container show -g $RG -a $CosmosAcct -d $CosmosDBName -n $CosmosColl --query name -o tsv 2>$null
    if (-not $dbOK -and $Apply) { az cosmosdb sql database create -g $RG -a $CosmosAcct -n $CosmosDBName | Out-Null; ok "DB creada" }
    if (-not $colOK -and $Apply) { az cosmosdb sql container create -g $RG -a $CosmosAcct -d $CosmosDBName -n $CosmosColl --partition-key-path $CosmosPK | Out-Null; ok "Container creado" }
  }

  # ---------- LOGIC APP: unificar MasterKey ----------
  info "`n[LOGIC APP] Forzando uso de una sola MasterKey en todas las ramas"
  # Toma la host key por defecto del host (funciona para todos los endpoints)
  $hostKeys = az rest --method post --uri "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$RG/providers/Microsoft.Web/sites/$Site/host/default/listKeys?api-version=2022-03-01" -o json | ConvertFrom-Json
  $unicaKey = $hostKeys.functionKeys.default
  if (-not $unicaKey) { warn "No pude leer host default key. Saltando reemplazo." }
  else {
    $defRaw = az resource show -g $RG --resource-type "Microsoft.Logic/workflows" -n $Workflow --api-version 2019-05-01 --query "properties.definition" -o json
    $def = $defRaw | ConvertFrom-Json

    $hits = @()
    function Patch-MasterKeys($node) {
      if ($null -eq $node) { return }
      if ($node.type -eq "SetVariable" -and $node.inputs -and $node.inputs.name -eq "MasterKey") {
        $node.inputs.value = $unicaKey; $script:hits += 1
      }
      foreach ($p in $node.PSObject.Properties) {
        $v = $p.Value
        if ($v -is [System.Collections.IDictionary] -or $v -is [System.Management.Automation.PSObject]) { Patch-MasterKeys $v }
        elseif ($v -is [System.Collections.IEnumerable]) { foreach ($i in $v) { Patch-MasterKeys $i } }
      }
    }
    Patch-MasterKeys $def
    if ($hits.Count -gt 0) {
      if ($Apply) {
        # Construye el payload como objeto y conviértelo a JSON para evitar problemas de comillas/parseo
        $payloadObj = @{
          properties = @{
            definition = $def
          }
        }
        # usa body desde archivo para evitar error de "línea demasiado larga"
        $tmp = Join-Path $PWD "logic_patch.json"
        $payloadObj | ConvertTo-Json -Depth 100 | Out-File $tmp -Encoding utf8
        az rest --method patch --uri "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$RG/providers/Microsoft.Logic/workflows/$Workflow?api-version=2019-05-01" --headers "Content-Type=application/json" --body @"$tmp" | Out-Null
        ok "Reemplazadas $($hits.Count) asignaciones de MasterKey por la host default key."
      }
      else {
        warn "Encontradas $($hits.Count) asignaciones MasterKey. Reemplazo simulado (ejecuta con -Apply)."
      }
    }
    else { ok "No se encontraron SetVariable de MasterKey (nada que unificar)." }
  }

  # ---------- PRUEBAS: Salud, Status, Ejecutar ----------
  info "`n[PRUEBAS] Endpoints de Function con key unificada"
  try {
    $h = Invoke-RestMethod "https://$Site.azurewebsites.net/api/health"
    if ($h.status -eq "healthy") { ok "Health OK" } else { warn "Health responde pero no 'healthy'" }
  }
  catch { warn "Health fallÃ³: $($_.Exception.Message)" }

  if ($unicaKey) {
    try {
      $s = Invoke-RestMethod "https://$Site.azurewebsites.net/api/status?code=$unicaKey"
      ok "Status 200"
    }
    catch { warn "Status 401/403: revisa MasterKey en Logic App/Function." }

    try {
      $body = @{ intencion = "dashboard"; modo = "normal"; parametros = @{} } | ConvertTo-Json
      $e = Invoke-RestMethod -Uri "https://$Site.azurewebsites.net/api/ejecutar?code=$unicaKey" -Method POST -Body $body -ContentType "application/json"
      ok "Ejecutar 200"
    }
    catch { warn "Ejecutar fallÃ³: $($_.Exception.Message)" }
  }

  # ---------- I/O de contexto (Blob & Cosmos prueba) ----------
  info "`n[PRUEBA CONTEXTO] Blob JSON de ida y vuelta"
  $storKey = az storage account keys list -g $RG -n $StorageAcct --query [0].value -o tsv
  $probeName = "$BlobPrefix/prueba-$(Get-Date -Format yyyyMMdd-HHmmss).json"
  $payload = @{ origen = "supervisor"; ts = (Get-Date).ToString("s"); nota = "prueba de escritura/lectura" } | ConvertTo-Json
  az storage blob upload --account-name $StorageAcct --account-key $storKey --container-name $BlobContainer --name $probeName --content-type "application/json" --data $payload --overwrite | Out-Null
  $readBack = az storage blob download --account-name $StorageAcct --account-key $storKey --container-name $BlobContainer --name $probeName --file "-" | ConvertFrom-Json
  if ($readBack.nota -eq "prueba de escritura/lectura") { ok "Blob R/W OK: $probeName" } else { warn "Blob R/W: verifique" }

  if ($cosmosOK) {
    info "[PRUEBA CONTEXTO] Cosmos (si RBAC data-plane habilitado podrÃ­as requerir token/SDK; aquÃ­ sÃ³lo valida existencia)"
    ok "Cosmos listo para integraciÃ³n desde cÃ³digo del Copiloto (SDK/conn)."
  }

  ok "`nâœ… PREPARACIÃ“N COMPLETA (modo $([string]::IsNullOrEmpty($Apply) ? 'VALIDATE' : 'APPLY'))"

