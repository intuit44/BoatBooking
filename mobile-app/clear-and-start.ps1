# Script para limpiar caché y reiniciar la aplicación Expo
Write-Host "Limpiando caché de Expo y reiniciando la aplicación..."

# Detener cualquier proceso de Expo en ejecución
try {
    $expoProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*expo*" }
    if ($expoProcesses) {
        $expoProcesses | ForEach-Object { Stop-Process -Id $_.Id -Force }
        Write-Host "Procesos de Expo detenidos"
    }
} catch {
    Write-Host "No se encontraron procesos de Expo en ejecución"
}

# Limpiar caché
Write-Host "Limpiando caché de Expo..."
npx expo start --clear --no-dev --minify

# Iniciar la aplicación
Write-Host "Iniciando la aplicación..."
npx expo start