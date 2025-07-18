# start-debug.ps1
# Script para iniciar con logging máximo y debugging

Write-Host "🚀 INICIANDO DEBUG MODE" -ForegroundColor Red
Write-Host "📅 $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Verificaciones previas
Write-Host "🔍 Verificaciones previas..."

# 1. Verificar procesos
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    Write-Host "⚠️ Hay $($nodeProcs.Count) procesos Node corriendo" -ForegroundColor Yellow
} else {
    Write-Host "✅ No hay procesos Node corriendo" -ForegroundColor Green
}

# 2. Verificar archivos críticos
$criticalFiles = @("index.js", "App.js", "package.json", "src\screens\home\HomeScreen.tsx")
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file existe" -ForegroundColor Green
    } else {
        Write-Host "❌ $file NO existe" -ForegroundColor Red
    }
}

# 3. Verificar node_modules
if (Test-Path "node_modules") {
    Write-Host "✅ node_modules existe" -ForegroundColor Green
} else {
    Write-Host "❌ node_modules NO existe" -ForegroundColor Red
    Write-Host "📦 Ejecuta: npm install" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🚀 Iniciando Expo con máximo logging..."
Write-Host "📋 BUSCA ESTOS LOGS ESPECÍFICOS:"
Write-Host "   🔥 [App] ===== APP.JS INICIANDO CARGA ====="
Write-Host "   🔥 [App] ===== APP FUNCTION EJECUTADA ====="
Write-Host "   🎉 [App] ===== APP COMPONENT MOUNTED ====="
Write-Host "   🚨 [HomeScreen] ===== RENDER FUNCTION EJECUTADA ====="
Write-Host ""

# Iniciar con variables de debug máximo
$env:EXPO_DEBUG = "true"
$env:DEBUG = "*"
npx expo start --clear --dev-client
