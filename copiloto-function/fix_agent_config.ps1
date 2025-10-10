# fix_agent_config.ps1 - VERSION CORREGIDA
# Corrige la configuración después de recrear el proyecto en AI Foundry

param(
    [Parameter(Mandatory = $true)]
    [string]$NewAgentId,
    
    [Parameter(Mandatory = $true)]
    [string]$NewFoundryEndpoint,
    
    [Parameter(Mandatory = $false)]
    [string]$NewApiKey = "",
    
    [string]$ResourceGroup = "boat-rental-app-group",
    [string]$FunctionApp = "copiloto-semantico-func-us2"
)

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "CORRECCION DE CONFIGURACION DEL AGENTE" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# Validar parámetros
if ([string]::IsNullOrWhiteSpace($NewAgentId)) {
    Write-Host "ERROR: NewAgentId es requerido" -ForegroundColor Red
    Write-Host "  Ejemplo: .\fix_agent_config.ps1 -NewAgentId 'agent-abc123' -NewFoundryEndpoint 'https://...'" -ForegroundColor Gray
    exit 1
}

if ([string]::IsNullOrWhiteSpace($NewFoundryEndpoint)) {
    Write-Host "ERROR: NewFoundryEndpoint es requerido" -ForegroundColor Red
    exit 1
}

# Mostrar configuración
Write-Host "Configuracion a aplicar:" -ForegroundColor Cyan
Write-Host "  Agent ID: $NewAgentId" -ForegroundColor Gray
Write-Host "  Foundry Endpoint: $NewFoundryEndpoint" -ForegroundColor Gray
if ($NewApiKey) {
    $maskedKey = $NewApiKey.Substring(0, 10) + "..." + $NewApiKey.Substring($NewApiKey.Length - 10)
    Write-Host "  API Key: $maskedKey" -ForegroundColor Gray
}

Write-Host "`n[1] Actualizando App Settings..." -ForegroundColor Yellow

# Configuración a aplicar
$settingsToUpdate = @{
    "AI_AGENT_ID"         = $NewAgentId
    "AI_FOUNDRY_ENDPOINT" = $NewFoundryEndpoint
}

if ($NewApiKey) {
    $settingsToUpdate["AZURE_VOICE_LIVE_API_KEY"] = $NewApiKey
}

# Aplicar cada setting
foreach ($key in $settingsToUpdate.Keys) {
    $value = $settingsToUpdate[$key]
    $applied = $false
    
    for ($i = 1; $i -le 3; $i++) {
        Write-Host "  Configurando $key (intento $i/3)..." -ForegroundColor Gray
        
        try {
            az functionapp config appsettings set `
                -g $ResourceGroup `
                -n $FunctionApp `
                --settings "$key=$value" `
                -o none
            
            Write-Host "  [OK] $key configurado correctamente" -ForegroundColor Green
            $applied = $true
            break
        }
        catch {
            Write-Host "  [INTENTO $i FALLADO] $($_.Exception.Message)" -ForegroundColor Yellow
            if ($i -lt 3) {
                Start-Sleep -Seconds 5
            }
        }
    }
    
    if (-not $applied) {
        Write-Host "  [ERROR] No se pudo configurar $key después de 3 intentos" -ForegroundColor Red
        exit 1
    }
}

# Reiniciar Function App
Write-Host "`n[2] Reiniciando Function App..." -ForegroundColor Yellow
try {
    az functionapp restart -g $ResourceGroup -n $FunctionApp -o none
    Write-Host "  [OK] Function App reiniciada" -ForegroundColor Green
}
catch {
    Write-Host "  [ERROR] Al reiniciar: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Esperar propagación
Write-Host "`n[3] Esperando propagación de configuracion (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar endpoints
Write-Host "`n[4] Verificando endpoints..." -ForegroundColor Yellow
$baseUrl = "https://$FunctionApp.azurewebsites.net"

function Test-Endpoint {
    param([string]$url, [string]$name)
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing
        Write-Host "  [OK] $name - Status: $($response.StatusCode)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  [ERROR] $name - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$healthOk = Test-Endpoint -url "$baseUrl/api/health" -name "Health"
$statusOk = Test-Endpoint -url "$baseUrl/api/status" -name "Status"

# Resumen final
Write-Host "`n========================================" -ForegroundColor Cyan
if ($healthOk -and $statusOk) {
    Write-Host "[EXITO] CONFIGURACION APLICADA CORRECTAMENTE" -ForegroundColor Green
    Write-Host "URL del agente: $baseUrl" -ForegroundColor Yellow
}
else {
    Write-Host "[ADVERTENCIA] Algunos endpoints no responden" -ForegroundColor Yellow
}

Write-Host "Configuracion completada.`n" -ForegroundColor Cyan