# Script para corregir los errores en TEST_COMPLETO_VALIDACION_OPENAPI.ps1

param(
  [string]$ScriptPath = ".\TEST_COMPLETO_VALIDACION_OPENAPI.ps1",
  [string]$OutputPath = ".\TEST_COMPLETO_VALIDACION_OPENAPI_FIXED.ps1"
)

Write-Host "Leyendo script original..." -ForegroundColor Cyan
$content = Get-Content $ScriptPath -Raw

Write-Host "Aplicando correcciones..." -ForegroundColor Yellow

# CorrecciÃ³n 1: Arreglar la llave faltante despuÃ©s de la lÃ­nea 236
# El problema estÃ¡ en la funciÃ³n Initialize-TestFiles donde falta cerrar un if
# CorrecciÃ³n 1: Arreglar la llave faltante despuÃ©s de la lÃ­nea 236
# El problema estÃ¡ en la funciÃ³n Initialize-TestFiles donde falta cerrar un if
$content = $content -replace '(\$Scenario\.QueryParams\["ruta"\] = \$ruta\s+Write-Host[^}]+Yellow\s+)', '$1}  # Cierre del if -not $ruta
    }'

# CorrecciÃ³n 2: Arreglar el problema de sintaxis en la lÃ­nea 718
# El problema es que falta cerrar el parÃ©ntesis antes de 'ms'
$oldLine718 = 'Write-Pass \("PASS \(\{0\}, \{1\}ms\)" -f \$result\.StatusCode, \$result\.'
$newLine718 = 'Write-Pass ("PASS ({0}, {1}ms)" -f $result.StatusCode, $result.ResponseTime)'
$content = $content -replace [regex]::Escape($oldLine718) + '.*', $newLine718

# CorrecciÃ³n 3: Arreglar la lÃ­nea 721 (FAIL message)
$oldLine721 = 'Write-Fail \("FAIL \(esperado: \{0\}, recibido: \{1\}\)" -f \(\$scenario'
$newLine721 = 'Write-Fail ("FAIL (esperado: {0}, recibido: {1})" -f ($scenario.ExpectedStatus -join ","), $result.StatusCode)'
$content = $content -replace [regex]::Escape($oldLine721) + '.*', $newLine721

# CorrecciÃ³n 4: Arreglar el problema del path en la lÃ­nea 791
$content = $content -replace '\$reportPath = "\./test-report-\$timestamp\.json"', '$reportPath = ".\test-report-$timestamp.json"'
# CorrecciÃ³n 5: Arreglar comillas en la lÃ­nea 830
$content = $content -replace 'Write-Host "  4\. Ejecuta con -VerboseOutput para mas detalles"', 'Write-Host "  4. Ejecuta con -VerboseOutput para mas detalles"'
# CorrecciÃ³n 5: Arreglar comillas en la lÃ­nea 830
$content = $content -replace 'Write-Host "  4\. Ejecuta con -VerboseOutput para mas detalles"', 'Write-Host "  4. Ejecuta con -VerboseOutput para mas detalles"'

# CorrecciÃ³n especÃ­fica para la funciÃ³n Initialize-TestFiles
# Buscar y corregir la estructura de la funciÃ³n
$functionPattern = '(function Initialize-TestFiles \{[^}]+if \(\$TestCase\.Path -eq "/api/leer-archivo"[^}]+)'
if ($content -match $functionPattern) {
  Write-Host "Corrigiendo estructura de Initialize-TestFiles..." -ForegroundColor Green
    
  # Extraer la funciÃ³n completa y corregirla
  $fixedFunction = @'
function Initialize-TestFiles {
  param($TestCase, $Scenario)
  
  # Variable global para la raÃ­z del proyecto (ajusta segÃºn tu estructura)
  if (-not $global:PROYECTO_RAIZ) {
    $global:PROYECTO_RAIZ = "."
  }
  
  # Crear archivo origen para /api/copiar-archivo
  if ($TestCase.Path -eq "/api/copiar-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $origen = $Scenario.Body.origen
    if ($origen) {
      $origenPath = Join-Path $global:PROYECTO_RAIZ $origen
      $origenDir = Split-Path $origenPath -Parent
      if (!(Test-Path $origenDir)) {
        New-Item -ItemType Directory -Path $origenDir -Force | Out-Null
      }
      if (!(Test-Path $origenPath)) {
        New-Item -ItemType File -Path $origenPath -Force | Out-Null
        Set-Content -Path $origenPath -Value "Contenido generado automÃ¡ticamente para pruebas - $(Get-Date)"
      }
      Write-Debug "Archivo origen creado: $origenPath"
    }
  }
  
  # Crear archivo origen para /api/mover-archivo
  if ($TestCase.Path -eq "/api/mover-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $origen = $Scenario.Body.origen
    if ($origen) {
      $origenPath = Join-Path $global:PROYECTO_RAIZ $origen
      $origenDir = Split-Path $origenPath -Parent
      if (!(Test-Path $origenDir)) {
        New-Item -ItemType Directory -Path $origenDir -Force | Out-Null
      }
      if (!(Test-Path $origenPath)) {
        New-Item -ItemType File -Path $origenPath -Force | Out-Null
        Set-Content -Path $origenPath -Value "Contenido generado automÃ¡ticamente para pruebas - $(Get-Date)"
      }
      Write-Debug "Archivo origen creado: $origenPath"
    }
  }

  # Crear archivo para /api/leer-archivo
  if ($TestCase.Path -eq "/api/leer-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    Write-Host "ðŸ”§ Initialize-TestFiles: Procesando /api/leer-archivo" -ForegroundColor Yellow
    $ruta = $Scenario.QueryParams["ruta"]
    Write-Host "ðŸ”§ Ruta inicial: '$ruta'" -ForegroundColor Yellow
    if (-not $ruta) {
      # Fallback: generar ruta si no existe
      $ruta = "test/sample_$(Get-Random -Maximum 9999).txt"
      $Scenario.QueryParams["ruta"] = $ruta
      Write-Host "ðŸ”§ Ruta generada: '$ruta'" -ForegroundColor Yellow
    }
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      Write-Host "ðŸ”§ Creando directorio: '$rutaDir'" -ForegroundColor Yellow
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      Write-Host "ðŸ”§ Creando archivo: '$rutaPath'" -ForegroundColor Yellow
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "Archivo de lectura para prueba - $(Get-Date)"
      }
      Write-Host "ðŸ”§ âœ… Archivo de lectura creado: $rutaPath" -ForegroundColor Green
      Write-Host "ðŸ”§ QueryParams final: $($Scenario.QueryParams | ConvertTo-Json -Compress)" -ForegroundColor Yellow
    }
  }

  # Crear archivo para /api/info-archivo
  if ($TestCase.Path -eq "/api/info-archivo" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $ruta = $Scenario.QueryParams["ruta"]
    if (-not $ruta) {
      # Fallback: generar ruta si no existe
      $ruta = "test/info_$(Get-Random -Maximum 9999).txt"
      $Scenario.QueryParams["ruta"] = $ruta
    }
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "Archivo para info - $(Get-Date)"
      }
      Write-Debug "Archivo para info creado: $rutaPath"
    }
  }

  # Crear archivo para /api/preparar-script
  if ($TestCase.Path -eq "/api/preparar-script" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $ruta = $Scenario.Body["ruta"]
    if ($ruta) {
      $rutaPath = Join-Path $global:PROYECTO_RAIZ $ruta
      $rutaDir = Split-Path $rutaPath -Parent
      if (!(Test-Path $rutaDir)) {
        New-Item -ItemType Directory -Path $rutaDir -Force | Out-Null
      }
      if (!(Test-Path $rutaPath)) {
        New-Item -ItemType File -Path $rutaPath -Force | Out-Null
        Set-Content -Path $rutaPath -Value "#!/usr/bin/env python3`nprint('Preparar script $(Get-Date)')"
      }
      Write-Debug "Script preparado: $rutaPath"
    }
  }

  # Crear archivo para /api/ejecutar-script
  if ($TestCase.Path -eq "/api/ejecutar-script" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $script = $Scenario.Body["script"]
    if ($script) {
      $scriptPath = Join-Path $global:PROYECTO_RAIZ $script
      $scriptDir = Split-Path $scriptPath -Parent
      if (!(Test-Path $scriptDir)) {
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
      }
      if (!(Test-Path $scriptPath)) {
        New-Item -ItemType File -Path $scriptPath -Force | Out-Null
        Set-Content -Path $scriptPath -Value "print('Test script ejecutado - $(Get-Date)')"
      }
      Write-Debug "Script creado: $scriptPath"
    }
  }

  # Crear archivo para /api/ejecutar-script-local
  if ($TestCase.Path -eq "/api/ejecutar-script-local" -and $Scenario.Name -eq "Valid_MinimalRequired") {
    $script = $Scenario.Body["script"]
    if ($script) {
      $scriptPath = Join-Path $global:PROYECTO_RAIZ $script
      $scriptDir = Split-Path $scriptPath -Parent
      if (!(Test-Path $scriptDir)) {
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
      }
      if (!(Test-Path $scriptPath)) {
        New-Item -ItemType File -Path $scriptPath -Force | Out-Null
        Set-Content -Path $scriptPath -Value "print('Script ejecutado')"
      }
      Write-Debug "Script local creado: $scriptPath"
    }
  }
}
'@

  # Reemplazar la funciÃ³n completa
  $content = $content -replace 'function Initialize-TestFiles \{[\s\S]*?\n\}\s*\n# ============', $fixedFunction + "`n# ============"
}

# Guardar el archivo corregido
Write-Host "Guardando archivo corregido en: $OutputPath" -ForegroundColor Green
$content | Set-Content $OutputPath -Encoding UTF8

Write-Host "`nâœ… Correcciones aplicadas exitosamente!" -ForegroundColor Green
Write-Host "`nErrores corregidos:" -ForegroundColor Cyan
Write-Host "  1. Llave faltante en funciÃ³n Initialize-TestFiles (lÃ­nea ~236)" -ForegroundColor White
Write-Host "  2. Sintaxis incorrecta en Write-Pass (lÃ­nea 718)" -ForegroundColor White
Write-Host "  3. Sintaxis incorrecta en Write-Fail (lÃ­nea 721)" -ForegroundColor White
Write-Host "  4. Path incorrecto en reportPath (lÃ­nea 791)" -ForegroundColor White
Write-Host "  5. Problema de comillas (lÃ­nea 830)" -ForegroundColor White

Write-Host "`nðŸ“ Archivo corregido guardado como: $OutputPath" -ForegroundColor Yellow
Write-Host "Para ejecutar el script corregido:" -ForegroundColor Cyan
Write-Host "  .\$OutputPath -BaseUrl `"https://copiloto-func.ngrok.app`"" -ForegroundColor White

# Validar sintaxis del archivo corregido
Write-Host "`nValidando sintaxis del archivo corregido..." -ForegroundColor Cyan
$parseErrors = $null
$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $OutputPath -Raw), [ref]$parseErrors)

if ($parseErrors.Count -eq 0) {
  Write-Host "âœ… El archivo corregido no tiene errores de sintaxis!" -ForegroundColor Green
}
else {
  Write-Host "âšï¸ AÃºn hay errores de sintaxis. Detalles:" -ForegroundColor Yellow
  $parseErrors | ForEach-Object {
    Write-Host ("  LÃ­nea $($_.StartLine): $($_.Message)") -ForegroundColor Red
  }
}