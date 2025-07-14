# Script para actualizar dependencias incompatibles en PowerShell
$packageJsonPath = Join-Path $PSScriptRoot "package.json"

# Leer el archivo package.json
$packageJson = Get-Content -Path $packageJsonPath -Raw | ConvertFrom-Json

# Crear copia de seguridad
$backupPath = "$packageJsonPath.backup-$(Get-Date -Format 'yyyyMMddHHmmss')"
Copy-Item -Path $packageJsonPath -Destination $backupPath
Write-Host "Copia de seguridad creada en: $backupPath"

# Dependencias a actualizar
$dependenciesToUpdate = @{
    '@expo/metro-runtime' = '~4.0.1'
    '@react-native-async-storage/async-storage' = '1.23.1'
    '@react-native-community/datetimepicker' = '8.2.0'
    '@react-native-community/slider' = '4.5.5'
    'react-native' = '0.76.9'
    'react-native-maps' = '1.18.0'
    'react-native-safe-area-context' = '4.12.0'
}

# Actualizar las versiones en el package.json
$updated = $false
foreach ($dependency in $dependenciesToUpdate.Keys) {
    if ($packageJson.dependencies.$dependency) {
        Write-Host "Actualizando $dependency a $($dependenciesToUpdate[$dependency])"
        $packageJson.dependencies.$dependency = $dependenciesToUpdate[$dependency]
        $updated = $true
    }
}

if ($updated) {
    # Guardar el package.json actualizado
    $packageJson | ConvertTo-Json -Depth 10 | Set-Content -Path $packageJsonPath
    Write-Host "package.json actualizado correctamente"
    
    # Ejecutar npm install
    Write-Host "Ejecutando npm install para aplicar los cambios..."
    npm install
} else {
    Write-Host "No se encontraron dependencias para actualizar"
}

Write-Host "`nProceso completado. Intenta iniciar la aplicación con: npx expo start"