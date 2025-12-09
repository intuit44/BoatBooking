# extract_and_analyze.ps1
# Extrae host-logs.zip con Python (evita problema de colons) y busca el error

$ErrorActionPreference = "Continue"

Write-Host "`nDESCARGANDO LOGS FRESCOS..." -ForegroundColor Magenta

# Descargar logs actuales primero
az webapp log download -g boat-rental-app-group -n copiloto-semantico-func-us2 --log-file host-logs.zip 2>&1 | Out-Null
if (Test-Path "host-logs.zip") {
    Write-Host "Logs descargados" -ForegroundColor Green
} else {
    Write-Host "Error descargando logs" -ForegroundColor Red
    exit 1
}

Write-Host "`nEXTRAYENDO Y ANALIZANDO host-logs.zip..." -ForegroundColor Magenta

# Extraer con Python para evitar problema de colons en NTFS
python -c @"
import zipfile, shutil, pathlib
dest = pathlib.Path('host_logs_extracted')
if dest.exists():
    shutil.rmtree(dest)
dest.mkdir()
with zipfile.ZipFile('host-logs.zip') as zf:
    for member in zf.namelist():
        # Reemplazar : con _ para NTFS
        safe_name = member.replace(':', '_')
        target = dest / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not member.endswith('/'):
            with zf.open(member) as source, open(target, 'wb') as dest_file:
                dest_file.write(source.read())
print(f'Extraídos {len(zf.namelist())} archivos')
"@

if (-not (Test-Path "host_logs_extracted")) {
    Write-Host "Error extrayendo. Intenta manualmente con 7zip" -ForegroundColor Red
    exit 1
}

Write-Host "`nBUSCANDO ERRORES EN HOST LOGS..." -ForegroundColor Yellow

# Buscar en Application/Functions/Host
$hostPath = "host_logs_extracted\LogFiles\Application\Functions\Host"
if (Test-Path $hostPath) {
    $logs = Get-ChildItem $hostPath -Filter "*.log" | Sort-Object LastWriteTime -Descending
    
    Write-Host "`nARCHIVOS ENCONTRADOS (ordenados por fecha):" -ForegroundColor Yellow
    $logs | ForEach-Object { Write-Host "  $($_.Name) - $($_.LastWriteTime)" -ForegroundColor Gray }
    
    # Buscar archivos de diciembre 2025
    $recentLogs = $logs | Where-Object { $_.Name -match "2025-12" } | Select-Object -First 3
    
    if (-not $recentLogs) {
        Write-Host "`n⚠️ NO HAY LOGS DE DICIEMBRE 2025. Los logs son antiguos (noviembre)." -ForegroundColor Red
        Write-Host "Ejecutando syncfunctiontriggers para generar logs frescos..." -ForegroundColor Yellow
        
        az rest --method POST --uri "https://management.azure.com/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.Web/sites/copiloto-semantico-func-us2/syncfunctiontriggers?api-version=2022-03-01" 2>&1 | Out-Null
        
        Write-Host "Esperando 10 segundos para que se generen logs..." -ForegroundColor Yellow
        Start-Sleep 10
        
        az webapp log download -g boat-rental-app-group -n copiloto-semantico-func-us2 --log-file host-logs-fresh.zip 2>&1 | Out-Null
        
        python -c @"
import zipfile, shutil, pathlib
dest = pathlib.Path('host_logs_fresh')
if dest.exists():
    shutil.rmtree(dest)
dest.mkdir()
with zipfile.ZipFile('host-logs-fresh.zip') as zf:
    for member in zf.namelist():
        safe_name = member.replace(':', '_')
        target = dest / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not member.endswith('/'):
            with zf.open(member) as source, open(target, 'wb') as dest_file:
                dest_file.write(source.read())
print('Logs frescos extraídos')
"@
        
        $hostPath = "host_logs_fresh\LogFiles\Application\Functions\Host"
        if (Test-Path $hostPath) {
            $logs = Get-ChildItem $hostPath -Filter "*.log" | Sort-Object LastWriteTime -Descending
            $recentLogs = $logs | Select-Object -First 3
        }
    }
    
    foreach ($log in $recentLogs) {
        Write-Host "`n=== $($log.Name) ===" -ForegroundColor Cyan
        $content = Get-Content $log.FullName
        
        # Buscar líneas con error/exception/sync
        $errorLines = $content | Select-String -Pattern "(error|exception|failed|sync.*trigger|internal.*server|traceback|stack)" -Context 3,10
        
        if ($errorLines) {
            foreach ($match in $errorLines) {
                Write-Host $match.Line -ForegroundColor Red
                foreach ($ctx in $match.Context.PostContext) {
                    Write-Host "  $ctx" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "Sin errores en este archivo" -ForegroundColor Gray
        }
    }
}

# Buscar también en Application general
$appPath = "host_logs_extracted\LogFiles\Application"
if (Test-Path $appPath) {
    Write-Host "`n=== LOGS DE APPLICATION ===" -ForegroundColor Cyan
    $appLogs = Get-ChildItem $appPath -Filter "*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 2
    
    foreach ($log in $appLogs) {
        $errors = Get-Content $log.FullName | Select-String -Pattern "(500|sync.*trigger|internal.*error)" -Context 1,3 | Select-Object -First 10
        if ($errors) {
            Write-Host "`n--- $($log.Name) ---" -ForegroundColor Yellow
            $errors | ForEach-Object { Write-Host $_.Line -ForegroundColor Red }
        }
    }
}

Write-Host "`nSi no aparece el stack trace, revisa manualmente:" -ForegroundColor Yellow
Write-Host "host_logs_extracted\LogFiles\Application\Functions\Host\" -ForegroundColor White
