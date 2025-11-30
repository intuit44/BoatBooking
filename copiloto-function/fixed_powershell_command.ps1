$response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/debug-openapi"

# Check in the correct property: all_files_found instead of files
$functionAppFile = $response.all_files_found | Where-Object { $_.file -eq "function_app.py" }

if ($functionAppFile) {
    Write-Host "function_app.py encontrado."
    Write-Host "Tamaño: $($functionAppFile.size) bytes"
    Write-Host "Ruta completa: $($functionAppFile.full_path)"
} else {
    Write-Host "function_app.py no está presente."
    Write-Host "Archivos encontrados:"
    $response.all_files_found | Select-Object -First 10 | ForEach-Object { 
        Write-Host "  - $($_.file) ($($_.size) bytes)" 
    }
}