# Validador Automatico de Configuracion Azure Functions
# Analiza app settings y detecta inconsistencias que pueden causar syncfunctiontriggers failures

param(
    [string]$FunctionAppName = "copiloto-semantico-func-us2",
    [string]$ResourceGroup = "boat-rental-app-group"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VALIDADOR DE CONFIGURACION AZURE FUNCTIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "App: $FunctionAppName" -ForegroundColor Yellow
Write-Host "RG: $ResourceGroup" -ForegroundColor Yellow
Write-Host ""

# Obtener configuracion actual
Write-Host "-> Obteniendo app settings..." -ForegroundColor Green
$appSettings = az functionapp config appsettings list --name $FunctionAppName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json

if (-not $appSettings) {
    Write-Host "[ERROR] No se pudieron obtener los app settings" -ForegroundColor Red
    exit 1
}

Write-Host "-> Configuracion obtenida: $($appSettings.Count) variables" -ForegroundColor Green
Write-Host ""

# Crear hashtable para busqueda rapida
$settings = @{}
foreach ($setting in $appSettings) {
    $settings[$setting.name] = $setting.value
}

# Resultados de validacion
$validationResults = @()

# Funcion helper para agregar resultado
function Add-ValidationResult {
    param($Category, $Setting, $CurrentValue, $Status, $Recommendation, $Impact)
    
    $script:validationResults += [PSCustomObject]@{
        Category       = $Category
        Setting        = $Setting
        CurrentValue   = $CurrentValue
        Status         = $Status
        Recommendation = $Recommendation
        Impact         = $Impact
    }
}

Write-Host "VALIDANDO CONFIGURACION..." -ForegroundColor Cyan
Write-Host ""

# 1. VALIDACION CONTENEDOR CUSTOM
Write-Host "1. CONTENEDOR CUSTOM" -ForegroundColor Yellow

$dockerUrl = $settings["DOCKER_REGISTRY_SERVER_URL"]
$dockerUsername = $settings["DOCKER_REGISTRY_SERVER_USERNAME"] 
$dockerPassword = $settings["DOCKER_REGISTRY_SERVER_PASSWORD"]

if ($dockerUrl -and $dockerUsername) {
    Add-ValidationResult "CONTENEDOR" "DOCKER_REGISTRY_*" "Configurado" "OK" "Contenedor custom detectado" "CRITICO"
    $isCustomContainer = $true
}
else {
    Add-ValidationResult "CONTENEDOR" "DOCKER_REGISTRY_*" "No configurado" "WARNING" "Parece ser deployment ZIP, no contenedor" "INFO"
    $isCustomContainer = $false
}

# 2. VALIDACION STORAGE Y MOUNT
Write-Host "2. STORAGE Y MOUNT" -ForegroundColor Yellow

$enableStorage = $settings["WEBSITES_ENABLE_APP_SERVICE_STORAGE"]
$mountEnabled = $settings["WEBSITE_MOUNT_ENABLED"] 
$scriptRoot = $settings["AzureWebJobsScriptRoot"]

# Logica de validacion segun tipo de deployment
if ($isCustomContainer) {
    # Para contenedor custom
    if ($enableStorage -eq "true") {
        Add-ValidationResult "STORAGE" "WEBSITES_ENABLE_APP_SERVICE_STORAGE" $enableStorage "WARNING" "Para contenedor custom, considerar 'false' si codigo esta en imagen" "ALTO"
    }
    else {
        Add-ValidationResult "STORAGE" "WEBSITES_ENABLE_APP_SERVICE_STORAGE" $enableStorage "OK" "Coherente con contenedor custom" "MEDIO"
    }
    
    if ($mountEnabled -eq "false" -or -not $mountEnabled) {
        Add-ValidationResult "STORAGE" "WEBSITE_MOUNT_ENABLED" $mountEnabled "OK" "Coherente con contenedor" "BAJO"
    }
    else {
        Add-ValidationResult "STORAGE" "WEBSITE_MOUNT_ENABLED" $mountEnabled "WARNING" "Puede causar conflictos con contenedor" "MEDIO"
    }
}
else {
    # Para ZIP deployment
    if ($enableStorage -eq "true") {
        Add-ValidationResult "STORAGE" "WEBSITES_ENABLE_APP_SERVICE_STORAGE" $enableStorage "OK" "Coherente con ZIP deployment" "MEDIO"
    }
    else {
        Add-ValidationResult "STORAGE" "WEBSITES_ENABLE_APP_SERVICE_STORAGE" $enableStorage "ERROR" "ZIP deployment requiere storage=true" "CRITICO"
    }
}

# 3. VALIDACION PATHS Y RUNTIME
Write-Host "3. PATHS Y RUNTIME" -ForegroundColor Yellow

$functionsVersion = $settings["FUNCTIONS_EXTENSION_VERSION"]
$workerRuntime = $settings["FUNCTIONS_WORKER_RUNTIME"]
$projectRoot = $settings["PROJECT_ROOT"]

if ($scriptRoot) {
    if ($scriptRoot -eq "/home/site/wwwroot") {
        Add-ValidationResult "PATHS" "AzureWebJobsScriptRoot" $scriptRoot "OK" "Path estandar de Azure Functions" "BAJO"
    }
    else {
        Add-ValidationResult "PATHS" "AzureWebJobsScriptRoot" $scriptRoot "WARNING" "Path no estandar, verificar que existe en contenedor" "MEDIO"
    }
}
else {
    Add-ValidationResult "PATHS" "AzureWebJobsScriptRoot" "No definido" "ERROR" "Debe estar definido" "ALTO"
}

if ($workerRuntime -eq "python") {
    Add-ValidationResult "RUNTIME" "FUNCTIONS_WORKER_RUNTIME" $workerRuntime "OK" "Python runtime configurado" "BAJO"
}
else {
    Add-ValidationResult "RUNTIME" "FUNCTIONS_WORKER_RUNTIME" $workerRuntime "ERROR" "Debe ser 'python'" "CRITICO"
}

# 4. VALIDACION BUILD Y DEPLOYMENT
Write-Host "4. BUILD Y DEPLOYMENT" -ForegroundColor Yellow

$scmBuild = $settings["SCM_DO_BUILD_DURING_DEPLOYMENT"]
$enableOryx = $settings["ENABLE_ORYX_BUILD"] 
$dockerCI = $settings["DOCKER_ENABLE_CI"]

if ($isCustomContainer) {
    # Para contenedor, build flags son irrelevantes
    if ($scmBuild -eq "true" -or $enableOryx -eq "true") {
        Add-ValidationResult "BUILD" "BUILD_FLAGS" "Habilitado" "WARNING" "Para contenedor custom, build flags son innecesarios" "BAJO"
    }
    else {
        Add-ValidationResult "BUILD" "BUILD_FLAGS" "Deshabilitado" "OK" "Coherente con contenedor custom" "BAJO"  
    }
}
else {
    # Para ZIP, pueden ser utiles
    Add-ValidationResult "BUILD" "BUILD_FLAGS" "Configurado" "INFO" "Build flags para ZIP deployment" "BAJO"
}

# 5. VALIDACION SERVICIOS EXTERNOS
Write-Host "5. SERVICIOS EXTERNOS" -ForegroundColor Yellow

# Cosmos DB
$cosmosEndpoint = $settings["COSMOSDB_ENDPOINT"]
$cosmosDb = $settings["COSMOSDB_DATABASE"] 
$cosmosContainer = $settings["COSMOSDB_CONTAINER"]

if ($cosmosEndpoint -and $cosmosDb -and $cosmosContainer) {
    Add-ValidationResult "SERVICIOS" "COSMOS_DB" "Configurado" "OK" "Cosmos DB configurado correctamente" "MEDIO"
}
else {
    Add-ValidationResult "SERVICIOS" "COSMOS_DB" "Incompleto" "ERROR" "Falta configuracion de Cosmos DB" "ALTO"
}

# Azure OpenAI
$openaiEndpoint = $settings["AZURE_OPENAI_ENDPOINT"]
$openaiKey = $settings["AZURE_OPENAI_KEY"]
$openaiDeployment = $settings["AZURE_OPENAI_DEPLOYMENT_NAME"]

if ($openaiEndpoint -and $openaiKey -and $openaiDeployment) {
    Add-ValidationResult "SERVICIOS" "AZURE_OPENAI" "Configurado" "OK" "Azure OpenAI configurado" "MEDIO"
}
else {
    Add-ValidationResult "SERVICIOS" "AZURE_OPENAI" "Incompleto" "WARNING" "Configuracion OpenAI incompleta" "MEDIO"
}

# Redis
$redisHost = $settings["REDIS_HOST"]
$redisKey = $settings["REDIS_KEY"]

if ($redisHost -and ($redisKey -or $settings["REDIS_USE_MANAGED_IDENTITY"] -eq "true")) {
    Add-ValidationResult "SERVICIOS" "REDIS" "Configurado" "OK" "Redis configurado correctamente" "BAJO"
}
else {
    Add-ValidationResult "SERVICIOS" "REDIS" "Incompleto" "WARNING" "Configuracion Redis incompleta" "BAJO"
}

# Storage
$storageConnection = $settings["AzureWebJobsStorage"]
if ($storageConnection -and $storageConnection -ne "UseDevelopmentStorage=true") {
    Add-ValidationResult "SERVICIOS" "AZURE_STORAGE" "Configurado" "OK" "Storage account configurado" "CRITICO"
}
else {
    Add-ValidationResult "SERVICIOS" "AZURE_STORAGE" "Incompleto" "ERROR" "Storage account requerido" "CRITICO"
}

# 6. VALIDACION DOCKERFILE
Write-Host "6. DOCKERFILE Y CONTENEDOR" -ForegroundColor Yellow

if (Test-Path "Dockerfile") {
    $dockerfileContent = Get-Content "Dockerfile" -Raw
    
    # Verificar si copia código a /home/site/wwwroot
    if ($dockerfileContent -match "COPY.*?/home/site/wwwroot") {
        Add-ValidationResult "DOCKERFILE" "COPY_TO_WWWROOT" "Detectado" "OK" "Código copiado a /home/site/wwwroot en build" "MEDIO"
        $hasCodeInImage = $true
    }
    else {
        Add-ValidationResult "DOCKERFILE" "COPY_TO_WWWROOT" "No detectado" "WARNING" "No se copia código a wwwroot, dependes de storage mount" "ALTO"
        $hasCodeInImage = $false
    }
    
    # Verificar ENTRYPOINT/CMD
    $entrypoint = ""
    if ($dockerfileContent -match 'ENTRYPOINT\s*\[(.*?)\]') {
        $entrypoint = $matches[1]
    }
    elseif ($dockerfileContent -match 'CMD\s*\[(.*?)\]') {
        $entrypoint = $matches[1]
    }
    elseif ($dockerfileContent -match 'CMD\s+(.+)') {
        $entrypoint = $matches[1]
    }
    
    if ($entrypoint) {
        Add-ValidationResult "DOCKERFILE" "ENTRYPOINT_CMD" $entrypoint.Substring(0, [Math]::Min(50, $entrypoint.Length)) "OK" "Comando de inicio definido" "BAJO"
    }
    else {
        Add-ValidationResult "DOCKERFILE" "ENTRYPOINT_CMD" "No detectado" "WARNING" "No hay comando de inicio explícito" "MEDIO"
    }
    
    # Verificar coherencia con WEBSITES_ENABLE_APP_SERVICE_STORAGE
    if ($enableStorage -eq "true" -and -not $hasCodeInImage) {
        Add-ValidationResult "COHERENCIA" "STORAGE_VS_IMAGE" "Incoherente" "ERROR" "STORAGE=true pero código no está en imagen, runtime quedará vacío" "CRITICO"
    }
    elseif ($enableStorage -eq "false" -and $hasCodeInImage) {
        Add-ValidationResult "COHERENCIA" "STORAGE_VS_IMAGE" "Coherente" "OK" "STORAGE=false y código en imagen es coherente" "BAJO"
    }
    
}
else {
    Add-ValidationResult "DOCKERFILE" "ARCHIVO" "No encontrado" "INFO" "No hay Dockerfile en directorio actual" "BAJO"
}

# 7. VALIDACION HOST.JSON
Write-Host "7. HOST.JSON" -ForegroundColor Yellow

if (Test-Path "host.json") {
    try {
        $hostJson = Get-Content "host.json" -Raw | ConvertFrom-Json
        
        # Verificar version
        if ($hostJson.version -eq "2.0") {
            Add-ValidationResult "HOST_JSON" "VERSION" "2.0" "OK" "Versión correcta" "MEDIO"
        }
        else {
            Add-ValidationResult "HOST_JSON" "VERSION" $hostJson.version "WARNING" "Versión no estándar, debería ser 2.0" "MEDIO"
        }
        
        # Verificar logging
        if ($hostJson.logging) {
            Add-ValidationResult "HOST_JSON" "LOGGING" "Configurado" "OK" "Logging configurado" "BAJO"
        }
        else {
            Add-ValidationResult "HOST_JSON" "LOGGING" "No configurado" "WARNING" "Sin configuración de logging explícita" "BAJO"
        }
        
        # Verificar extensions
        if ($hostJson.extensions -and $hostJson.extensions.http) {
            $routePrefix = $hostJson.extensions.http.routePrefix
            if ($routePrefix -eq "" -or $routePrefix -eq $null) {
                Add-ValidationResult "HOST_JSON" "ROUTE_PREFIX" "Vacío/null" "OK" "Sin prefijo de ruta (functions en root)" "BAJO"
            }
            else {
                Add-ValidationResult "HOST_JSON" "ROUTE_PREFIX" $routePrefix "INFO" "Prefijo de ruta personalizado: $routePrefix" "BAJO"
            }
        }
        
    }
    catch {
        Add-ValidationResult "HOST_JSON" "PARSING" "Error" "ERROR" "Archivo host.json corrupto o JSON inválido: $($_.Exception.Message)" "ALTO"
    }
}
else {
    Add-ValidationResult "HOST_JSON" "ARCHIVO" "No encontrado" "ERROR" "Archivo host.json requerido no encontrado" "CRITICO"
}

# 8. VALIDACION ARCHIVOS PYTHON CRITICOS
Write-Host "8. ARCHIVOS PYTHON" -ForegroundColor Yellow

$criticalFiles = @("function_app.py", "requirements.txt")
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Add-ValidationResult "ARCHIVOS" $file "Existe ($size bytes)" "OK" "Archivo crítico presente" "MEDIO"
    }
    else {
        Add-ValidationResult "ARCHIVOS" $file "No encontrado" "ERROR" "Archivo crítico faltante" "CRITICO"
    }
}

# Verificar function_app.py tiene imports básicos
if (Test-Path "function_app.py") {
    $functionAppContent = Get-Content "function_app.py" -Raw
    if ($functionAppContent -match "import azure\.functions") {
        Add-ValidationResult "ARCHIVOS" "FUNCTION_APP_IMPORTS" "OK" "OK" "Imports de Azure Functions detectados" "BAJO"
    }
    else {
        Add-ValidationResult "ARCHIVOS" "FUNCTION_APP_IMPORTS" "Faltante" "WARNING" "No se detectan imports de azure.functions" "MEDIO"
    }
}

# 9. VALIDACION REMOTA DEL CONTENEDOR
Write-Host "9. ESTADO REAL DEL CONTENEDOR" -ForegroundColor Yellow

# Función helper para ejecutar comandos remotos via Kudu
function Invoke-KuduCommand {
    param($Command, $Description)
    
    try {
        Write-Host "  -> $Description..." -ForegroundColor Gray
        
        # Intentar via SSH/Kudu
        $result = az webapp ssh --name $FunctionAppName --resource-group $ResourceGroup --instance 0 --timeout 30 -c "$Command" 2>$null
        
        if ($LASTEXITCODE -eq 0 -and $result) {
            return [PSCustomObject]@{
                Success = $true
                Output  = $result -join "`n"
                Error   = $null
            }
        }
        else {
            return [PSCustomObject]@{
                Success = $false
                Output  = $null
                Error   = "Comando falló o timeout"
            }
        }
    }
    catch {
        return [PSCustomObject]@{
            Success = $false
            Output  = $null
            Error   = $_.Exception.Message
        }
    }
}

# A. VERIFICAR CODIGO EN /home/site/wwwroot
$wwwrootCheck = Invoke-KuduCommand "ls -la /home/site/wwwroot/ 2>/dev/null | head -10" "Listando /home/site/wwwroot"

if ($wwwrootCheck.Success) {
    $wwwrootContent = $wwwrootCheck.Output
    
    if ($wwwrootContent -match "function_app\.py") {
        Add-ValidationResult "CONTENEDOR_REMOTO" "CODIGO_EN_WWWROOT" "function_app.py detectado" "OK" "Código Python accesible en contenedor" "CRITICO"
    }
    else {
        Add-ValidationResult "CONTENEDOR_REMOTO" "CODIGO_EN_WWWROOT" "function_app.py faltante" "ERROR" "Código no accesible dentro del contenedor" "CRITICO"
    }
    
    if ($wwwrootContent -match "host\.json") {
        Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_JSON_REMOTO" "Existe" "OK" "host.json accesible en contenedor" "ALTO"
    }
    else {
        Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_JSON_REMOTO" "Faltante" "ERROR" "host.json no accesible en contenedor" "CRITICO"
    }
}
else {
    Add-ValidationResult "CONTENEDOR_REMOTO" "ACCESO_SSH" "Falló" "WARNING" "No se pudo acceder al contenedor vía SSH: $($wwwrootCheck.Error)" "ALTO"
}

# B. VERIFICAR PROCESO AZURE FUNCTIONS HOST
$processCheck = Invoke-KuduCommand "ps -ef | grep -E '(Microsoft.Azure.WebJobs|func|dotnet.*WebHost)' | grep -v grep" "Verificando procesos Functions Host"

if ($processCheck.Success) {
    $processes = $processCheck.Output
    
    if ($processes -match "Microsoft\.Azure\.WebJobs\.Script\.WebHost" -or $processes -match "func.*start") {
        Add-ValidationResult "CONTENEDOR_REMOTO" "FUNCTIONS_HOST_PROCESO" "Corriendo" "OK" "Azure Functions Host está ejecutándose" "CRITICO"
    }
    else {
        Add-ValidationResult "CONTENEDOR_REMOTO" "FUNCTIONS_HOST_PROCESO" "No detectado" "ERROR" "Azure Functions Host no está corriendo" "CRITICO"
    }
}
else {
    Add-ValidationResult "CONTENEDOR_REMOTO" "FUNCTIONS_HOST_PROCESO" "No verificable" "WARNING" "No se pudo verificar procesos: $($processCheck.Error)" "MEDIO"
}

# C. VERIFICAR PUERTO Y HEALTH STATUS
Write-Host "  -> Verificando health del host..." -ForegroundColor Gray

try {
    # Intentar acceder al endpoint de status del host
    $statusUrl = "https://$FunctionAppName.azurewebsites.net/admin/host/status"
    $statusResponse = az rest --method GET --url $statusUrl --query "state" -o tsv 2>$null
    
    if ($statusResponse -eq "Running") {
        Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_STATUS" "Running" "OK" "Host responde correctamente en puerto 80" "CRITICO"
    }
    elseif ($statusResponse) {
        Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_STATUS" $statusResponse "WARNING" "Host responde pero estado: $statusResponse" "ALTO"
    }
    else {
        Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_STATUS" "Sin respuesta" "ERROR" "Host no responde en puerto 80 o admin endpoint inaccesible" "CRITICO"
    }
}
catch {
    Add-ValidationResult "CONTENEDOR_REMOTO" "HOST_STATUS" "Error" "WARNING" "No se pudo verificar status del host: $($_.Exception.Message)" "MEDIO"
}

# D. VERIFICAR LOGS EN VIVO
Write-Host "  -> Obteniendo últimos logs..." -ForegroundColor Gray

try {
    $recentLogs = az webapp log tail --name $FunctionAppName --resource-group $ResourceGroup --provider application --num-lines 5 2>$null | Select-Object -Last 5
    
    if ($recentLogs) {
        $logsText = $recentLogs -join " "
        
        if ($logsText -match "error|exception|fail" -and $logsText -notmatch "info|debug") {
            Add-ValidationResult "CONTENEDOR_REMOTO" "LOGS_RECIENTES" "Errores detectados" "ERROR" "Logs muestran errores recientes" "ALTO"
        }
        else {
            Add-ValidationResult "CONTENEDOR_REMOTO" "LOGS_RECIENTES" "Normales" "OK" "Logs sin errores críticos recientes" "BAJO"
        }
    }
    else {
        Add-ValidationResult "CONTENEDOR_REMOTO" "LOGS_RECIENTES" "Sin logs" "WARNING" "No se obtuvieron logs recientes" "BAJO"
    }
}
catch {
    Add-ValidationResult "CONTENEDOR_REMOTO" "LOGS_RECIENTES" "Error" "WARNING" "Error obteniendo logs: $($_.Exception.Message)" "BAJO"
}

# 10. GENERAR REPORTE
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REPORTE DE VALIDACION" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan

$criticalIssues = @($validationResults | Where-Object { $_.Status -eq "ERROR" })
$warnings = @($validationResults | Where-Object { $_.Status -eq "WARNING" })
$okItems = @($validationResults | Where-Object { $_.Status -eq "OK" })

Write-Host ""
Write-Host "RESUMEN:" -ForegroundColor White
Write-Host "- Criticos: $($criticalIssues.Count)" -ForegroundColor $(if ($criticalIssues.Count -gt 0) { "Red" } else { "Green" })
Write-Host "- Warnings: $($warnings.Count)" -ForegroundColor $(if ($warnings.Count -gt 0) { "Yellow" } else { "Green" })  
Write-Host "- OK: $($okItems.Count)" -ForegroundColor Green
Write-Host ""

# Mostrar issues criticos
if ($criticalIssues.Count -gt 0) {
    Write-Host "ISSUES CRITICOS:" -ForegroundColor Red
    foreach ($issue in $criticalIssues) {
        Write-Host "  [ERROR] $($issue.Setting): $($issue.Recommendation)" -ForegroundColor Red
    }
    Write-Host ""
}

# Mostrar warnings importantes
$importantWarnings = $warnings | Where-Object { $_.Impact -eq "ALTO" -or $_.Impact -eq "CRITICO" }
if ($importantWarnings.Count -gt 0) {
    Write-Host "WARNINGS IMPORTANTES:" -ForegroundColor Yellow
    foreach ($warning in $importantWarnings) {
        Write-Host "  [WARN] $($warning.Setting): $($warning.Recommendation)" -ForegroundColor Yellow
    }
    Write-Host ""
}

# 11. DIAGNOSTICO SYNCFUNCTIONTRIGGERS
Write-Host "DIAGNOSTICO SYNCFUNCTIONTRIGGERS:" -ForegroundColor Magenta

$syncIssues = @()

# Verificar condiciones que impiden sync
if ($enableStorage -eq "false" -and $isCustomContainer) {
    $syncIssues += "WEBSITES_ENABLE_APP_SERVICE_STORAGE=false impide que syncfunctiontriggers acceda al codigo"
}

# Verificar coherencia Dockerfile vs Storage
$dockerfileIssues = $validationResults | Where-Object { $_.Category -eq "COHERENCIA" -and $_.Status -eq "ERROR" }
if ($dockerfileIssues.Count -gt 0) {
    $syncIssues += "Incoherencia entre Dockerfile y WEBSITES_ENABLE_APP_SERVICE_STORAGE"
}

# Verificar host.json
$hostJsonIssues = $validationResults | Where-Object { $_.Category -eq "HOST_JSON" -and $_.Status -eq "ERROR" }
if ($hostJsonIssues.Count -gt 0) {
    $syncIssues += "Problemas con host.json que pueden impedir el registro de functions"
}

# Verificar estado remoto del contenedor
$remoteIssues = $validationResults | Where-Object { $_.Category -eq "CONTENEDOR_REMOTO" -and $_.Status -eq "ERROR" }
if ($remoteIssues.Count -gt 0) {
    $syncIssues += "Problemas detectados en el contenedor remoto (código, host, procesos)"
}

if (-not $storageConnection -or $storageConnection -eq "UseDevelopmentStorage=true") {
    $syncIssues += "AzureWebJobsStorage invalido o no configurado"
}

if ($criticalIssues.Count -gt 0) {
    $syncIssues += "Hay $($criticalIssues.Count) issues criticos que deben resolverse"
}

if ($syncIssues.Count -gt 0) {
    Write-Host ""
    Write-Host "POSIBLES CAUSAS DEL FALLO SYNCFUNCTIONTRIGGERS:" -ForegroundColor Red
    foreach ($issue in $syncIssues) {
        Write-Host "  • $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "RECOMENDACIONES:" -ForegroundColor Yellow
    
    # Análisis basado en validación remota
    $codeInContainer = $validationResults | Where-Object { $_.Setting -eq "CODIGO_EN_WWWROOT" -and $_.Status -eq "OK" }
    $hostRunning = $validationResults | Where-Object { $_.Setting -eq "FUNCTIONS_HOST_PROCESO" -and $_.Status -eq "OK" }
    
    if (-not $codeInContainer) {
        Write-Host "  PROBLEMA CRITICO - CODIGO NO ACCESIBLE:" -ForegroundColor Red
        Write-Host "  1. El código no está en /home/site/wwwroot dentro del contenedor" -ForegroundColor Yellow
        Write-Host "  2. Opciones de resolución:" -ForegroundColor Yellow
        Write-Host "     A. Habilitar storage y copiar código: WEBSITES_ENABLE_APP_SERVICE_STORAGE=true" -ForegroundColor White
        Write-Host "     B. Verificar Dockerfile que COPY . /home/site/wwwroot esté presente" -ForegroundColor White
        Write-Host "     C. Reconstruir y redesplegar el contenedor" -ForegroundColor White
        Write-Host ""
    }
    
    if (-not $hostRunning) {
        Write-Host "  PROBLEMA CRITICO - HOST NO CORRIENDO:" -ForegroundColor Red
        Write-Host "  1. Azure Functions Host no está ejecutándose" -ForegroundColor Yellow
        Write-Host "  2. Verificar ENTRYPOINT/CMD en Dockerfile" -ForegroundColor Yellow
        Write-Host "  3. Revisar logs de startup del contenedor" -ForegroundColor Yellow
        Write-Host ""
    }
    
    if ($enableStorage -eq "false") {
        Write-Host "  OPCION A - HABILITAR STORAGE:" -ForegroundColor Yellow
        Write-Host "  1. az functionapp config appsettings set -g $ResourceGroup -n $FunctionAppName --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true" -ForegroundColor White
        Write-Host "  2. Copiar codigo fuente a /home/site/wwwroot via Kudu/SSH" -ForegroundColor Yellow
        Write-Host "  3. Reiniciar function app" -ForegroundColor Yellow
        Write-Host "  4. Ejecutar syncfunctiontriggers" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  OPCION B - DEPLOYMENT DIRECTO:" -ForegroundColor Yellow
        Write-Host "  1. Usar 'az functionapp deployment' en lugar de syncfunctiontriggers" -ForegroundColor Yellow
        Write-Host "  2. O aceptar que el Portal no muestre las functions (solo via API)" -ForegroundColor Yellow
    }
    
    # Mostrar comando para aplicar fix automatico
    Write-Host ""
    Write-Host "COMANDO PARA APLICAR FIX AUTOMATICO:" -ForegroundColor Cyan
    if ($enableStorage -eq "false") {
        Write-Host "  az functionapp config appsettings set -g $ResourceGroup -n $FunctionAppName --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true" -ForegroundColor White
    }

}
else {
    Write-Host "  ✓ No se detectaron problemas obvios con syncfunctiontriggers" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Exportar reporte detallado
$validationResults | Export-Csv -Path "validation-report.csv" -NoTypeInformation -Encoding UTF8
Write-Host "Reporte detallado guardado en: validation-report.csv" -ForegroundColor Green

# Return exit code basado en severity
if ($criticalIssues.Count -gt 0) {
    exit 2
}
elseif ($importantWarnings.Count -gt 0) {
    exit 1
}
else {
    exit 0
}
