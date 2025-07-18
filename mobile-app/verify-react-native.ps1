# verify-react-native.ps1
# Script para verificar que React Native funciona correctamente

Write-Host "🔍 Verificando React Native..." -ForegroundColor Yellow

# Test de resolución
Write-Host "1. Resolución de módulo:"
try {
    $resolved = node -e "console.log(require.resolve('react-native'))"
    if ($resolved -match "mobile-app") {
        Write-Host "   ✅ $resolved" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ $resolved" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error de resolución" -ForegroundColor Red
}

# Test de importación
Write-Host "2. Importación de módulo:"
try {
    $result = node -e "try { require('react-native'); console.log('OK'); } catch(e) { console.log('ERROR: ' + e.message); }"
    if ($result -eq "OK") {
        Write-Host "   ✅ Importación exitosa" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $result" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error de importación" -ForegroundColor Red
}

Write-Host "🎯 Verificación completada" -ForegroundColor Yellow
