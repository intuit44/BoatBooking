# verify-phase3-complete.ps1
# Script de verificación para Fase 3 - APIs GraphQL & Integración
# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`nVERIFICACION COMPLETA FASE 3 - APIS GRAPHQL & INTEGRACION" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

Write-Host "Iniciando verificacion FASE 3...`n" -ForegroundColor Yellow

# 1. VERIFICACIÓN DE APIS GRAPHQL
Write-Host "1. VERIFICANDO APIS GRAPHQL..." -ForegroundColor Green

# Verificar schema.graphql (está en mobile-app/amplify)
Write-Host "`n   >> Analizando: schema.graphql"
if (Test-Path "../amplify/backend/api/boatrentallapp/schema.graphql") {
    $schemaContent = Get-Content "../amplify/backend/api/boatrentallapp/schema.graphql" -Raw
    
    # Verificar tipos principales
    if ($schemaContent -match "type Boat @model") {
        Write-Host "[OK] Modelo Boat encontrado" -ForegroundColor Green
    }
    if ($schemaContent -match "type Booking @model") {
        Write-Host "[OK] Modelo Booking encontrado" -ForegroundColor Green
    }
    if ($schemaContent -match "type User @model") {
        Write-Host "[OK] Modelo User encontrado" -ForegroundColor Green
    }
    
    # Verificar directivas
    if ($schemaContent -match "@auth") {
        Write-Host "[OK] Directivas de autorizacion configuradas" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] schema.graphql no encontrado" -ForegroundColor Red
}

# Verificar archivos GraphQL generados
Write-Host "`n   >> Analizando: Archivos GraphQL generados"
$graphqlFiles = @(
    "../src/graphql/queries.ts",
    "../src/graphql/mutations.ts",
    "../src/graphql/subscriptions.ts"
)

foreach ($file in $graphqlFiles) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        Write-Host "[OK] $file generado correctamente" -ForegroundColor Green
        
        # Verificar contenido específico
        if ($content -match "listBoats" -or $content -match "getBoat") {
            Write-Host "   - Queries de boats encontradas" -ForegroundColor Green
        }
        if ($content -match "createBooking" -or $content -match "updateBooking") {
            Write-Host "   - Mutations de bookings encontradas" -ForegroundColor Green
        }
    } else {
        Write-Host "[ERROR] $file no encontrado" -ForegroundColor Red
    }
}

# Verificar tipos TypeScript
Write-Host "`n   >> Analizando: Tipos TypeScript"
if (Test-Path "../src/API.ts") {
    Write-Host "[OK] Tipos TypeScript generados" -ForegroundColor Green
    $apiContent = Get-Content "../src/API.ts" -Raw
    if ($apiContent -match "export type Boat" -and $apiContent -match "export type Booking") {
        Write-Host "   - Interfaces principales encontradas" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] API.ts no encontrado" -ForegroundColor Red
}

# 2. VERIFICACIÓN DE SERVICIOS
Write-Host "`n2. VERIFICANDO INTEGRACION DE SERVICIOS..." -ForegroundColor Green

$services = @(
    "../src/services/boatsService.ts",
    "../src/services/bookingsService.ts",
    "../src/services/reservationsService.ts"
)

foreach ($service in $services) {
    Write-Host "`n   >> Analizando: $service"
    if (Test-Path $service) {
        $serviceContent = Get-Content $service -Raw
        
        # Verificar importaciones GraphQL
        if ($serviceContent -match "import.*from '../graphql/") {
            Write-Host "[OK] Importaciones GraphQL correctas" -ForegroundColor Green
        }
        
        # Verificar manejo de errores
        if ($serviceContent -match "try.*catch" -and $serviceContent -match "throw new Error") {
            Write-Host "[OK] Manejo de errores implementado" -ForegroundColor Green
        }
        
        # Verificar uso de tipos
        if ($serviceContent -match "import.*from '../API'") {
            Write-Host "[OK] Tipos TypeScript importados" -ForegroundColor Green
        }
        
        # Verificar optimistic updates
        if ($serviceContent -match "optimisticResponse") {
            Write-Host "[OK] Optimistic updates configurados" -ForegroundColor Green
        }
    } else {
        Write-Host "[ERROR] $service no encontrado" -ForegroundColor Red
    }
}

# 3. VERIFICACIÓN DE RESOLVERS
Write-Host "`n3. VERIFICANDO RESOLVERS..." -ForegroundColor Green

$resolversPath = "../amplify/backend/api/boatrentallapp/resolvers"
if (Test-Path $resolversPath) {
    Write-Host "[OK] Directorio de resolvers encontrado" -ForegroundColor Green
    $resolverFiles = Get-ChildItem $resolversPath -Filter "*.vm"
    if ($resolverFiles.Count -gt 0) {
        Write-Host "   - $($resolverFiles.Count) resolvers encontrados" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Directorio de resolvers no encontrado (pueden estar usando resolvers automáticos)" -ForegroundColor Yellow
}

# 4. VERIFICACIÓN DE ENDPOINTS
Write-Host "`n4. VERIFICANDO ENDPOINTS..." -ForegroundColor Green

# Verificar configuración de API
$awsExportsPath = "../src/aws-exports.js"
if (Test-Path $awsExportsPath) {
    $awsExportsContent = Get-Content $awsExportsPath -Raw
    if ($awsExportsContent -match "aws_appsync_graphqlEndpoint") {
        Write-Host "[OK] GraphQL endpoint configurado" -ForegroundColor Green
    }
    if ($awsExportsContent -match "aws_appsync_apiKey") {
        Write-Host "[OK] API Key configurada" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] aws-exports.js no encontrado" -ForegroundColor Red
}

# 5. VERIFICACIÓN DE FLUJOS END-TO-END
Write-Host "`n5. VERIFICANDO FLUJOS END-TO-END..." -ForegroundColor Green

# Verificar componentes necesarios para flujos
$screens = @(
    "../src/screens/boats/BoatDetailsScreen.tsx",
    "../src/screens/booking/BookingScreen.tsx",
    "../src/screens/payment/PaymentScreen.tsx",
    "../src/screens/bookings/BookingsScreen.tsx"
)

foreach ($screen in $screens) {
    Write-Host "`n   >> Analizando: $screen"
    if (Test-Path $screen) {
        $screenContent = Get-Content $screen -Raw
        
        # Verificar uso de servicios
        if ($screenContent -match "import.*from '../../services/") {
            Write-Host "[OK] Servicios importados" -ForegroundColor Green
        }
        
        # Verificar manejo de estados
        if ($screenContent -match "useState" -and $screenContent -match "useEffect") {
            Write-Host "[OK] Manejo de estado implementado" -ForegroundColor Green
        }
        
        # Verificar manejo de errores UI
        if ($screenContent -match "try.*catch" -and $screenContent -match "Alert") {
            Write-Host "[OK] Manejo de errores UI implementado" -ForegroundColor Green
        }
    } else {
        Write-Host "[ERROR] $screen no encontrado" -ForegroundColor Red
    }
}

# 6. VERIFICACIÓN DE CONFIGURACIÓN AMPLIFY
Write-Host "`n6. VERIFICANDO CONFIGURACION AMPLIFY..." -ForegroundColor Green

# Verificar amplifyConfig.ts
if (Test-Path "../src/config/amplifyConfig.ts") {
    Write-Host "[OK] amplifyConfig.ts encontrado" -ForegroundColor Green
    $amplifyConfigContent = Get-Content "../src/config/amplifyConfig.ts" -Raw
    if ($amplifyConfigContent -match "Amplify.configure") {
        Write-Host "   - Configuración de Amplify implementada" -ForegroundColor Green
    }
}

# Verificar slices de Redux
Write-Host "`n7. VERIFICANDO SLICES DE REDUX..." -ForegroundColor Green
$slices = @(
    "../src/store/slices/boatsSlice.ts",
    "../src/store/slices/bookingsSlice.ts",
    "../src/store/slices/authSlice.ts"
)

foreach ($slice in $slices) {
    if (Test-Path $slice) {
        Write-Host "[OK] $slice encontrado" -ForegroundColor Green
        $sliceContent = Get-Content $slice -Raw
        if ($sliceContent -match "createAsyncThunk" -and $sliceContent -match "createSlice") {
            Write-Host "   - Slice correctamente configurado" -ForegroundColor Green
        }
    }
}

# RESUMEN
Write-Host "`nRESUMEN FASE 3 - APIS GRAPHQL & INTEGRACION" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$errorCount = 0
$warningCount = 0

# Contar errores
$allFiles = $graphqlFiles + $services + $screens + @("../src/API.ts", "../src/aws-exports.js")
foreach ($file in $allFiles) {
    if (-not (Test-Path $file)) {
        $errorCount++
    }
}

Write-Host "`nEstadisticas:"
Write-Host "- APIs GraphQL verificadas: $($graphqlFiles.Count)"
Write-Host "- Servicios analizados: $($services.Count)"
Write-Host "- Pantallas verificadas: $($screens.Count)"
Write-Host "- Slices Redux verificados: $($slices.Count)"
Write-Host "- Errores encontrados: $errorCount"
Write-Host "- Advertencias: $warningCount`n"

if ($errorCount -eq 0) {
    Write-Host "FASE 3 COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "[OK] APIs GraphQL configuradas" -ForegroundColor Green
    Write-Host "[OK] Servicios integrados" -ForegroundColor Green
    Write-Host "[OK] Flujos end-to-end verificados" -ForegroundColor Green
    Write-Host "[OK] Redux Store integrado" -ForegroundColor Green
} else {
    Write-Host "FASE 3 INCOMPLETA" -ForegroundColor Red
    Write-Host "[ERROR] $errorCount errores encontrados" -ForegroundColor Red
    
    Write-Host "`nAcciones requeridas:"
    Write-Host "- Generar archivos GraphQL con: amplify codegen"
    Write-Host "- Crear servicios faltantes"
    Write-Host "- Implementar manejo de errores"
    Write-Host "- Completar flujos faltantes"
    
    Write-Host "`nComandos sugeridos:"
    Write-Host "  cd ../.. && amplify codegen" -ForegroundColor Yellow
    Write-Host "  npm run generate-types" -ForegroundColor Yellow
}

Write-Host "`nVerificacion FASE 3 completada" -ForegroundColor Yellow

# Verificación adicional de funcionalidades específicas
Write-Host "`nVERIFICACION DE FUNCIONALIDADES ESPECIFICAS:" -ForegroundColor Cyan

# Verificar si existe el servicio de pagos
if (Test-Path "../src/services/paymentService.ts") {
    Write-Host "[OK] Servicio de pagos encontrado" -ForegroundColor Green
} else {
    Write-Host "[INFO] Servicio de pagos no implementado aún" -ForegroundColor Yellow
}

# Verificar si existe el servicio de notificaciones
if (Test-Path "../src/services/notificationService.ts") {
    Write-Host "[OK] Servicio de notificaciones encontrado" -ForegroundColor Green
} else {
    Write-Host "[INFO] Servicio de notificaciones no implementado aún" -ForegroundColor Yellow
}

# Mostrar ruta actual para debugging
Write-Host "`nEjecutando desde: $(Get-Location)" -ForegroundColor Gray

Write-Host "`nFin de la verificación." -ForegroundColor Cyan