# AÑADIR ESTAS LÍNEAS AL INICIO del fix_functionapp_final.ps1 (después de FASE 2)

# ==========================================
# FASE 2.1: FORZAR CONFIGURACIÓN DE CONTENEDOR
# ==========================================
Write-Step "FASE 2.1: ASEGURAR CONFIGURACIÓN DE CONTENEDOR" 2.1

# Construir imagen con nuevo tag
Write-Info "Construyendo imagen con bash incluido..."
docker build -t "$ACR.azurecr.io/copiloto-func-azcli:$ImageTag" .
docker push "$ACR.azurecr.io/copiloto-func-azcli:$ImageTag"

# CRÍTICO: Configurar contenedor ANTES de app settings
Write-Info "Configurando contenedor personalizado..."
az functionapp config container set `
  --name $FunctionApp `
  --resource-group $ResourceGroup `
  --docker-custom-image-name "$ACR.azurecr.io/copiloto-func-azcli:$ImageTag" `
  --docker-registry-server-url "https://$ACR.azurecr.io" `
  --docker-registry-server-user $acrUsername `
  --docker-registry-server-password $acrPassword

Write-Success "Contenedor configurado correctamente"

# ==========================================
# AÑADIR ESTAS VARIABLES A LA SECCIÓN $settings
# ==========================================

# Dentro del hashtable $settings, AÑADIR:
"WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"  # CRÍTICO para contenedores
"DOCKER_ENABLE_CI" = "true"                      # CRÍTICO para auto-deploy
"FUNCTIONS_CUSTOM_CONTAINER_USE_DEFAULT_PORT" = "1"  # CRÍTICO para puerto 80