$response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/debug-openapi"

Write-Host "Response structure:"
$response | ConvertTo-Json -Depth 3

Write-Host "`nChecking for function_app.py in all_files_found:"
$functionAppFile = $response.all_files_found | Where-Object { $_.file -eq "function_app.py" }
if ($functionAppFile) {
    Write-Host "function_app.py found!"
    Write-Host "Size: $($functionAppFile.size) bytes"
    Write-Host "Full path: $($functionAppFile.full_path)"
} else {
    Write-Host "function_app.py not found in all_files_found"
    Write-Host "Available files:"
    $response.all_files_found | ForEach-Object { Write-Host "  - $($_.file)" }
}