# start-expo.ps1
# Script optimizado para iniciar app Expo con verificaciones

Write-Host "🚀 Iniciando Boat Rental App con Expo SDK 53..." -ForegroundColor Green

# Verificación de prerequisitos
Write-Host "🔍 Verificando prerequisitos..."

# 1. Verificar React Native
try {
    $rnTest = node -e "require('react-native'); console.log('OK')" 2>&1
    if ($rnTest -eq "OK") {
        Write-Host "✅ React Native: Funcional" -ForegroundColor Green
    } else {
        Write-Host "❌ React Native: Problemas" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ React Native: No disponible" -ForegroundColor Red
    exit 1
}

# 2. Verificar Expo
try {
    $expoTest = node -e "require('expo'); console.log('OK')" 2>&1
    if ($expoTest -eq "OK") {
        Write-Host "✅ Expo: Funcional" -ForegroundColor Green
    } else {
        Write-Host "❌ Expo: Problemas" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Expo: No disponible" -ForegroundColor Red
    exit 1
}

# 3. Verificar App.js
if (Test-Path "App.js") {
    Write-Host "✅ App.js: Encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ App.js: No encontrado" -ForegroundColor Red
    exit 1
}

# 4. Verificar index.js
if (Test-Path "index.js") {
    Write-Host "✅ index.js: Encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ index.js: No encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Iniciando Expo con cache limpio..."
npx expo start --clear
