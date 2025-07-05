# Script de verificacion completa FASE 2 - Autenticacion y Navegacion
# Uso: .\scripts\verify-phase2-complete.ps1

Write-Host "VERIFICACION COMPLETA FASE 2 - AUTENTICACION" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Funcion para mostrar resultados
function Show-Result {
    param(
        [bool]$Success,
        [string]$Message,
        [string]$Details = ""
    )
    
    if ($Success) {
        Write-Host "[OK] $Message" -ForegroundColor Green
        if ($Details) {
            Write-Host "   $Details" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ERROR] $Message" -ForegroundColor Red
        if ($Details) {
            Write-Host "   $Details" -ForegroundColor Yellow
        }
        $script:Errors++
    }
}

# Funcion para buscar patrones en archivos
function Search-Patterns {
    param(
        [string]$FilePath,
        [string[]]$Patterns
    )
    
    $results = @()
    if (Test-Path $FilePath) {
        $content = Get-Content $FilePath -Raw
        foreach ($pattern in $Patterns) {
            if ($content -match $pattern) {
                $results += $pattern
            }
        }
    }
    return $results
}

# Funcion para analizar archivo especifico
function Test-AuthFile {
    param(
        [string]$FilePath,
        [string]$FileName
    )
    
    if (-not (Test-Path $FilePath)) {
        Show-Result $false "$FileName no encontrado" $FilePath
        return
    }
    
    $content = Get-Content $FilePath -Raw
    Write-Host ""
    Write-Host "   >> Analizando: $FileName" -ForegroundColor Yellow
    
    # Patrones de autenticacion
    $authPatterns = @(
        "Auth\.signIn",
        "Auth\.signOut",
        "Auth\.federatedSignIn",
        "Auth\.currentAuthenticatedUser",
        "useSelector.*auth",
        "useAppSelector.*auth"
    )
    
    # Patrones de navegacion protegida
    $navPatterns = @(
        "navigation\.navigate.*Login",
        "if.*user.*navigation",
        "isAuthenticated",
        "authState"
    )
    
    # Patrones de datos reales vs mock
    $dataPatterns = @(
        "USE_MOCK_DATA.*false",
        "API\.graphql",
        "client\.graphql",
        "mockData",
        "mockBoats"
    )
    
    $foundAuth = Search-Patterns -FilePath $FilePath -Patterns $authPatterns
    $foundNav = Search-Patterns -FilePath $FilePath -Patterns $navPatterns
    $foundData = Search-Patterns -FilePath $FilePath -Patterns $dataPatterns
    
    if ($foundAuth.Count -gt 0) {
        Show-Result $true "Metodos de Auth" "$($foundAuth -join ', ')"
    }
    
    if ($foundNav.Count -gt 0) {
        Show-Result $true "Navegacion protegida" "$($foundNav -join ', ')"
    }
    
    if ($foundData.Count -gt 0) {
        $usingMock = $content -match "USE_MOCK_DATA.*true" -or $content -match "mockData" -or $content -match "mockBoats"
        if ($usingMock) {
            Show-Result $false "Usando datos MOCK" "Cambiar a datos reales"
        } else {
            Show-Result $true "Usando datos reales" "$($foundData -join ', ')"
        }
    }
}

# Contador de errores
$script:Errors = 0

Write-Host ""
Write-Host "Iniciando verificacion FASE 2..." -ForegroundColor Blue

# 1. Verificar pantallas principales con autenticacion
Write-Host ""
Write-Host "1. VERIFICANDO PANTALLAS PRINCIPALES..."

$screenFiles = @(
    @{ Path = "src\screens\auth\LoginScreen.tsx"; Name = "LoginScreen" },
    @{ Path = "src\screens\auth\RegisterScreen.tsx"; Name = "RegisterScreen" },
    @{ Path = "src\screens\home\HomeScreen.tsx"; Name = "HomeScreen" },
    @{ Path = "src\screens\boats\BoatDetailsScreen.tsx"; Name = "BoatDetailsScreen" },
    @{ Path = "src\screens\booking\BookingScreen.tsx"; Name = "BookingScreen" },
    @{ Path = "src\screens\bookings\BookingsScreen.tsx"; Name = "BookingsScreen" },
    @{ Path = "src\screens\payment\PaymentScreen.tsx"; Name = "PaymentScreen" },
    @{ Path = "src\screens\profile\ProfileScreen.tsx"; Name = "ProfileScreen" },
    @{ Path = "src\screens\search\SearchScreen.tsx"; Name = "SearchScreen" }
)

foreach ($screen in $screenFiles) {
    Test-AuthFile -FilePath $screen.Path -FileName $screen.Name
}

# 2. Verificar servicios de autenticacion
Write-Host ""
Write-Host "2. VERIFICANDO SERVICIOS DE AUTENTICACION..."

$serviceFiles = @(
    @{ Path = "src\services\authService.ts"; Name = "AuthService" },
    @{ Path = "src\store\slices\authSlice.ts"; Name = "AuthSlice" }
)

foreach ($service in $serviceFiles) {
    Test-AuthFile -FilePath $service.Path -FileName $service.Name
}

# 3. Verificar navegacion protegida
Write-Host ""
Write-Host "3. VERIFICANDO NAVEGACION PROTEGIDA..."

$navFiles = @(
    "src\navigation\AppNavigator.tsx",
    "src\navigation\AuthNavigator.tsx",
    "src\navigation\index.tsx"
)

foreach ($navFile in $navFiles) {
    if (Test-Path $navFile) {
        Write-Host ""
        Write-Host "   >> Analizando: $(Split-Path $navFile -Leaf)" -ForegroundColor Yellow
        
        $protectionPatterns = @(
            "isAuthenticated",
            "user.*null",
            "authState",
            "Auth\.currentAuthenticatedUser",
            "useSelector.*auth"
        )
        
        $foundProtection = Search-Patterns -FilePath $navFile -Patterns $protectionPatterns
        if ($foundProtection.Count -gt 0) {
            Show-Result $true "Navegacion protegida implementada" "$($foundProtection -join ', ')"
        } else {
            Show-Result $false "Sin proteccion de navegacion" "Implementar guards de autenticacion"
        }
    } else {
        Show-Result $false "Archivo de navegacion no encontrado" $navFile
    }
}

# 4. Verificar configuracion de Amplify
Write-Host ""
Write-Host "4. VERIFICANDO CONFIGURACION DE AMPLIFY..."

$configFiles = @(
    @{ Path = "src\config\amplifyConfig.ts"; Name = "AmplifyConfig" },
    @{ Path = "src\aws-exports.js"; Name = "AWS Exports" }
)

foreach ($config in $configFiles) {
    if (Test-Path $config.Path) {
        if ($config.Name -eq "AmplifyConfig") {
            $patterns = @(
                "import.*Amplify",
                "Amplify\.configure",
                "awsconfig"
            )
        } else {
            $patterns = @(
                "aws_user_pools_id",
                "aws_appsync_graphqlEndpoint",
                "oauth"
            )
        }
        
        $found = Search-Patterns -FilePath $config.Path -Patterns $patterns
        if ($found.Count -gt 0) {
            Show-Result $true "$($config.Name) configurado" "$($found.Count) configuraciones encontradas"
        } else {
            Show-Result $false "$($config.Name) mal configurado" "Revisar configuracion"
        }
    } else {
        Show-Result $false "$($config.Name) no encontrado" $config.Path
    }
}

# 5. Verificar uso de datos reales vs mock
Write-Host ""
Write-Host "5. VERIFICANDO USO DE DATOS REALES..."

$dataServiceFiles = @(
    "src\services\boatsService.ts",
    "src\services\bookingsService.ts",
    "src\services\reservationsService.ts"
)

$mockUsageCount = 0
$realDataCount = 0

foreach ($serviceFile in $dataServiceFiles) {
    if (Test-Path $serviceFile) {
        $content = Get-Content $serviceFile -Raw
        $fileName = Split-Path $serviceFile -Leaf
        
        Write-Host ""
        Write-Host "   >> Analizando: $fileName" -ForegroundColor Yellow
        
        if ($content -match "USE_MOCK_DATA.*true" -or $content -match "mockData" -or $content -match "mockBoats") {
            Show-Result $false "Usando datos MOCK" "Cambiar a datos reales para produccion"
            $mockUsageCount++
        } elseif ($content -match "API\.graphql" -or $content -match "client\.graphql") {
            Show-Result $true "Usando datos reales" "GraphQL API configurado"
            $realDataCount++
        } else {
            Show-Result $false "Configuracion de datos unclear" "Revisar implementacion"
        }
    }
}

# 6. Verificar hooks tipados de Redux
Write-Host ""
Write-Host "6. VERIFICANDO HOOKS TIPADOS DE REDUX..."

$hooksPath = "src\store\hooks.ts"
if (Test-Path $hooksPath) {
    $hookPatterns = @(
        "useAppDispatch",
        "useAppSelector",
        "TypedUseSelectorHook"
    )
    
    $foundHooks = Search-Patterns -FilePath $hooksPath -Patterns $hookPatterns
    if ($foundHooks.Count -ge 2) {
        Show-Result $true "Hooks tipados configurados" "$($foundHooks -join ', ')"
    } else {
        Show-Result $false "Hooks tipados incompletos" "Configurar useAppDispatch y useAppSelector"
    }
} else {
    Show-Result $false "Archivo de hooks no encontrado" $hooksPath
}

# 7. Buscar uso incorrecto de hooks genericos
Write-Host ""
Write-Host "7. VERIFICANDO USO CORRECTO DE HOOKS..."

$allTsxFiles = Get-ChildItem -Path "src" -Filter "*.tsx" -Recurse
$incorrectHookUsage = 0

foreach ($file in $allTsxFiles) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match "useDispatch<AppDispatch>" -or $content -match "useSelector.*RootState") {
        $incorrectHookUsage++
        Write-Host "   [!] Uso de hooks genericos en: $($file.Name)" -ForegroundColor Yellow
    }
}

if ($incorrectHookUsage -eq 0) {
    Show-Result $true "Hooks utilizados correctamente" "No se encontraron usos genericos"
} else {
    Show-Result $false "Uso incorrecto de hooks encontrado" "$incorrectHookUsage archivos con hooks genericos"
}

# Resumen final FASE 2
Write-Host ""
Write-Host "RESUMEN FASE 2 - AUTENTICACION" -ForegroundColor Blue
Write-Host "================================="

Write-Host ""
Write-Host "Estadisticas:" -ForegroundColor Yellow
Write-Host "- Pantallas analizadas: $($screenFiles.Count)"
Write-Host "- Servicios verificados: $($serviceFiles.Count)"
Write-Host "- Archivos usando datos reales: $realDataCount"
Write-Host "- Archivos usando datos mock: $mockUsageCount"
Write-Host "- Errores encontrados: $script:Errors"

if ($script:Errors -eq 0) {
    Write-Host ""
    Write-Host "FASE 2 COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "[OK] Autenticacion completamente configurada" -ForegroundColor Green
    Write-Host "[OK] Navegacion protegida implementada" -ForegroundColor Green
    Write-Host "[OK] Hooks tipados configurados" -ForegroundColor Green
    Write-Host ""
    Write-Host "LISTO PARA FASE 3:" -ForegroundColor Blue
    Write-Host "- Verificacion de APIs GraphQL"
    Write-Host "- Integracion completa de servicios"
    Write-Host "- Testing end-to-end"
} else {
    Write-Host ""
    Write-Host "FASE 2 INCOMPLETA" -ForegroundColor Red
    Write-Host "[ERROR] $script:Errors errores encontrados" -ForegroundColor Red
    Write-Host ""
    Write-Host "Acciones requeridas:" -ForegroundColor Yellow
    Write-Host "- Corregir errores de autenticacion"
    Write-Host "- Implementar navegacion protegida"
    Write-Host "- Cambiar de mock data a datos reales"
    Write-Host "- Configurar hooks tipados"
}

Write-Host ""
Write-Host "Verificacion FASE 2 completada" -ForegroundColor Cyan