# copiloto_alias.ps1
# Configurar alias en Azure Cloud Shell para uso fácil

# Obtener la function key
$functionKey = az functionapp function keys list `
  --name copiloto-semantico-func `
  --resource-group boat-rental-app-group `
  --function-name ejecutar `
  --query "default" -o tsv

# Crear funciones helper
function copiloto {
  param(
    [string]$intencion,
    [hashtable]$parametros = @{},
    [string]$modo = "normal"
  )
    
  $body = @{
    intencion  = $intencion
    parametros = $parametros
    modo       = $modo
  } | ConvertTo-Json
    
  $uri = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar?code=$functionKey"
    
  try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Body $body -ContentType "application/json"
    $response | ConvertTo-Json -Depth 10
  }
  catch {
    Write-Error "Error: $_"
  }
}

# Función para comandos semánticos directos
function cop {
  param([string]$comando)
    
  # Mapeo de comandos cortos a intenciones
  $mapeo = @{
    "diag"   = "diagnosticar:completo"
    "dash"   = "dashboard"
    "help"   = "guia:ayuda"
    "blob"   = "guia:configurar_blob"
    "logs"   = "analizar:logs"
    "report" = "generar:reporte"
  }
    
  $intencion = if ($mapeo.ContainsKey($comando)) { $mapeo[$comando] } else { $comando }
  copiloto -intencion $intencion
}

# Función para ejecutar comandos Azure CLI a través del copiloto
function Invoke-CopAz {
  param([string]$comando)
    
  copiloto -intencion "ejecutar:azure" -parametros @{comando = "az $comando" }
}

# Función para modo guiado
function Show-CopGuia {
  param([string]$tema)
    
  copiloto -intencion "guia:$tema" -modo "guiado"
}

# Función para orquestar flujos
function Start-CopFlow {
  param([string]$flujo)
    
  copiloto -intencion "orquestar:$flujo" -modo "orquestador"
}

# Mostrar ayuda
function Show-CopHelp {
  @"
🤖 COPILOTO SEMÁNTICO - Comandos Disponibles

COMANDOS BÁSICOS:
  cop diag          - Diagnóstico completo del sistema
  cop dash          - Ver dashboard con insights
  cop logs          - Analizar logs recientes
  cop report        - Generar reporte del proyecto

COMANDOS AZURE:
  Invoke-CopAz "functionapp list"                    - Listar function apps
  Invoke-CopAz "storage blob list --container-name boat-rental-project"  - Listar archivos

MODO GUIADO:
  Show-CopGuia configurar_blob     - Guía para configurar Blob Storage
  Show-CopGuia optimizar_performance  - Guía de optimización
  Show-CopGuia debug_errores       - Guía de debugging

FLUJOS ORQUESTADOS:
  Start-CopFlow deployment          - Flujo completo de deployment
  Start-CopFlow monitoreo           - Flujo de monitoreo

COMANDOS DIRECTOS:
  copiloto -intencion "buscar:*.py" -parametros @{limite=10}
  copiloto -intencion "generar:config" -parametros @{tipo="azure"}

EJEMPLOS:
  cop dash                     # Ver dashboard
  Invoke-CopAz "monitor metrics list --resource <id>"  # Métricas de Azure
  Show-CopGuia configurar_blob     # Guía paso a paso
"@
}

Write-Host "✅ Alias de copiloto configurados. Escribe 'Show-CopHelp' para ver comandos disponibles." -ForegroundColor Green
Write-Host "🔑 Function Key guardada en variable `$functionKey" -ForegroundColor Yellow

function cld {
  Set-Location -Path "$HOME/clouddrive"
}

