param(
  [string]$Directory = ".",
  [string[]]$Extensions = @("*.ps1", "*.psm1", "*.psd1")
)

Write-Host "🧹 Limpiando caracteres invisibles en: $Directory" -ForegroundColor Cyan

# Caracteres invisibles comunes: BOM, Zero-width space, NBSP
$invisibles = @(
  ([char]0xFEFF),  # BOM
  ([char]0x200B),  # Zero-width space
  ([char]0x00A0)   # NBSP
)

$files = Get-ChildItem -Path $Directory -Recurse -Include $Extensions -File

foreach ($file in $files) {
  $original = Get-Content $file.FullName -Raw
  $cleaned = $original
  $replacements = 0

  foreach ($char in $invisibles) {
    if ($cleaned.Contains($char)) {
      $cleaned = $cleaned -replace [regex]::Escape($char), ""
      $replacements++
    }
  }

  if ($replacements -gt 0) {
    Write-Host "✅ Limpiado: $($file.FullName)" -ForegroundColor Green
    $cleaned | Set-Content $file.FullName -Encoding UTF8
  }
  else {
    Write-Host "✔️  Sin cambios: $($file.FullName)" -ForegroundColor DarkGray
  }
}

Write-Host "`n🎯 Proceso finalizado. Todos los archivos fueron procesados." -ForegroundColor Yellow
