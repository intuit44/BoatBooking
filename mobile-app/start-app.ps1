# start-app.ps1
# Script optimizado para iniciar la app sin errores

Write-Host "🚀 Iniciando Boat Rental App..." -ForegroundColor Green

# Verificar React Native
Write-Host "🔍 Verificando React Native..."
try {
    $rnTest = node -e "require('react-native'); console.log('OK')"
    if ($rnTest -eq "OK") {
        Write-Host "✅ React Native funcional" -ForegroundColor Green
    } else {
        Write-Host "❌ React Native con problemas" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ React Native no funciona" -ForegroundColor Red
    exit 1
}

# Iniciar Expo
Write-Host "🚀 Iniciando Expo..."
npx expo start --clear
