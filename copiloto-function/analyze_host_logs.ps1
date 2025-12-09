# analyze_host_logs.ps1
# Busca el stack trace real de syncfunctiontriggers en logs extraídos

param(
    [string]$LogsDir = "logs_extracted"
)

function Write-Info { param($msg) Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

Write-Host "`nBUSCANDO ERRORES DE SYNCFUNCTIONTRIGGERS..." -ForegroundColor Magenta

$hostLogsPath = Join-Path $LogsDir "LogFiles\Application\Functions\Host"

if (-not (Test-Path $hostLogsPath)) {
    Write-Error "No existe: $hostLogsPath"
    Write-Info "Extrae logs.zip primero con el script Python/WSL"
    exit 1
}

$logFiles = Get-ChildItem $hostLogsPath -Filter "*.log" | Sort-Object LastWriteTime -Descending

Write-Info "Analizando $($logFiles.Count) archivos de host..."

foreach ($file in $logFiles) {
    $content = Get-Content $file.FullName -Raw
    
    # Buscar patrones de error relacionados con sync/triggers
    if ($content -match "(?i)(sync.*trigger|trigger.*sync|exception|error|traceback|failed.*sync)") {
        Write-Host "`n=== $($file.Name) ===" -ForegroundColor Yellow
        
        # Extraer líneas relevantes con contexto
        $lines = Get-Content $file.FullName
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match "(?i)(sync|trigger|exception|error|traceback|failed)") {
                # Mostrar 3 líneas antes y 10 después para contexto
                $start = [Math]::Max(0, $i - 3)
                $end = [Math]::Min($lines.Count - 1, $i + 10)
                
                for ($j = $start; $j -le $end; $j++) {
                    if ($lines[$j] -match "(?i)(exception|error|failed)") {
                        Write-Host $lines[$j] -ForegroundColor Red
                    } else {
                        Write-Host $lines[$j] -ForegroundColor Gray
                    }
                }
                Write-Host ""
            }
        }
    }
}

Write-Info "`nSi no aparece nada, ejecuta capture_syncfunctiontriggers_error.ps1 para generar logs frescos"
