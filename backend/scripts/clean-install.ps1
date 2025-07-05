# Script de limpieza profunda para Windows PowerShell
Write-Host "🧹 Iniciando limpieza profunda..." -ForegroundColor Cyan

# Cambiar al directorio backend
Set-Location -Path "C:\ProyectosSimbolicos\boat-rental-app\backend"

# 1. Eliminar archivos problemáticos
Write-Host "📁 Eliminando node_modules y archivos de lock..." -ForegroundColor Yellow
Remove-Item -Path "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "package-lock.json" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".npmrc" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "npm-debug.log" -Force -ErrorAction SilentlyContinue

# 2. Limpiar cache de npm
Write-Host "🗑️ Limpiando cache de npm..." -ForegroundColor Yellow
npm cache clean --force

# 3. Verificar versión de npm
Write-Host "📊 Verificando versión de npm..." -ForegroundColor Yellow
npm --version

# 4. Crear .npmrc local
Write-Host "📝 Creando .npmrc..." -ForegroundColor Yellow
@"
engine-strict=false
legacy-peer-deps=true
save-exact=false
package-lock=true
audit=false
fund=false
"@ | Out-File -FilePath ".npmrc" -Encoding UTF8

# 5. Instalar dependencias
Write-Host "📦 Instalando dependencias..." -ForegroundColor Green
npm install --verbose

# 6. Verificar instalación
if (Test-Path "package-lock.json") {
    Write-Host "✅ Instalación completada!" -ForegroundColor Green
    
    # Buscar claves vacías
    $emptyKeys = Select-String -Path "package-lock.json" -Pattern '"":'
    if ($emptyKeys) {
        Write-Host "⚠️ ADVERTENCIA: Se encontraron claves vacías en package-lock.json" -ForegroundColor Red
        Write-Host "🔧 Ejecutando corrección automática..." -ForegroundColor Yellow
        
        # Corregir el archivo
        $content = Get-Content "package-lock.json" -Raw
        $content = $content -replace '"": \{', '".": {'
        $content | Out-File -FilePath "package-lock.json" -Encoding UTF8
        
        Write-Host "✅ Corrección aplicada!" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Error: No se generó package-lock.json" -ForegroundColor Red
}