# =======================================================================
# CONFIGURADOR DE CLAVE REDIS
# =======================================================================
# Este script te ayuda a configurar la clave de acceso a Redis
# Uso: .\configurar-redis-key.ps1

Write-Host "🔑 Configurador de Clave Redis para Diagnósticos" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Verificar si Azure CLI está instalado
$azCliInstalled = Get-Command "az" -ErrorAction SilentlyContinue
if (-not $azCliInstalled) {
    Write-Host "❌ Azure CLI no está instalado." -ForegroundColor Red
    Write-Host "💡 Instalar desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Opciones de configuración:" -ForegroundColor Cyan
Write-Host "1. Obtener clave automáticamente (requiere Azure CLI)" -ForegroundColor White
Write-Host "2. Configurar clave manualmente" -ForegroundColor White
Write-Host "3. Mostrar configuración actual" -ForegroundColor White
Write-Host ""

$opcion = Read-Host "Selecciona una opción (1-3)"

switch ($opcion) {
    "1" {
        if ($azCliInstalled) {
            Write-Host "🔄 Obteniendo clave de Redis desde Azure..." -ForegroundColor Yellow
            
            try {
                $redisKey = az redis list-keys --name boat-rental-cache --resource-group boat-rental-rg --query primaryKey -o tsv 2>$null
                
                if ($redisKey -and $redisKey.Trim() -ne "") {
                    # Configurar en el entorno actual
                    $env:REDIS_KEY = $redisKey.Trim()
                    
                    # Actualizar el archivo de activación
                    $activateScript = ".\.venv\Scripts\Activate.ps1"
                    if (Test-Path $activateScript) {
                        (Get-Content $activateScript) -replace 'REDIS_ACCESS_KEY_PLACEHOLDER', $redisKey.Trim() | Set-Content $activateScript
                        Write-Host "✅ Clave configurada exitosamente" -ForegroundColor Green
                        Write-Host "✅ Archivo de activación actualizado" -ForegroundColor Green
                    }
                    else {
                        Write-Host "⚠️  Clave configurada pero archivo de activación no encontrado" -ForegroundColor Yellow
                    }
                }
                else {
                    Write-Host "❌ No se pudo obtener la clave. Verifica tu autenticación en Azure." -ForegroundColor Red
                }
            }
            catch {
                Write-Host "❌ Error al obtener la clave: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "❌ Azure CLI no disponible" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "📝 Configuración manual de clave Redis" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Obtén tu clave Redis desde:" -ForegroundColor Yellow
        Write-Host "• Azure Portal > Redis Cache > Access keys" -ForegroundColor Gray
        Write-Host "• Azure CLI: az redis list-keys --name boat-rental-cache --resource-group boat-rental-rg" -ForegroundColor Gray
        Write-Host ""
        
        $redisKey = Read-Host "Ingresa tu clave Redis" -AsSecureString
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($redisKey))
        
        if ($plainKey -and $plainKey.Trim() -ne "") {
            # Configurar en el entorno actual
            $env:REDIS_KEY = $plainKey.Trim()
            
            # Actualizar el archivo de activación
            $activateScript = ".\.venv\Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                (Get-Content $activateScript) -replace 'REDIS_ACCESS_KEY_PLACEHOLDER', $plainKey.Trim() | Set-Content $activateScript
                Write-Host "✅ Clave configurada exitosamente" -ForegroundColor Green
                Write-Host "✅ Archivo de activación actualizado" -ForegroundColor Green
            }
            else {
                Write-Host "⚠️  Clave configurada pero archivo de activación no encontrado" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "❌ Clave vacía. No se realizaron cambios." -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "📊 Configuración actual de Redis:" -ForegroundColor Cyan
        Write-Host "=================================" -ForegroundColor Cyan
        Write-Host "Host: $env:REDIS_HOST" -ForegroundColor White
        Write-Host "Port: $env:REDIS_PORT" -ForegroundColor White
        Write-Host "SSL:  $env:REDIS_SSL" -ForegroundColor White
        
        if ($env:REDIS_KEY) {
            $maskedKey = $env:REDIS_KEY.Substring(0, [Math]::Min(8, $env:REDIS_KEY.Length)) + "***"
            Write-Host "Key:  $maskedKey" -ForegroundColor White
        }
        else {
            Write-Host "Key:  ❌ NO CONFIGURADA" -ForegroundColor Red
        }
    }
    
    default {
        Write-Host "❌ Opción inválida" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔧 Para probar la configuración ejecuta:" -ForegroundColor Yellow
Write-Host "   .\redis-quick-check.ps1" -ForegroundColor Gray
Write-Host ""