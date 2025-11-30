Write-Host "== PowerShell Test Script Demo =="
$sum = 7 + 3
Write-Host "Resultado suma 7 + 3: $sum"
Write-Host "Archivos encontrados en debug-openapi (top 5):"
$response = Invoke-RestMethod -Uri "https://copiloto-semantico-func-us2.azurewebsites.net/api/debug-openapi"
$response.all_files_found | Select-Object -First 5 | ForEach-Object { Write-Host $_.file }