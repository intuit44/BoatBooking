param(
  [string]$Archivo = "fix_functionapp_final.ps1"
)

Write-Host "`n🧼 Limpiando archivo: $Archivo" -ForegroundColor Cyan

# Leer contenido como texto plano
$contenidoOriginal = Get-Content $Archivo -Raw

# Eliminar caracteres invisibles y corruptos comunes
$contenidoLimpio = $contenidoOriginal `
  -replace "`uFEFF", '' `             # BOM
-replace "`u200B", '' `             # Zero-width space
-replace "`u00A0", ' ' `            # Non-breaking space a espacio normal
-replace "âœ“", "✓" `
  -replace "âœ”", "✓" `
  -replace "âœ—", "✗" `
  -replace "âš ", "⚠" `
  -replace "â†’", "→"

# Guardar copia original
Copy-Item $Archivo "$Archivo.bak"

# Guardar archivo limpio
$contenidoLimpio | Set-Content -Path $Archivo -Encoding UTF8

Write-Host "✅ Archivo limpiado. Copia de respaldo en: $Archivo.bak`n" -ForegroundColor Green
