# sync_to_blob.ps1
# Script para sincronizar tu proyecto con Azure Blob Storage

param(
  [string]$ResourceGroup = "boat-rental-app-group",
  [string]$StorageAccount = "boatrentalstorage",
  [string]$Container = "boat-rental-project",
  [string]$ProjectPath = "C:\ProyectosSimbolicos\boat-rental-app"
)

Write-Host "🚀 Sincronización con Azure Blob Storage" -ForegroundColor Cyan

# 1. Crear Storage Account si no existe
Write-Host "`n1️⃣ Verificando Storage Account..." -ForegroundColor Yellow
$storageExists = az storage account show `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --query "name" -o tsv 2>$null

if (-not $storageExists) {
  Write-Host "   Creando Storage Account..." -ForegroundColor Green
  az storage account create `
    --name $StorageAccount `
    --resource-group $ResourceGroup `
    --location eastus `
    --sku Standard_LRS `
    --kind StorageV2
}

# 2. Obtener connection string
Write-Host "`n2️⃣ Obteniendo connection string..." -ForegroundColor Yellow
$connectionString = az storage account show-connection-string `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --query "connectionString" -o tsv

# 3. Crear container si no existe
Write-Host "`n3️⃣ Verificando container..." -ForegroundColor Yellow
$containerExists = az storage container exists `
  --name $Container `
  --connection-string $connectionString `
  --query "exists" -o tsv

if ($containerExists -eq "false") {
  Write-Host "   Creando container..." -ForegroundColor Green
  az storage container create `
    --name $Container `
    --connection-string $connectionString `
    --public-access off
}

# 4. Sincronizar archivos
Write-Host "`n4️⃣ Sincronizando archivos del proyecto..." -ForegroundColor Yellow

# Lista de extensiones a sincronizar
$extensions = @("*.py", "*.js", "*.ts", "*.tsx", "*.json", "*.yaml", "*.yml", "*.md", "*.txt", "*.env", "*.config")

# Función para subir archivos
function Upload-ToBlob {
  param($LocalPath, $BlobPath)
    
  az storage blob upload `
    --container-name $Container `
    --file $LocalPath `
    --name $BlobPath `
    --connection-string $connectionString `
    --overwrite 2>$null
}

# Contador de archivos
$totalFiles = 0
$uploadedFiles = 0

# Recorrer y subir archivos
foreach ($ext in $extensions) {
  $files = Get-ChildItem -Path $ProjectPath -Filter $ext -Recurse -File | 
  Where-Object { $_.FullName -notmatch "node_modules|\.venv|\.git" }
    
  foreach ($file in $files) {
    $totalFiles++
    $relativePath = $file.FullName.Replace("$ProjectPath\", "").Replace("\", "/")
        
    Write-Host "   Subiendo: $relativePath" -ForegroundColor Gray
    Upload-ToBlob -LocalPath $file.FullName -BlobPath $relativePath
    $uploadedFiles++
        
    # Mostrar progreso cada 10 archivos
    if ($uploadedFiles % 10 -eq 0) {
      Write-Host "   ✅ $uploadedFiles archivos sincronizados..." -ForegroundColor Green
    }
  }
}

# 5. Configurar la Function App con el connection string
Write-Host "`n5️⃣ Configurando Function App..." -ForegroundColor Yellow
az functionapp config appsettings set `
  --name "copiloto-semantico-func" `
  --resource-group $ResourceGroup `
  --settings "AZURE_STORAGE_CONNECTION_STRING=$connectionString"

# 6. Resumen
Write-Host "`n✅ SINCRONIZACIÓN COMPLETA" -ForegroundColor Green
Write-Host "📊 Resumen:" -ForegroundColor Cyan
Write-Host "   - Total archivos: $totalFiles"
Write-Host "   - Archivos subidos: $uploadedFiles"
Write-Host "   - Storage Account: $StorageAccount"
Write-Host "   - Container: $Container"
Write-Host "   - Connection String configurado en Function App"

# 7. Crear archivo de configuración local
$configPath = "$ProjectPath\copiloto-function\blob_config.json"
$config = @{
  StorageAccount   = $StorageAccount
  Container        = $Container
  ConnectionString = $connectionString
  LastSync         = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  FilesSynced      = $uploadedFiles
} | ConvertTo-Json -Depth 5

$config | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "`n📄 Configuración guardada en: $configPath" -ForegroundColor Yellow

Write-Host "`n🎯 Próximos pasos:" -ForegroundColor Magenta
Write-Host "   1. Actualiza function_app.py con la versión de Blob Storage"
Write-Host "   2. Publica la función: func azure functionapp publish copiloto-semantico-func"
Write-Host "   3. Prueba con: leer:mobile-app/package.json"