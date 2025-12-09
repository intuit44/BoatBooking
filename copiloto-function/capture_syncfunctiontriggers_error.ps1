# capture_syncfunctiontriggers_error.ps1
# ==========================================
# CAPTURA EL ERROR REAL DE SYNCFUNCTIONTRIGGERS
# ==========================================

param(
    [string]$ResourceGroup = "boat-rental-app-group",
    [string]$FunctionApp = "copiloto-semantico-func-us2",
    [string]$SubscriptionId = "380fa841-83f3-42fe-adc4-582a5ebe139b"
)

function Write-Info {
    param($msg)
    Write-Host "-> $msg" -ForegroundColor Cyan
}
function Write-Success {
    param($msg)
    Write-Host "[OK] $msg" -ForegroundColor Green
}
function Write-Error {
    param($msg)
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}
function Write-Warning {
    param($msg)
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "CAPTURA DE ERROR SYNCFUNCTIONTRIGGERS" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# ==========================================
# MÉTODO 1: MONITOR DE LOGS EN TIEMPO REAL
# ==========================================
Write-Info "MÉTODO 1: Iniciando monitor de logs en background..."

$job = Start-Job -ScriptBlock {
    param($rg, $app)
    az webapp log tail --resource-group $rg --name $app
} -ArgumentList $ResourceGroup, $FunctionApp

Start-Sleep 3  # Dar tiempo al job de iniciar

Write-Info "Logs iniciados. Esperando 2 segundos antes de ejecutar syncfunctiontriggers..."
Start-Sleep 2

# ==========================================
# EJECUCIÓN DE SYNCFUNCTIONTRIGGERS
# ==========================================
Write-Warning "Ejecutando syncfunctiontriggers..."
$syncUri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionApp/syncfunctiontriggers?api-version=2022-03-01"

try {
    $syncResult = az rest --method POST --uri $syncUri 2>&1
    Write-Error "Resultado: $syncResult"
}
catch {
    Write-Error "Excepción capturada: $($_.Exception.Message)"
}

Write-Info "Esperando 10 segundos para capturar logs post-sync..."
Start-Sleep 10

# ==========================================
# CAPTURAR Y MOSTRAR LOGS
# ==========================================
Write-Info "Capturando últimas líneas de log..."
try {
    $logOutput = Receive-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force

    if ($logOutput) {
        Write-Success "LOGS CAPTURADOS:"
        Write-Host "=================" -ForegroundColor Yellow
        
        # Mostrar las últimas 100 líneas
        $lastLines = $logOutput | Select-Object -Last 100
        foreach ($line in $lastLines) {
            if ($line -match "ERROR|Exception|Traceback|Failed|Error") {
                Write-Host $line -ForegroundColor Red
            }
            elseif ($line -match "syncfunctiontriggers|sync|trigger") {
                Write-Host $line -ForegroundColor Yellow
            }
            elseif ($line -match "WARNING|WARN") {
                Write-Host $line -ForegroundColor DarkYellow
            }
            else {
                Write-Host $line -ForegroundColor Gray
            }
        }
        Write-Host "=================" -ForegroundColor Yellow
    }
    else {
        Write-Warning "No se capturaron logs del job"
    }
}
catch {
    Write-Error "Error capturando logs: $($_.Exception.Message)"
    Remove-Job $job -Force -ErrorAction SilentlyContinue
}

# ==========================================
# MÉTODO 2: ACCESO DIRECTO A KUDU LOGS
# ==========================================
Write-Info "`nMÉTODO 2: Intentando acceso directo a logs de Kudu..."

try {
    # Obtener credentials de publicación para Kudu
    Write-Info "Obteniendo credenciales de publicación..."
    $pubProfile = az functionapp deployment list-publishing-profiles -g $ResourceGroup -n $FunctionApp --query "[?publishMethod=='MSDeploy']" -o json | ConvertFrom-Json
    
    if ($pubProfile -and $pubProfile[0]) {
        $kuduUrl = "https://$($pubProfile[0].publishUrl)/api/logs/recent"
        Write-Info "URL Kudu: $kuduUrl"
        
        # Crear credenciales base64
        $credentials = "$($pubProfile[0].userName):$($pubProfile[0].userPWD)"
        $credentialsBase64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($credentials))
        
        Write-Info "Intentando obtener logs recientes via Kudu..."
        $headers = @{
            'Authorization' = "Basic $credentialsBase64"
        }
        
        $kuduLogs = Invoke-RestMethod -Uri $kuduUrl -Headers $headers -TimeoutSec 30 -ErrorAction Stop
        
        if ($kuduLogs) {
            Write-Success "LOGS DE KUDU OBTENIDOS:"
            Write-Host "========================" -ForegroundColor Green
            $kuduLogs | ForEach-Object {
                Write-Host $_ -ForegroundColor White
            }
            Write-Host "========================" -ForegroundColor Green
        }
    }
    else {
        Write-Warning "No se pudieron obtener credenciales de publicación"
    }
}
catch {
    Write-Warning "Error accediendo a Kudu: $($_.Exception.Message)"
}

# ==========================================
# MÉTODO 3: LOGS ESPECÍFICOS DE HOST
# ==========================================
Write-Info "`nMÉTODO 3: Buscando logs específicos de Host..."

try {
    # Intentar obtener logs específicos del host de Functions
    $hostLogCommand = "az webapp log download -g $ResourceGroup -n $FunctionApp --log-file host-logs.zip"
    Write-Info "Ejecutando: $hostLogCommand"
    
    Invoke-Expression $hostLogCommand 2>$null
    
    if (Test-Path "host-logs.zip") {
        Write-Success "Logs del host descargados en host-logs.zip"
        Write-Info "Extrae el archivo y revisa LogFiles/Application/Functions/Host/ para el stack trace"
    }
}
catch {
    Write-Warning "Error descargando logs del host: $($_.Exception.Message)"
}

# ==========================================
# RESUMEN Y PRÓXIMOS PASOS
# ==========================================
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "RESUMEN" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

Write-Info "Si no se capturó el stack trace arriba, ejecuta manualmente:"
Write-Host "1. Abre Kudu Console: https://$FunctionApp.scm.azurewebsites.net/DebugConsole" -ForegroundColor White
Write-Host "2. Navega a: LogFiles/Application/Functions/Host/" -ForegroundColor White
Write-Host "3. Busca archivos .log recientes" -ForegroundColor White
Write-Host "4. Ejecuta syncfunctiontriggers mientras monitorizas esos logs" -ForegroundColor White

Write-Info "O alternativamente:"
Write-Host "func host start --verbose" -ForegroundColor White
Write-Info "desde el directorio local para ver errores de startup en tiempo real"

Write-Host "`nScript completado." -ForegroundColor Cyan
