# Script de verificación completa antes de amplify push
# Uso: .\scripts\verify-amplify.ps1

Write-Host "🔍 VERIFICACIÓN COMPLETA DE AMPLIFY" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Función para mostrar resultados
function Show-Result {
    param(
        [bool]$Success,
        [string]$Message
    )
    
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
        $script:Errors++
    }
}

# Contador de errores
$script:Errors = 0

Write-Host "`n📋 Iniciando verificaciones..." -ForegroundColor Blue

# 1. Verificar que estamos en el directorio correcto
Write-Host "`n1. Verificando directorio del proyecto..."
if (Test-Path "amplify\.config\project-config.json") {
    Show-Result $true "Directorio correcto (amplify project encontrado)"
} else {
    Show-Result $false "No estás en el directorio raíz del proyecto Amplify"
}

# 2. Verificar status de Amplify
Write-Host "`n2. Verificando status de Amplify..."
try {
    $amplifyStatus = amplify status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Show-Result $true "Amplify status OK"
        Write-Host "📊 Status actual:" -ForegroundColor Yellow
        Write-Host $amplifyStatus
    } else {
        Show-Result $false "Error en amplify status"
    }
} catch {
    Show-Result $false "Error ejecutando amplify status"
}

# 3. Verificar que Auth esté configurado
Write-Host "`n3. Verificando configuración de Auth..."
if ($amplifyStatus -match "Auth") {
    Show-Result $true "Auth está configurado"
} else {
    Show-Result $false "Auth NO está configurado (requerido para @auth rules)"
}

# 4. Verificar sintaxis del schema GraphQL
Write-Host "`n4. Compilando schema GraphQL..."
try {
    $gqlCompile = amplify api gql-compile 2>&1
    if ($LASTEXITCODE -eq 0) {
        Show-Result $true "Schema GraphQL compilado correctamente"
    } else {
        Show-Result $false "Error en compilación de GraphQL"
        Write-Host "🚨 Errores encontrados:" -ForegroundColor Red
        Write-Host $gqlCompile -ForegroundColor Red
    }
} catch {
    Show-Result $false "Error ejecutando gql-compile"
}

# 5. Verificar dependencias de Amplify en package.json
Write-Host "`n5. Verificando dependencias de Amplify..."
if (Test-Path "package.json") {
    $packageJson = Get-Content "package.json" -Raw
    if ($packageJson -match "aws-amplify") {
        Show-Result $true "Dependencias de Amplify encontradas"
        Write-Host "📦 Versiones instaladas:" -ForegroundColor Yellow
        $packageJson | Select-String -Pattern "(aws-amplify|@aws-amplify)" | ForEach-Object { Write-Host $_.Line.Trim() }
    } else {
        Show-Result $false "Dependencias de Amplify NO encontradas"
    }
} else {
    Show-Result $false "package.json no encontrado"
}

# 6. Verificar estructura de archivos
Write-Host "`n6. Verificando estructura de archivos..."
$requiredFiles = @(
    "amplify\backend\api",
    "src\services\boatsService.ts",
    "src\services\bookingsService.ts", 
    "src\services\reservationsService.ts",
    "src\store\hooks.ts"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Show-Result $true "Archivo/directorio encontrado: $file"
    } else {
        Show-Result $false "Archivo/directorio faltante: $file"
    }
}

# 7. Verificar conexión a AWS
Write-Host "`n7. Verificando conexión a AWS..."
try {
    $null = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Show-Result $true "Conexión a AWS OK"
        Write-Host "👤 Usuario AWS actual:" -ForegroundColor Yellow
        $awsArn = aws sts get-caller-identity --query 'Arn' --output text 2>$null
        if ($awsArn) { Write-Host $awsArn } else { Write-Host "No se pudo obtener info del usuario" }
    } else {
        Show-Result $false "Sin conexión a AWS o credenciales no configuradas"
    }
} catch {
    Show-Result $false "AWS CLI no disponible"
}

# 8. Verificar espacio en disco
Write-Host "`n8. Verificando espacio en disco..."
try {
    $drive = Get-PSDrive -Name (Get-Location).Drive.Name
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeSpaceGB -gt 1) {
        Show-Result $true "Espacio en disco suficiente ($freeSpaceGB GB disponibles)"
    } else {
        Show-Result $false "Poco espacio en disco disponible ($freeSpaceGB GB)"
    }
} catch {
    Show-Result $false "No se pudo verificar espacio en disco"
}

# 9. Verificar procesos de Amplify
Write-Host "`n9. Verificando procesos de Amplify..."
$amplifyProcesses = Get-Process | Where-Object { $_.ProcessName -like "*amplify*" -or $_.ProcessName -like "*node*" }
if ($amplifyProcesses) {
    Show-Result $false "Hay procesos que podrían interferir"
    Write-Host "🔄 Procesos encontrados:" -ForegroundColor Yellow
    $amplifyProcesses | Select-Object ProcessName, Id | Format-Table
} else {
    Show-Result $true "No hay procesos conflictivos"
}

# 10. Verificar archivos temporales
Write-Host "`n10. Verificando archivos temporales..."
$tempDirs = @(
    "amplify\.temp",
    "amplify\backend\.temp",
    "node_modules\.cache"
)

$tempFound = $false
foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        $tempFound = $true
        Write-Host "⚠️  Directorio temporal encontrado: $dir" -ForegroundColor Yellow
    }
}

if (-not $tempFound) {
    Show-Result $true "No hay archivos temporales conflictivos"
} else {
    Show-Result $false "Archivos temporales encontrados (recomendado limpiar)"
}

# Resumen final
Write-Host "`n📊 RESUMEN DE VERIFICACIÓN" -ForegroundColor Blue
Write-Host "=========================="

if ($script:Errors -eq 0) {
    Write-Host "🎉 ¡TODO LISTO PARA AMPLIFY PUSH!" -ForegroundColor Green
    Write-Host "✅ Todas las verificaciones pasaron correctamente" -ForegroundColor Green
    Write-Host "`n🚀 Comandos sugeridos:" -ForegroundColor Blue
    Write-Host "1. amplify push"
    Write-Host "2. Seleccionar 'Yes' para generar código TypeScript"
    Write-Host "3. Usar patrón: src/graphql/**/*.ts"
} else {
    Write-Host "🚨 ERRORES ENCONTRADOS: $($script:Errors)" -ForegroundColor Red
    Write-Host "❌ Corrige los errores antes de hacer amplify push" -ForegroundColor Red
    Write-Host "`n🔧 Acciones recomendadas:" -ForegroundColor Yellow
    
    if ($gqlCompile -match "relationship") {
        Write-Host "- Corregir relaciones en schema.graphql"
    }
    
    if ($amplifyStatus -notmatch "Auth") {
        Write-Host "- Configurar Auth: amplify add auth"
    }
    
    if ($tempFound) {
        Write-Host "- Limpiar archivos temporales"
    }
}

Write-Host "`n✨ Verificación completada" -ForegroundColor Cyan