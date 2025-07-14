# Script para verificar y corregir errores críticos
Write-Host "🔍 Verificando estado del proyecto..." -ForegroundColor Yellow

# Verificar si existe package.json
if (Test-Path "package.json") {
    Write-Host "✅ package.json encontrado" -ForegroundColor Green
    
    # Leer y verificar contenido
    $content = Get-Content "package.json" -Raw
    
    if ($content -match '"undefined"') {
        Write-Host "❌ ERROR CRÍTICO: Dependencia 'undefined' encontrada" -ForegroundColor Red
    }
    
    if ($content -match '"@expo/metro-runtime": "~5.0.4"') {
        Write-Host "❌ ERROR: @expo/metro-runtime versión incorrecta" -ForegroundColor Red
    }
    
    if ($content -match '"react-native-maps": "1.20.1"') {
        Write-Host "❌ ERROR: react-native-maps versión incompatible" -ForegroundColor Red
    }
    
    # Ejecutar corrección
    Write-Host "`n🔧 Ejecutando corrección de errores críticos..." -ForegroundColor Yellow
    node "fix-critical-errors.js"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Corrección completada. Instalando dependencias..." -ForegroundColor Green
        npm install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n🚀 Iniciando aplicación con caché limpia..." -ForegroundColor Green
            npx expo start --clear
        } else {
            Write-Host "`n❌ Error en npm install. Revisa los mensajes anteriores." -ForegroundColor Red
        }
    } else {
        Write-Host "`n❌ Error en la corrección. Revisa los mensajes anteriores." -ForegroundColor Red
    }
} else {
    Write-Host "❌ package.json no encontrado en el directorio actual" -ForegroundColor Red
}