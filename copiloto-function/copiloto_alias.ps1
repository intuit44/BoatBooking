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
    
  $uri = "https://copiloto-semantico-func.azurewebsites.net/api/ejecutar?code=$functionKey"
    
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
function cop-az {
  param([string]$comando)
    
  copiloto -intencion "ejecutar:azure" -parametros @{comando = "az $comando" }
}

# Función para modo guiado
function cop-guia {
  param([string]$tema)
    
  copiloto -intencion "guia:$tema" -modo "guiado"
}

# Función para orquestar flujos
function cop-flow {
  param([string]$flujo)
    
  copiloto -intencion "orquestar:$flujo" -modo "orquestador"
}

# Mostrar ayuda
function cop-help {
  @"
🤖 COPILOTO SEMÁNTICO - Comandos Disponibles

COMANDOS BÁSICOS:
  cop diag          - Diagnóstico completo del sistema
  cop dash          - Ver dashboard con insights
  cop logs          - Analizar logs recientes
  cop report        - Generar reporte del proyecto

COMANDOS AZURE:
  cop-az "functionapp list"                    - Listar function apps
  cop-az "storage blob list --container-name boat-rental-project"  - Listar archivos

MODO GUIADO:
  cop-guia configurar_blob     - Guía para configurar Blob Storage
  cop-guia optimizar_performance  - Guía de optimización
  cop-guia debug_errores       - Guía de debugging

FLUJOS ORQUESTADOS:
  cop-flow deployment          - Flujo completo de deployment
  cop-flow monitoreo          - Flujo de monitoreo

COMANDOS DIRECTOS:
  copiloto -intencion "buscar:*.py" -parametros @{limite=10}
  copiloto -intencion "generar:config" -parametros @{tipo="azure"}

EJEMPLOS:
  cop dash                     # Ver dashboard
  cop-az "monitor metrics list --resource <id>"  # Métricas de Azure
  cop-guia configurar_blob     # Guía paso a paso
"@
}

Write-Host "✅ Alias de copiloto configurados. Escribe 'cop-help' para ver comandos disponibles." -ForegroundColor Green
Write-Host "🔑 Function Key guardada en variable `$functionKey" -ForegroundColor Yellow

function cld {
  Set-Location -Path "$HOME/clouddrive"
}

