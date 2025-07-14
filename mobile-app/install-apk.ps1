# install-apk.ps1
# Script para instalar el APK compilado en dispositivo Android

Write-Host "📱 INSTALANDO BOAT RENTAL APP" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Ruta del APK compilado
$apkPath = "C:\ProyectosSimbolicos\boat-rental-app\mobile-app\android\app\build\outputs\apk\debug\app-debug.apk"

# Verificar que el APK existe
if (!(Test-Path $apkPath)) {
    Write-Host "❌ Error: APK no encontrado en $apkPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ APK encontrado: $apkPath" -ForegroundColor Green

# Verificar dispositivos conectados
Write-Host "`n📋 Verificando dispositivos Android..." -ForegroundColor Yellow
$devices = & adb devices 2>$null

if ($devices -like "*device*" -or $devices -like "*emulator*") {
    Write-Host "✅ Dispositivo Android detectado" -ForegroundColor Green
    Write-Host $devices -ForegroundColor Cyan
    
    # Desinstalar versión anterior si existe
    Write-Host "`n📋 Desinstalando versión anterior..." -ForegroundColor Yellow
    & adb uninstall com.boatrentals.app 2>$null
    
    # Instalar nueva versión
    Write-Host "`n📋 Instalando APK..." -ForegroundColor Yellow
    $installResult = & adb install -r $apkPath 2>&1
    
    if ($installResult -like "*Success*") {
        Write-Host "✅ APK instalado exitosamente" -ForegroundColor Green
        
        # Configurar puerto para desarrollo (opcional)
        Write-Host "`n📋 Configurando puerto para desarrollo..." -ForegroundColor Yellow
        & adb reverse tcp:8081 tcp:8081 2>$null
        
        # Iniciar la aplicación
        Write-Host "`n📋 Iniciando aplicación..." -ForegroundColor Yellow
        & adb shell am start -n com.boatrentals.app/.MainActivity
        
        Write-Host "`n🎉 ¡APLICACIÓN INSTALADA Y EJECUTÁNDOSE!" -ForegroundColor Green
        Write-Host "=========================================" -ForegroundColor Green
        Write-Host "📱 Revisa tu dispositivo Android" -ForegroundColor Cyan
        Write-Host "🔍 Para ver logs en tiempo real: adb logcat *:E" -ForegroundColor Cyan
        Write-Host "🔄 Para reinstalar: ejecuta este script nuevamente" -ForegroundColor Cyan
        
    } else {
        Write-Host "❌ Error al instalar APK:" -ForegroundColor Red
        Write-Host $installResult -ForegroundColor Red
    }
    
} else {
    Write-Host "❌ No se detectaron dispositivos Android" -ForegroundColor Red
    Write-Host "`n📋 PARA CONECTAR UN DISPOSITIVO:" -ForegroundColor Yellow
    Write-Host "`n1. 📱 DISPOSITIVO FÍSICO:" -ForegroundColor Cyan
    Write-Host "   • Ve a Configuración > Acerca del teléfono" -ForegroundColor White
    Write-Host "   • Toca 7 veces en 'Número de compilación'" -ForegroundColor White
    Write-Host "   • Regresa y busca 'Opciones de desarrollador'" -ForegroundColor White
    Write-Host "   • Activa 'Depuración USB'" -ForegroundColor White
    Write-Host "   • Conecta por cable USB" -ForegroundColor White
    Write-Host "   • Acepta el diálogo de depuración en el teléfono" -ForegroundColor White
    
    Write-Host "`n2. 🖥️ EMULADOR:" -ForegroundColor Cyan
    Write-Host "   • Abre Android Studio" -ForegroundColor White
    Write-Host "   • Ve a Tools > AVD Manager" -ForegroundColor White
    Write-Host "   • Crea/inicia un dispositivo virtual" -ForegroundColor White
    Write-Host "   • Espera que cargue completamente" -ForegroundColor White
    
    Write-Host "`n3. 🔄 VERIFICAR CONEXIÓN:" -ForegroundColor Cyan
    Write-Host "   • Ejecuta: adb devices" -ForegroundColor White
    Write-Host "   • Deberías ver tu dispositivo listado" -ForegroundColor White
    
    Write-Host "`n📋 Luego ejecuta este script nuevamente" -ForegroundColor Yellow
}

Write-Host "`n💡 NOTA: El bundle JS tiene errores pero el APK nativo funciona" -ForegroundColor Yellow
