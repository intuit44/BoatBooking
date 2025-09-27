param(
  [string]$Directory = ".",
  [string[]]$Extensions = @("*.ps1", "*.psm1", "*.psd1"),
  [switch]$CreateBackup = $true,
  [switch]$WhatIf
)

Write-Host "Limpiando caracteres invisibles en: $Directory" -ForegroundColor Cyan

# Lista de caracteres invisibles
$invisibles = @{
  "BOM"                   = 0xFEFF
  "Zero-Width Space"      = 0x200B
  "Zero-Width Non-Joiner" = 0x200C
  "Zero-Width Joiner"     = 0x200D
  "Non-Breaking Space"    = 0x00A0
}

$files = Get-ChildItem -Path $Directory -Recurse -Include $Extensions -File -ErrorAction SilentlyContinue
$totalFiles = $files.Count
$modifiedFiles = 0

Write-Host "Encontrados $totalFiles archivos para procesar" -ForegroundColor Yellow

foreach ($file in $files) {
  try {
    $content = Get-Content $file.FullName -Raw -ErrorAction Stop
    if ($null -eq $content) {
      Write-Host "Archivo vacio: $($file.Name)" -ForegroundColor DarkGray
      continue
    }
        
    $originalLength = $content.Length
    $cleaned = $content
    $foundChars = @()
        
    foreach ($charName in $invisibles.Keys) {
      $charCode = $invisibles[$charName]
      $char = [char]$charCode
      $charString = $char.ToString()
            
      if ($cleaned.Contains($charString)) {
        # Contar ocurrencias antes de reemplazar
        $count = 0
        $tempStr = $cleaned
        while ($tempStr.Contains($charString)) {
          $count++
          $pos = $tempStr.IndexOf($charString)
          $tempStr = $tempStr.Substring($pos + 1)
        }
                
        $foundChars += "$charName (x$count)"
        # Usar el método Replace de String que acepta strings
        $cleaned = $cleaned.Replace($charString, [string]::Empty)
      }
    }
        
    if ($foundChars.Count -gt 0) {
      if ($WhatIf) {
        Write-Host "SIMULACION - Limpieza: $($file.Name)" -ForegroundColor Yellow
        Write-Host "   Caracteres encontrados: $($foundChars -join ', ')" -ForegroundColor DarkYellow
      }
      else {
        if ($CreateBackup) {
          $backupPath = "$($file.FullName).bak"
          Copy-Item -Path $file.FullName -Destination $backupPath -Force
        }
                
        # Guardar con UTF8 sin BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($file.FullName, $cleaned, $utf8NoBom)
                
        $reduction = $originalLength - $cleaned.Length
        Write-Host "LIMPIADO: $($file.Name)" -ForegroundColor Green
        Write-Host "   Removidos: $($foundChars -join ', ')" -ForegroundColor DarkGreen
        Write-Host "   Reduccion: $reduction bytes" -ForegroundColor DarkGreen
        $modifiedFiles++
      }
    }
    else {
      Write-Host "Sin cambios: $($file.Name)" -ForegroundColor DarkGray
    }
  }
  catch {
    Write-Host "ERROR procesando: $($file.Name)" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor DarkRed
  }
}

Write-Host "`nRESUMEN:" -ForegroundColor Cyan
Write-Host "   Total archivos: $totalFiles" -ForegroundColor White
Write-Host "   Modificados: $modifiedFiles" -ForegroundColor Green
Write-Host "   Sin cambios: $($totalFiles - $modifiedFiles)" -ForegroundColor Gray

if ($WhatIf) {
  Write-Host "`nModo simulacion activo. Ejecuta sin -WhatIf para aplicar cambios." -ForegroundColor Yellow
}
elseif ($CreateBackup -and $modifiedFiles -gt 0) {
  Write-Host "`nSe crearon archivos .bak de respaldo" -ForegroundColor Blue
}

Write-Host "`nProceso finalizado." -ForegroundColor Green