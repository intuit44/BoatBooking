# final-fix.ps1
# Script final para arreglar completamente la app

Write-Host "🚀 ARREGLANDO BOAT RENTAL APP - VERSIÓN FINAL" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# IMPORTANTE: Cambiar al directorio del proyecto
$projectPath = "C:\ProyectosSimbolicos\boat-rental-app\mobile-app"
Write-Host "`n📁 Cambiando al directorio: $projectPath" -ForegroundColor Yellow
Set-Location $projectPath

# Verificar que estamos en el directorio correcto
if (!(Test-Path "package.json")) {
    Write-Host "❌ Error: No se encontró package.json. Verifica la ruta del proyecto." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Directorio correcto" -ForegroundColor Green

# 1. Crear styles.xml con el tema completo
Write-Host "`n📋 Paso 1: Creando archivo de estilos..." -ForegroundColor Yellow
$stylesPath = "android\app\src\main\res\values"
New-Item -ItemType Directory -Force -Path $stylesPath | Out-Null

$stylesContent = @"
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Base application theme -->
    <style name="AppTheme" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="android:textColor">#000000</item>
        <item name="android:windowBackground">@android:color/white</item>
        <item name="android:navigationBarColor">@android:color/white</item>
        <item name="android:statusBarColor">@android:color/transparent</item>
        <item name="android:windowLightStatusBar">true</item>
    </style>

    <!-- Splash Screen theme -->
    <style name="Theme.App.SplashScreen" parent="AppTheme">
        <item name="android:windowBackground">@drawable/splashscreen</item>
        <item name="android:windowFullscreen">true</item>
        <item name="android:windowContentOverlay">@null</item>
        <item name="android:windowNoTitle">true</item>
    </style>
</resources>
"@

$stylesContent | Out-File -FilePath "$stylesPath\styles.xml" -Encoding UTF8 -Force
Write-Host "✅ styles.xml creado" -ForegroundColor Green

# 2. Crear drawable del splash screen
Write-Host "`n📋 Paso 2: Creando splash screen..." -ForegroundColor Yellow
$drawablePath = "android\app\src\main\res\drawable"
New-Item -ItemType Directory -Force -Path $drawablePath | Out-Null

$splashContent = @"
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/white"/>
    <item>
        <bitmap
            android:gravity="center"
            android:src="@mipmap/ic_launcher"/>
    </item>
</layer-list>
"@

$splashContent | Out-File -FilePath "$drawablePath\splashscreen.xml" -Encoding UTF8 -Force
Write-Host "✅ splashscreen.xml creado" -ForegroundColor Green

# 3. Asegurarse de que el bundle existe
Write-Host "`n📋 Paso 3: Verificando bundle JavaScript..." -ForegroundColor Yellow
$bundlePath = "android\app\src\main\assets\index.android.bundle"
if (!(Test-Path $bundlePath)) {
    Write-Host "⚠️  Bundle no encontrado, generando..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path "android\app\src\main\assets" | Out-Null
    & npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output $bundlePath --assets-dest android/app/src/main/res
}
Write-Host "✅ Bundle verificado" -ForegroundColor Green

# 4. Compilar APK
Write-Host "`n📋 Paso 4: Compilando APK..." -ForegroundColor Yellow
Set-Location android

# Usar gradlew.bat en Windows
if (Test-Path "gradlew.bat") {
    & .\gradlew.bat clean
    & .\gradlew.bat assembleDebug
} else {
    Write-Host "❌ Error: No se encontró gradlew.bat" -ForegroundColor Red
    exit 1
}

Set-Location ..

# 5. Verificar e instalar APK
$apkPath = "android\app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $apkPath) {
    Write-Host "`n✅ APK compilado exitosamente" -ForegroundColor Green
    
    # Desinstalar versión anterior
    Write-Host "`n📋 Paso 5: Desinstalando versión anterior..." -ForegroundColor Yellow
    & adb uninstall com.boatrentals.app 2>$null
    
    # Instalar nuevo APK
    Write-Host "`n📋 Paso 6: Instalando APK..." -ForegroundColor Yellow
    & adb install -r $apkPath
    
    # Configurar puerto
    Write-Host "`n📋 Paso 7: Configurando puerto..." -ForegroundColor Yellow
    & adb reverse tcp:8081 tcp:8081
    
    # Iniciar la app
    Write-Host "`n📋 Paso 8: Iniciando la app..." -ForegroundColor Yellow
    & adb shell am start -n com.boatrentals.app/.MainActivity
    
    Write-Host "`n✅ ¡INSTALACIÓN COMPLETA!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "✅ La app debería estar funcionando" -ForegroundColor Cyan
    Write-Host "📱 Si ves una pantalla blanca, espera unos segundos" -ForegroundColor Cyan
    Write-Host "🔍 Para ver logs: adb logcat *:E" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Error: El APK no se compiló correctamente" -ForegroundColor Red
    Write-Host "Busca errores en la salida anterior de Gradle" -ForegroundColor Yellow
}
