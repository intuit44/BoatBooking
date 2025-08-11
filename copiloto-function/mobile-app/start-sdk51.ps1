# start-sdk51.ps1
# Script para iniciar con Expo SDK 51

Write-Host "🚀 INICIANDO BOAT RENTAL APP CON EXPO SDK 51" -ForegroundColor Green
Write-Host "📅 $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Verificaciones previas
Write-Host "🔍 Verificaciones previas..."

# Verificar archivos críticos
$criticalFiles = @("index.js", "App.js", "package.json")
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file existe" -ForegroundColor Green
    } else {
        Write-Host "❌ $file NO existe" -ForegroundColor Red
        exit 1
    }
}

# Verificar node_modules
if (Test-Path "node_modules") {
    Write-Host "✅ node_modules existe" -ForegroundColor Green
} else {
    Write-Host "❌ node_modules NO existe - ejecuta: npm install" -ForegroundColor Red
    exit 1
}

# Verificar versión de Expo
Write-Host "🔍 Verificando Expo SDK..."
try {
    $pkg = Get-Content "package.json" | ConvertFrom-Json
    $expoVersion = $pkg.dependencies.expo
    if ($expoVersion -match "51\.") {
        Write-Host "✅ Expo SDK 51 detectado: $expoVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Versión de Expo: $expoVersion (esperaba 51.x)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Error verificando versión de Expo" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Iniciando Expo SDK 51..."
Write-Host "📋 BUSCA ESTOS LOGS:"
Write-Host "   🔥 [Index] ===== INDEX.JS SDK 51 EJECUTADO ====="
Write-Host "   🔥 [App] ===== APP.JS INICIANDO CARGA ====="
Write-Host "   🔥 [App] ===== APP FUNCTION EJECUTADA ====="
Write-Host "   🎉 [App] ===== APP COMPONENT MOUNTED ====="
Write-Host ""

npx expo start --clear
