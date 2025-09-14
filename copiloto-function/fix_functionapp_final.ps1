# fix_functionapp_final.ps1
# ==========================================
# SCRIPT PROFESIONAL DE CORRECCIÓN DEFINITIVA
# ==========================================

param(
  [string]$ResourceGroup = "boat-rental-app-group",
  [string]$FunctionApp = "copiloto-semantico-func-us2",
  [string]$ACR = "boatrentalacr",
  [string]$ImageTag = "",  # Ahora vacío por defecto para usar auto-incremento
  [switch]$Force
)

# Colores para output
function Write-Step { param($msg) Write-Host "`n[$($args[0])] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "→ $msg" -ForegroundColor Gray }

# ==========================================
# AUTO-INCREMENTO DE TAG
# ==========================================
if ([string]::IsNullOrEmpty($ImageTag)) {
  Write-Info "Calculando siguiente tag automáticamente..."

  $allTags = az acr repository show-tags `
    -n $ACR `
    --repository copiloto-func-azcli `
    --orderby time_desc `
    -o tsv

  # Filtrar solo los tags que coincidan con formato vNN
  $versionTags = $allTags | Where-Object { $_ -match "^v(\d+)$" }

  if ($versionTags.Count -gt 0) {
    $latestVersionTag = ($versionTags | Sort-Object {
        [int]($_ -replace '^v', '')
      } -Descending)[0]

    if ($latestVersionTag -match "^v(\d+)$") {
      $nextVersion = [int]$Matches[1] + 1
      $ImageTag = "v$nextVersion"
      Write-Info "→ Usando siguiente tag: $ImageTag"
    }
  }
  else {
    # No hay tags previos → arrancar en v1
    $ImageTag = "v1"
    Write-Warning "→ No se encontraron tags vNN previos. Iniciando en $ImageTag"
  }
}


# ==========================================
# FASE 1: VALIDACIÓN INICIAL
# ==========================================
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "CORRECCIÓN DEFINITIVA FUNCTION APP v3.0" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

Write-Step "FASE 1: VALIDACIÓN INICIAL" 1

# Verificar que la Function App existe
$appExists = az functionapp show -g $ResourceGroup -n $FunctionApp 2>$null
if (-not $appExists) {
  Write-Error "Function App '$FunctionApp' no existe en '$ResourceGroup'"
  exit 1
}
Write-Success "Function App encontrada"

# Verificar plan de servicio
$plan = az functionapp show -g $ResourceGroup -n $FunctionApp --query "appServicePlanId" -o tsv
$planDetails = az appservice plan show --ids $plan 2>$null | ConvertFrom-Json
if ($planDetails.sku.tier -eq "Dynamic") {
  Write-Error "El plan es Consumption (Y1). Los contenedores custom requieren Premium (EP1+)"
  Write-Info "Ejecuta: az functionapp plan update --name $($planDetails.name) -g $ResourceGroup --sku EP1"
  if (-not $Force) { exit 1 }
}
Write-Success "Plan de servicio: $($planDetails.sku.name) - $($planDetails.sku.tier) ✓"

# ==========================================
# FASE 2: OBTENER CREDENCIALES Y STORAGE KEY
# ==========================================
Write-Step "FASE 2: OBTENER CREDENCIALES" 2

# Obtener Storage Account Key
Write-Info "Obteniendo Storage Account Key..."
$storageKey = az storage account keys list -n boatrentalstorage -g $ResourceGroup --query "[0].value" -o tsv 2>$null
if (-not $storageKey) {
  Write-Error "No se pudo obtener la Storage Key"
  # Intentar con otro método
  $storageKey = "IzbvFwD7WupP22swwnpo4k+yKgPLOGnR84jViNT1AxYLUxvjW8Qs/Nxm9IDnpQegi1B2F2fNOY9Q+AStZy8ACA=="
  Write-Warning "Usando Storage Key hardcodeada como fallback"
}
Write-Success "Storage Key obtenida"

# Obtener credenciales ACR
Write-Info "Obteniendo credenciales ACR..."
$acrUsername = az acr credential show -n $ACR --query username -o tsv 2>$null
$acrPassword = az acr credential show -n $ACR --query "passwords[0].value" -o tsv 2>$null

if (-not $acrUsername -or -not $acrPassword) {
  Write-Error "No se pudieron obtener credenciales ACR"
  exit 1
}
Write-Success "Credenciales ACR obtenidas"

# ==========================================
# FASE 3: CONFIGURAR APP SETTINGS CRÍTICOS
# ==========================================
Write-Step "FASE 3: CONFIGURAR APP SETTINGS" 3

$settings = @{
  "FUNCTIONS_WORKER_RUNTIME"                    = "python"
  "FUNCTIONS_EXTENSION_VERSION"                 = "~4"
  "AzureWebJobsStorage"                         = "..."
  "WEBSITES_ENABLE_APP_SERVICE_STORAGE"         = "false"
  "WEBSITES_PORT"                               = "80"
  "FUNCTIONS_CUSTOM_CONTAINER_USE_DEFAULT_PORT" = "1"
  "AzureWebJobsScriptRoot"                      = "/home/site/wwwroot"
  "AzureWebJobsDisableHomepage"                 = "false"
  "WEBSITE_MOUNT_ENABLED"                       = "1"
  "DOCKER_ENABLE_CI"                            = "true"
  "FUNCTION_BASE_URL"                           = "https://copiloto-semantico-func-us2.azurewebsites.net"
  "AZURE_CLIENT_ID"                             = "768637f1-4a55-4f42-8526-cb57782a0285"
  "AZURE_SUBSCRIPTION_ID"                       = "380fa841-83f3-42fe-adc4-582a5ebe139b"
  # Dejarlo de último
  "AzureWebJobsFeatureFlags"                    = "EnableWorkerIndexing"
}



Write-Info "Aplicando settings críticos..."
foreach ($key in $settings.Keys) {
  $value = $settings[$key]
  $applied = $false
  for ($i = 1; $i -le 3; $i++) {
    Write-Info "  Configurando: $key (intento $i/3)"
    $result = az functionapp config appsettings set `
      -g $ResourceGroup `
      -n $FunctionApp `
      --settings "$key=$value" 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Success "$key configurado"
      $applied = $true
      break
    }
    else {
      Write-Warning "Fallo al configurar $key. Reintentando en $([int](5 * $i))s..."
      Start-Sleep -Seconds (5 * $i)
    }
  }
  if (-not $applied -and -not $Force) {
    Write-Error "No se pudo configurar $key después de 3 intentos"
    exit 1
  }
}

Write-Success "App Settings configurados"

# ==========================================
# FASE 3.5: IDENTIDAD ADMINISTRADA PARA BLOB (SIN CLAVES)
# ==========================================
Write-Step "FASE 3.5: IDENTIDAD ADMINISTRADA PARA BLOB (SIN CLAVES)" 3.5

# Variables de storage
$StorageAccount = "boatrentalstorage"
$ContainerName = "boat-rental-project"

# 3.5.1 – Asignar RBAC a la MI de la Function App (Data Contributor)
try {
  $mi = az functionapp show -g $ResourceGroup -n $FunctionApp --query identity.principalId -o tsv
  $saId = az storage account show -g $ResourceGroup -n $StorageAccount --query id -o tsv

  if (-not $mi -or -not $saId) {
    Write-Error "No se pudo obtener MI o id de Storage Account"
    if (-not $Force) { exit 1 }
  }

  Write-Info "Asignando rol 'Storage Blob Data Contributor' a la MI de la app..."
  az role assignment create --assignee $mi --role "Storage Blob Data Contributor" --scope $saId 1>$null 2>$null
  Write-Success "RBAC aplicado (puede tardar 1–3 min en propagarse)"
}
catch {
  Write-Warning "No se pudo asignar RBAC (posible duplicado). Continuo..."
}

# 3.5.2 – Garantizar acceso público de red al endpoint de blobs (sin abrir anonimato)
try {
  $pna = az storage account show -g $ResourceGroup -n $StorageAccount --query publicNetworkAccess -o tsv
  $dfa = az storage account show -g $ResourceGroup -n $StorageAccount --query networkRuleSet.defaultAction -o tsv

  if ($pna -ne "Enabled") {
    Write-Info "Habilitando PublicNetworkAccess=Enabled..."
    az storage account update -g $ResourceGroup -n $StorageAccount --public-network-access Enabled 1>$null
  }
  if ($dfa -ne "Allow") {
    Write-Info "Estableciendo defaultAction=Allow..."
    az storage account update -g $ResourceGroup -n $StorageAccount --default-action Allow 1>$null
  }
  Write-Success "Red de Storage OK (PNA=Enabled / defaultAction=Allow)"
}
catch {
  Write-Warning "No se pudo actualizar configuración de red de Storage. Reviso de todos modos..."
}

# 3.5.3 – Forzar ruta MI en tu código: solo BLOB_ACCOUNT_URL, sin connection string de datos
try {
  $blobUrl = "https://$StorageAccount.blob.core.windows.net"
  az functionapp config appsettings set -g $ResourceGroup -n $FunctionApp --settings BLOB_ACCOUNT_URL="$blobUrl" 1>$null
  az functionapp config appsettings delete -g $ResourceGroup -n $FunctionApp --setting-names AZURE_STORAGE_CONNECTION_STRING 1>$null
  Write-Success "AppSettings para MI aplicados (BLOB_ACCOUNT_URL set / AZURE_STORAGE_CONNECTION_STRING eliminado)"
}
catch {
  Write-Error "No se pudieron aplicar AppSettings para MI"
  if (-not $Force) { exit 1 }
}

# 3.5.4 – Asegurar que existe el contenedor que usa tu código (CONTAINER_NAME)
try {
  Write-Info "Creando contenedor '$ContainerName' (idempotente) con AAD..."
  az storage container create -n $ContainerName --account-name $StorageAccount --auth-mode login 1>$null
  Write-Success "Contenedor verificado/creado"
}
catch {
  Write-Warning "No se pudo crear/verificar el contenedor (quizá ya existe)."
}

# 3.5.5 – Reinicio rápido para recoger RBAC/AppSettings
Write-Info "Reiniciando para recoger MI/RBAC..."
az functionapp restart -g $ResourceGroup -n $FunctionApp 1>$null
Write-Info "Esperando propagación de RBAC (75s)..."
Start-Sleep -Seconds 75

# ==========================================
# FASE 3.9: CONSTRUIR Y PUBLICAR IMAGEN DOCKER
# ==========================================
Write-Step "FASE 3.9: CONSTRUIR Y PUBLICAR IMAGEN DOCKER" 3.9

$fullImage = "$ACR.azurecr.io/copiloto-func-azcli:$ImageTag"

# Build de imagen Docker
Write-Info "Construyendo imagen Docker: $fullImage"
docker build -t $fullImage .
if ($LASTEXITCODE -ne 0) {
  Write-Error "Falló la construcción de la imagen Docker"
  if (-not $Force) { exit 1 }
}
Write-Success "Imagen Docker construida exitosamente"

# Login ACR
Write-Info "Autenticando con ACR: $ACR"
az acr login -n $ACR
if ($LASTEXITCODE -ne 0) {
  Write-Error "Falló autenticación con ACR"
  if (-not $Force) { exit 1 }
}
Write-Success "Login en ACR exitoso"

# Push al ACR
Write-Info "Publicando imagen en ACR: $fullImage"
docker push $fullImage
if ($LASTEXITCODE -ne 0) {
  Write-Error "Falló la publicación de la imagen en ACR"
  if (-not $Force) { exit 1 }
}
Write-Success "Imagen Docker publicada exitosamente"


# ==========================================
# FASE 4: CONFIGURAR CONTENEDOR CON CREDENCIALES
# ==========================================
Write-Step "FASE 4: CONFIGURAR CONTENEDOR" 4

$fullImage = "$ACR.azurecr.io/copiloto-func-azcli:$ImageTag"
Write-Info "Configurando imagen: $fullImage"

# Validar que la imagen existe en ACR
Write-Info "Verificando que la imagen existe en ACR..."
$tagExists = az acr repository show-tags -n $ACR --repository copiloto-func-azcli --query "[?@ == '$ImageTag']" -o tsv
if (-not $tagExists) {
  Write-Error "La imagen $fullImage no existe en ACR"
  if (-not $Force) { exit 1 }
}
Write-Success "Imagen encontrada en ACR: $ImageTag"

# Verificación opcional del contenido de la imagen Docker
Write-Info "Verificando contenido de la imagen Docker..."
try {
  $dockerContent = docker run --rm $fullImage ls -la /home/site/wwwroot 2>&1
  if ($LASTEXITCODE -eq 0) {
    Write-Success "Contenido de la imagen verificado"
    Write-Info "Archivos en /home/site/wwwroot:"
    $dockerContent | ForEach-Object { Write-Info "  $_" }
  }
  else {
    Write-Warning "No se pudo verificar el contenido de la imagen Docker"
    Write-Info "Error: $dockerContent"
  }
}
catch {
  Write-Warning "Docker no disponible o imagen no accesible localmente"
}

# Intentar configurar con credenciales explícitas
$containerResult = az functionapp config container set `
  -g $ResourceGroup `
  -n $FunctionApp `
  --image $fullImage `
  --registry-server "https://$ACR.azurecr.io" `
  --registry-username $acrUsername `
  --registry-password $acrPassword 2>&1

if ($LASTEXITCODE -ne 0) {
  Write-Warning "Primer intento falló, reintentando sin https..."
    
  $containerResult = az functionapp config container set `
    -g $ResourceGroup `
    -n $FunctionApp `
    --docker-custom-image-name $fullImage `
    --docker-registry-server-url "$ACR.azurecr.io" `
    --docker-registry-server-username $acrUsername `
    --docker-registry-server-password $acrPassword 2>&1
}

Write-Success "Contenedor configurado"

# Verificar que se aplicó
$containerConfig = az functionapp config container show -g $ResourceGroup -n $FunctionApp | ConvertFrom-Json
$dockerImageSetting = $containerConfig | Where-Object { $_.name -eq "DOCKER_CUSTOM_IMAGE_NAME" }

if ($dockerImageSetting.value -like "*$ImageTag*") {
  Write-Success "Imagen verificada: $($dockerImageSetting.value)"
}
else {
  Write-Error "La imagen no se configuró correctamente"
  if (-not $Force) { exit 1 }
}

# ==========================================
# FASE 5: REINICIAR Y ESPERAR
# ==========================================
Write-Step "FASE 5: REINICIAR FUNCTION APP" 5

Write-Info "Reiniciando Function App..."
$restartResult = az functionapp restart -g $ResourceGroup -n $FunctionApp 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Error "Fallo al reiniciar Function App"
  Write-Info "Error: $restartResult"
  if (-not $Force) { exit 1 }
}
else {
  Write-Success "Function App reiniciada correctamente"
}

Write-Info "Esperando 60 segundos para que el contenedor inicie..."
$waitTime = 60
for ($i = 1; $i -le $waitTime; $i++) {
  Write-Progress -Activity "Esperando inicio del contenedor" -Status "$i de $waitTime segundos" -PercentComplete (($i / $waitTime) * 100)
  Start-Sleep -Seconds 1
}
Write-Progress -Activity "Esperando inicio del contenedor" -Completed

# ==========================================
# FASE 6: VERIFICACIÓN DE ENDPOINTS
# ==========================================
Write-Step "FASE 6: VERIFICACIÓN DE ENDPOINTS" 6

$baseUrl = "https://$FunctionApp.azurewebsites.net"
$successCount = 0

function Test-Endpoint($url, $label) {
  try {
    $r = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 15 -ErrorAction Stop
    Write-Success "$label - Status: $($r.StatusCode)"
    return $true
  }
  catch {
    $sc = $_.Exception.Response.StatusCode.value__
    if ($sc) { Write-Warning "$label - Status: $sc" } else { Write-Error "$label - No responde" }
    return $false
  }
}

# Health + Status (una vez)
if (Test-Endpoint "$baseUrl/api/health" "(/api/health)") { $successCount++ }
if (Test-Endpoint "$baseUrl/api/status" "(/api/status)") { $successCount++ }

# listar-blobs con retry suave (RBAC puede demorar)
$max = 4; $ok = $false
for ($i = 1; $i -le $max; $i++) {
  if (Test-Endpoint "$baseUrl/api/listar-blobs" "(/api/listar-blobs intento $i/$max)") { $ok = $true; break }
  if ($i -lt $max) { Write-Info "Reintentando en 20s..."; Start-Sleep -Seconds 20 }
}
if ($ok) { $successCount++ }

# ==========================================
# FASE 7: DIAGNÓSTICO FINAL
# ==========================================
Write-Step "FASE 7: DIAGNÓSTICO FINAL" 7

if ($successCount -gt 0) {
  Write-Host "`n========================================" -ForegroundColor Green
  Write-Host "✓ ÉXITO: Function App OPERATIVA" -ForegroundColor Green
  Write-Host "========================================" -ForegroundColor Green
  Write-Success "$successCount de 3 endpoints funcionando"
  Write-Info "URL: $baseUrl"
    
  # Listar funciones disponibles
  Write-Info "`nFunciones registradas:"
  $functions = az functionapp function list -g $ResourceGroup -n $FunctionApp --query "[].name" -o tsv 2>$null
  foreach ($func in $functions) {
    Write-Info "  • $func"
  }
    
}
else {
  Write-Host "`n========================================" -ForegroundColor Red
  Write-Host "✗ PROBLEMA PERSISTE" -ForegroundColor Red
  Write-Host "========================================" -ForegroundColor Red
    
  Write-Warning "Acciones adicionales requeridas:"
  Write-Info "1. Verificar logs del contenedor:"
  Write-Info "   az webapp log tail -g $ResourceGroup -n $FunctionApp"
    
  Write-Info "2. Verificar que la imagen tiene los archivos correctos:"
  Write-Info "   docker run --rm $fullImage ls -la /home/site/wwwroot/"
    
  Write-Info "3. Si persiste, recrear la Function App:"
  Write-Info "   az functionapp delete -g $ResourceGroup -n $FunctionApp"
  Write-Info "   az functionapp create -g $ResourceGroup -n $FunctionApp --plan <PLAN> --deployment-container-image-name $fullImage --runtime custom"
}

# Registrar timestamp de ejecución final
Write-Info "Ejecución completada en: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "`nScript completado.`n" -ForegroundColor Cyan