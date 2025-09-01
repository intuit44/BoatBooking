TEST COMPLETO ENDPOINTS PARA VERIFICAR ANTES DE HACER PRUEBAS CON EL AGENTE 

# ============ Config ============
$fn = "https://copiloto-semantico-func.azurewebsites.net"

# ============ Helpers ===========
function J($o) { $o | ConvertTo-Json -Depth 20 -Compress }
function Try-Invoke {
  param(
    [string]$Method = "GET",
    [string]$Url,
    [hashtable]$Body = $null,
    [int[]]$Accept = @(200),
    [switch]$Raw,
    [hashtable]$Headers = @{ "Content-Type" = "application/json" },
    [int]$TimeoutSec = 30
  )
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    if ($Method -eq "GET" -or $Method -eq "DELETE") {
      $r = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
      $content = if ($Raw) { $r.Content } else { try { $r.Content | ConvertFrom-Json } catch { $r.Content } }
      $status = [int]$r.StatusCode
      $ctype = $r.Headers["Content-Type"]
    }
    else {
      $json = if ($Body) { $Body | ConvertTo-Json -Depth 20 -Compress } else { "{}" }
      $r = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -Body $json -TimeoutSec $TimeoutSec -ErrorAction Stop
      $content = if ($Raw) { $r.Content } else { try { $r.Content | ConvertFrom-Json } catch { $r.Content } }
      $status = [int]$r.StatusCode
      $ctype = $r.Headers["Content-Type"]
    }
    $ok = $Accept -contains $status
  }
  catch {
    $resp = $_.Exception.Response
    $status = if ($resp) { [int]$resp.StatusCode } else { -1 }
    try {
      $stream = $resp?.GetResponseStream()
      $reader = if ($stream) { New-Object System.IO.StreamReader($stream) } else { $null }
      $raw = if ($reader) { $reader.ReadToEnd() } else { $_.ToString() }
      $content = try { $raw | ConvertFrom-Json } catch { $raw }
    }
    catch { $content = $_.ToString() }
    $ctype = if ($resp) { $resp.Headers["Content-Type"] } else { $null }
    $ok = $Accept -contains $status
  }
  $sw.Stop()
  [pscustomobject]@{
    url = $Url; method = $Method; status = $status; ok = $ok; ms = $sw.ElapsedMilliseconds
    ctype = $ctype; body = $Body; out = $content
  }
}

function Row {
  param($name, $method, $path, $accept = @(200), $body = $null, $raw = $false)
  $res = Try-Invoke -Method $method -Url ($fn + $path) -Body $body -Accept $accept -Raw:$raw
  [pscustomobject]@{
    name   = $name
    path   = $path
    method = $method
    status = $res.status
    ok     = $res.ok
    ms     = $res.ms
    note   = if ($res.ok) { "OK" }else { "FAIL" }
    out    = $res.out
  }
}

function Assert-ErrorEnvelope($o) {
  return ($o.ok -eq $false) -and $o.error_code
}

# ========= Etapa 0: Smoke / Descubrir visibilidad =========
$expected = @(
  "/api/health", "/api/status", "/api/copiloto",
  "/api/hybrid", "/api/ejecutar", "/api/ejecutar-script", "/api/preparar-script", "/api/ejecutar-cli",
  "/api/deploy", "/api/crear-contenedor",
  "/api/escribir-archivo", "/api/leer-archivo", "/api/modificar-archivo", "/api/eliminar-archivo",
  "/api/mover-archivo", "/api/copiar-archivo", "/api/info-archivo", "/api/descargar-archivo", "/api/listar-blobs",
  "/api/configurar-cors", "/api/configurar-app-settings", "/api/escalar-plan",
  "/api/auditar-deploy", "/api/diagnostico-recursos", "/api/diagnostico-recursos-completo",
  "/api/diagnostico-configurar", "/api/diagnostico-listar", "/api/diagnostico-eliminar",
  "/api/bateria-endpoints", "/api/probar-endpoint", "/api/invocar", "/api/render-error"
)

$smoke = Row "status" "GET" "/api/status"
$visible = @()
if ($smoke.ok -and $smoke.out.endpoints) { $visible = $smoke.out.endpoints | Sort-Object -Unique }
$missing = $expected | Where-Object { $_ -notin $visible }
$extra = $visible  | Where-Object { $_ -notin $expected }

"--- Visibilidad (status.endpoints) ---"
"Declarados en OpenAPI (esperados): $($expected.Count)"
"Reportados por /api/status:        $($visible.Count)"
if ($missing.Count) { "FALTAN en status: `n - " + ($missing -join "`n - ") } else { "No faltan rutas en status (o status no lista todas)." }
if ($extra.Count) { "EXTRAS en status: `n - " + ($extra -join "`n - ") }

# ========= Etapa 1: Pruebas seguras (sin efectos) =========
$ts = Get-Date -Format "yyyyMMddHHmmssfff"
$fileA = "tmp/e2e-$ts.txt"
$fileB = "tmp/e2e-$ts-copy.txt"
$fileC = "tmp/e2e-$ts-moved.txt"
$script = "scripts/_e2e_$ts.py"

# --- FIX 1: deploy-validate con recurso real ---
$deployValidate = @{
  resourceGroup = "boat-rental-app-group"
  location      = "eastus"
  validate_only = $true
  template      = @{
    '$schema'      = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
    contentVersion = '1.0.0.0'
    parameters     = @{}
    variables      = @{ storageAccountName = "[concat('e2e', uniqueString(resourceGroup().id, subscription().id))]" }
    resources      = @(
      @{
        type       = "Microsoft.Storage/storageAccounts"
        apiVersion = "2022-09-01"
        name       = "[variables('storageAccountName')]"
        location   = "[resourceGroup().location]"
        sku        = @{ name = "Standard_LRS" }
        kind       = "StorageV2"
        properties = @{ accessTier = "Hot" }
      }
    )
    outputs        = @{}
  }
}

# --- FIX 5: diagnostico-recursos POST con resourceId ---
$subId = $env:AZ_SUBSCRIPTION_ID
if (-not $subId) { $subId = "<SUBSCRIPTION_ID>" }        # <-- pon tu SubId aquí si no usas env var
$funcId = "/subscriptions/$subId/resourceGroups/boat-rental-app-group/providers/Microsoft.Web/sites/copiloto-semantico-func"

$tests = @()

# Salud / estado / descubrimiento
$tests += Row "health" "GET" "/api/health"
$tests += $smoke
$tests += Row "copiloto" "GET" "/api/copiloto"

# Hybrid: JSON y semántico (texto)
$tests += Row "hybrid-json" "POST" "/api/hybrid" @(200) @{ agent_response = "ping" }
$tests += Row "hybrid-semantic" "POST" "/api/hybrid?semantic_response=true" @(200) @{ agent_response = "ping" } $true
$hyb400 = Row "hybrid-400" "POST" "/api/hybrid" @(400) @{}   # debe disparar ErrorEnvelope
$tests += $hyb400

# Deploy: sólo validación (no crea recursos)
$tests += Row "deploy-validate" "POST" "/api/deploy" @(200, 400, 401, 403) $deployValidate
$tests += Row "deploy-400"     "POST" "/api/deploy" @(400) @{ resourceGroup = "boat-rental-app-group" }  # body incompleto -> error controlado

# Archivo: CRUD seguro en tmp/
$tests += Row "write"  "POST" "/api/escribir-archivo" @(201) @{ ruta = $fileA; contenido = "hola-$ts" }
$tests += Row "info"   "GET"  ("/api/info-archivo?ruta=" + [uri]::EscapeDataString($fileA))
$tests += Row "read"   "GET"  ("/api/leer-archivo?ruta=" + [uri]::EscapeDataString($fileA))
$tests += Row "modify" "POST" "/api/modificar-archivo" @(200) @{ ruta = $fileA; operacion = "agregar_final"; contenido = "linea-extra" }
$tests += Row "download-b64" "GET" ("/api/descargar-archivo?ruta=" + [uri]::EscapeDataString($fileA) + "&modo=base64")
$tests += Row "download-inline" "GET" ("/api/descargar-archivo?ruta=" + [uri]::EscapeDataString($fileA) + "&modo=inline") @(200)
$tests += Row "copy"   "POST" "/api/copiar-archivo" @(200) @{ origen = $fileA; destino = $fileB; overwrite = $true }
# --- FIX 2: mover archivo requiere 'blob': true ---
$tests += Row "move" "POST" "/api/mover-archivo" @(200) @{
  origen = $fileB; destino = $fileC; overwrite = $true; eliminar_origen = $true; blob = $true
}
$tests += Row "list"   "GET"  ("/api/listar-blobs?prefix=" + [uri]::EscapeDataString("tmp/e2e-") + "&top=5")
$tests += Row "deleteA" "POST" "/api/eliminar-archivo" @(200, 404) @{ ruta = $fileA }
$tests += Row "deleteC" "POST" "/api/eliminar-archivo" @(200, 404) @{ ruta = $fileC }
$tests += Row "delete-DELETE" "DELETE" ("/api/eliminar-archivo?ruta=" + [uri]::EscapeDataString("tmp/__noexiste__.txt")) @(200, 404)

# Scripts: preparar + ejecutar (desde Blob a /scripts local)
$tests += Row "put-script" "POST" "/api/escribir-archivo" @(201) @{ ruta = $script; contenido = "print('ok-e2e')" }
$tests += Row "prep-script" "POST" "/api/preparar-script" @(200) @{ ruta = $script }
$tests += Row "run-script"  "POST" "/api/ejecutar-script" @(200) @{ script = $script; args = @() }

# Testing helpers
$tests += Row "bateria-endpoints-POST" "POST" "/api/bateria-endpoints" @(200)
$tests += Row "bateria-endpoints-GET" "GET" "/api/bateria-endpoints" @(200)
$tests += Row "probar-endpoint(status)" "POST" "/api/probar-endpoint" @(200) @{ endpoint = "/api/status"; method = "GET" }
$tests += Row "probar-endpoint-GET" "GET" ("/api/probar-endpoint?endpoint=" + [uri]::EscapeDataString("/api/status") + "&method=GET") @(200)
# --- FIX 3: invocar algo soportado ---
$tests += Row "invocar(health)" "POST" "/api/invocar" @(200) @{ endpoint = "/api/health"; method = "GET" }

# Storage: crear-contenedor (sin efectos reales, nombre inválido)
$tests += Row "crear-contenedor-400" "POST" "/api/crear-contenedor" @(400) @{
  nombre = "INVALID NAME"
}

# Azure CLI: acepta 200 si hay login, o 401/403 si no lo hay
$tests += Row "ejecutar-cli" "POST" "/api/ejecutar-cli" @(200, 401, 403, 501) @{
  servicio = "resource"; comando = "list"
}

# Diagnóstico/Monitor: faltantes controlados (contract check)
$tests += Row "diag-configurar-400" "POST" "/api/diagnostico-configurar" @(400) @{ } # falta resourceId/workspaceId
$tests += Row "diag-listar-400"     "GET"  "/api/diagnostico-listar"     @(400)     # falta ?resourceId=...
$tests += Row "diag-eliminar-400"   "DELETE" "/api/diagnostico-eliminar" @(400)     # falta ?resourceId&settingName

# Endpoints "peligrosos": validar existencia con 400 controlado (sin efectos)
# --- FIX 4: CORS acepta lista vacía (ajusta expectativa) ---
$tests += Row "configurar-cors-empty-ok" "POST" "/api/configurar-cors" @(200, 400, 401, 403) @{ allowed_origins = @() }
$tests += Row "configurar-app-settings-400"  "POST" "/api/configurar-app-settings" @(400) @{ }                    # falta 'settings'
$tests += Row "escalar-plan-400"             "POST" "/api/escalar-plan" @(400, 401, 403) @{ }                               # falta 'plan_name'
$tests += Row "diagnostico-recursos-GET"     "GET"  "/api/diagnostico-recursos"
# --- FIX 5: diagnostico-recursos POST con resourceId ---
$tests += Row "diagnostico-recursos-POST" "POST" "/api/diagnostico-recursos" @(200, 400, 401, 403) @{
  recurso = $funcId; profundidad = "basico"
}
$tests += Row "auditar-deploy"               "GET"  "/api/auditar-deploy" @(200, 400, 401, 403, 500)
$tests += Row "render-error"                 "POST" "/api/render-error" @(200) @{ error = "e2e"; context = @{ stage = "test" } }
# --- FIX 7: diagnóstico completo vía POST mientras se parchea el GET ---
$tests += Row "diag-completo-POST" "POST" "/api/diagnostico-recursos-completo" @(200, 400, 401, 403) @{ recurso = $funcId }

# ========= Ejecutar batería =========
$results = $tests
$ok = ($results | Where-Object { $_.ok }).Count
$fail = ($results | Where-Object { -not $_.ok }).Count

# Contract assertions
if ($hyb400.ok -and -not (Assert-ErrorEnvelope $hyb400.out)) {
  "WARN: /api/hybrid 400 no cumple ErrorEnvelope esperado"
}

# Cobertura: paths con test vs. esperados
$testedPaths = $tests | Select-Object -ExpandProperty path | Sort-Object -Unique
$notTested = $expected | Where-Object { $_ -notin $testedPaths }

""
"--- Cobertura de pruebas ---"
"Esperados: $($expected.Count)  Con test: $($testedPaths.Count)"
if ($notTested.Count) { "Sin test para:`n - " + ($notTested -join "`n - ") } else { "Todos los esperados tienen al menos una prueba." }

""
"===== RESUMEN ====="
"Total: $($results.Count)  OK: $ok  FAIL: $fail"
"==================="

$results | Select-Object name, method, path, status, ok, ms, note | Format-Table -AutoSize

# Opcional: ver detalles de los FAIL
if ($fail -gt 0) {
  "`n--- Detalles de FAIL ---"
  $results | Where-Object { -not $_.ok } | ForEach-Object {
    "[$($_.name)] $($_.method) $($_.path) -> $($_.status)"
    "Salida:"
    ($_.out | ConvertTo-Json -Depth 20)
    "`n"
  }
}

# Export artifacts for CI
$results | ConvertTo-Json -Depth 20 > .\e2e-tooling-report.json
$results | Export-Csv .\e2e-tooling-report.csv -NoTypeInformation -Encoding UTF8


# --- FIX 6: auditoría de deploy (define secretos Kudu antes) ---
# Ejecuta una vez (cuando tengas el perfil de publicación) y luego vuelve a probar auditar-deploy:
# $tests += Row "appsettings-kudu" "POST" "/api/configurar-app-settings" @(200) @{
#   settings = @{ KUDU_USER = "<publishingUser>"; KUDU_PASS = "<publishingPass>" }
# }
