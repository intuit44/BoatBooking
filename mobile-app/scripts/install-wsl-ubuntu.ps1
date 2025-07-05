# Script para instalar WSL2 + Ubuntu en Windows
# Ejecutar como Administrador en PowerShell

Write-Host "🐧 INSTALACIÓN DE WSL2 + UBUNTU" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Verificar si se ejecuta como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host "Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Ejecutándose como Administrador" -ForegroundColor Green

# 1. Habilitar WSL
Write-Host "`n1. Habilitando Windows Subsystem for Linux..." -ForegroundColor Blue
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. Habilitar Virtual Machine Platform
Write-Host "`n2. Habilitando Virtual Machine Platform..." -ForegroundColor Blue
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. Descargar e instalar el kernel de WSL2
Write-Host "`n3. Descargando kernel de WSL2..." -ForegroundColor Blue
$wslUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$wslUpdatePath = "$env:TEMP\wsl_update_x64.msi"

try {
    Invoke-WebRequest -Uri $wslUpdateUrl -OutFile $wslUpdatePath
    Write-Host "✅ Kernel descargado" -ForegroundColor Green
    
    # Instalar el kernel
    Write-Host "4. Instalando kernel de WSL2..." -ForegroundColor Blue
    Start-Process msiexec.exe -Wait -ArgumentList "/i $wslUpdatePath /quiet"
    Write-Host "✅ Kernel instalado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error descargando kernel, continuando..." -ForegroundColor Yellow
}

# 4. Establecer WSL2 como versión por defecto
Write-Host "`n5. Estableciendo WSL2 como versión por defecto..." -ForegroundColor Blue
wsl --set-default-version 2

# 5. Instalar Ubuntu
Write-Host "`n6. Instalando Ubuntu..." -ForegroundColor Blue
wsl --install -d Ubuntu

Write-Host "`n🎉 INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "✅ WSL2 habilitado" -ForegroundColor Green
Write-Host "✅ Ubuntu instalado" -ForegroundColor Green
Write-Host "`n⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "1. REINICIA tu computadora ahora" -ForegroundColor Red
Write-Host "2. Después del reinicio, abre 'Ubuntu' desde el menú de inicio" -ForegroundColor Yellow
Write-Host "3. Configura tu usuario y contraseña de Ubuntu" -ForegroundColor Yellow
Write-Host "4. Ejecuta el siguiente script de configuración" -ForegroundColor Yellow

Write-Host "`n🚀 Próximo paso:" -ForegroundColor Blue
Write-Host "Después del reinicio, ejecuta en Ubuntu:" -ForegroundColor Cyan
Write-Host "curl -fsSL https://raw.githubusercontent.com/tu-repo/setup-dev-environment.sh | bash" -ForegroundColor White

pause