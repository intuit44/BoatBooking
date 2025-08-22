# test-logic-app.ps1
# Script para verificar que la Logic App funciona correctamente

Write-Host "🧪 TEST DE LOGIC APP Y COPILOTO" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# URL completa con todos los parámetros
$baseUrl = "https://prod-15.eastus.logic.azure.com/workflows/4711b810bb5f478aa4d8dc5662c61c53/triggers/When_a_HTTP_request_is_received/paths/invoke"
$queryParams = "?api-version=2019-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=IUqo-n0TnqdRiQF7qSGSBnofI5LZPmuzdYHCdmsahss"

# Test 1: Ping simple
Write-Host "`n📍 Test 1: Ping simple" -ForegroundColor Yellow
$body1 = @{
  agent_response = "ping"
  agent_name     = "Test_Script"
} | ConvertTo-Json

try {
  $response1 = Invoke-RestMethod `
    -Uri ($baseUrl + "/ejecutar" + $queryParams) `
    -Method POST `
    -ContentType "application/json" `
    -Body $body1
    
  Write-Host "✅ Ping exitoso" -ForegroundColor Green
  $response1 | ConvertTo-Json -Depth 3
}
catch {
  Write-Host "❌ Error en ping: $_" -ForegroundColor Red
  Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# Test 2: Dashboard
Write-Host "`n📍 Test 2: Dashboard" -ForegroundColor Yellow
$body2 = @{
  agent_response = "Generando dashboard.`n`n``````json`n{`n  `"endpoint`": `"ejecutar`",`n  `"method`": `"POST`",`n  `"intencion`": `"dashboard`",`n  `"parametros`": {},`n  `"modo`": `"normal`"`n}``````"
  agent_name     = "Test_Script"
} | ConvertTo-Json

try {
  $response2 = Invoke-RestMethod `
    -Uri ($baseUrl + "/ejecutar" + $queryParams) `
    -Method POST `
    -ContentType "application/json" `
    -Body $body2
    
  Write-Host "✅ Dashboard ejecutado" -ForegroundColor Green
  $response2 | ConvertTo-Json -Depth 3
}
catch {
  Write-Host "❌ Error en dashboard: $_" -ForegroundColor Red
}

# Test 3: Verificar en App Insights
Write-Host "`n📍 Test 3: Verificando en App Insights..." -ForegroundColor Yellow

$APPID = "e2fa2b26-ad14-40ae-8663-00783afa7201"
$KQL = @"
requests
| where timestamp > ago(2m)
| where url contains "hybrid" or url contains "ejecutar"
| project timestamp, resultCode, url, customDimensions["user_agent.original"]
| order by timestamp desc
| take 5
"@

$insights = az monitor app-insights query --app $APPID --analytics-query $KQL -o json | ConvertFrom-Json

if ($insights.tables[0].rows.Count -gt 0) {
  Write-Host "✅ Solicitudes encontradas en App Insights:" -ForegroundColor Green
  foreach ($row in $insights.tables[0].rows) {
    Write-Host "  - $($row[0]): HTTP $($row[1]) - UA: $($row[3])" -ForegroundColor Gray
  }
}
else {
  Write-Host "⚠️ No se encontraron solicitudes recientes" -ForegroundColor Yellow
}

Write-Host "`n✅ TEST COMPLETADO" -ForegroundColor Green
Write-Host "Si ves respuestas 200, la Logic App está funcionando correctamente." -ForegroundColor Cyan
Write-Host "Si ves errores 400, revisa que la URL incluya todos los parámetros." -ForegroundColor Yellow