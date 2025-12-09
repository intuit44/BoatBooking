#!/usr/bin/env pwsh

# Sync Functions with Extended Wait - v407
Write-Host "[INFO] Azure Functions Sync with Extended Wait Strategy..." -ForegroundColor Green

$resourceGroup = "boat-rental-app-group"
$functionAppName = "copiloto-semantico-func-us2"
$subscriptionId = "380fa841-83f3-42fe-adc4-582a5ebe139b"

function Test-HostReadiness {
    param([string]$AppName)
    
    Write-Host "[INFO] Testing host readiness..." -ForegroundColor Yellow
    
    $endpoints = @(
        "https://$AppName.azurewebsites.net/api/redis-cache-health",
        "https://$AppName.azurewebsites.net/api/verificar-sistema"
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint -Method GET -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "[OK] $endpoint - OK" -ForegroundColor Green
            }
            else {
                Write-Host "[WARN] $endpoint - Status: $($response.StatusCode)" -ForegroundColor Yellow
                return $false
            }
        }
        catch {
            Write-Host "[ERROR] $endpoint - Error: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    return $true
}

function Invoke-SyncWithRetry {
    param([int]$MaxRetries = 3, [int]$WaitSeconds = 60)
    
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        Write-Host "`n[INFO] Sync attempt $attempt of $MaxRetries" -ForegroundColor Cyan

        if (-not (Test-HostReadiness -AppName $functionAppName)) {
            Write-Host "[WARN] Host not ready, waiting $WaitSeconds seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $WaitSeconds
            continue
        }

        Write-Host "[INFO] Attempting syncfunctiontriggers..." -ForegroundColor Cyan
        
        try {
            $syncUri = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$functionAppName/syncfunctiontriggers?api-version=2022-03-01"
            
            $result = az rest --method POST --uri $syncUri 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Host "[SUCCESS] SYNC SUCCESSFUL!" -ForegroundColor Green
                Write-Host "[INFO] Functions should now be visible in Azure Portal" -ForegroundColor Cyan
                return $true
            }
            else {
                Write-Host "[ERROR] Sync failed: $result" -ForegroundColor Red

                if ($attempt -lt $MaxRetries) {
                    Write-Host "[INFO] Waiting $WaitSeconds seconds before retry..." -ForegroundColor Yellow
                    Start-Sleep -Seconds $WaitSeconds
                }
            }
        }
        catch {
            Write-Host "[ERROR] Exception during sync: $($_.Exception.Message)" -ForegroundColor Red

            if ($attempt -lt $MaxRetries) {
                Write-Host "[INFO] Waiting $WaitSeconds seconds before retry..." -ForegroundColor Yellow
                Start-Sleep -Seconds $WaitSeconds
            }
        }
    }
    
    return $false
}

# Main execution
Write-Host "[INFO] Configuration:" -ForegroundColor Cyan
Write-Host "   Function App: $functionAppName" -ForegroundColor White
Write-Host "   Resource Group: $resourceGroup" -ForegroundColor White
Write-Host "   Subscription: $subscriptionId" -ForegroundColor White

Write-Host "`n[INFO] Initial wait (90 seconds) for host stabilization..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

$success = Invoke-SyncWithRetry -MaxRetries 3 -WaitSeconds 120

if ($success) {
    Write-Host "`n[SUCCESS] Azure Functions sync completed successfully!" -ForegroundColor Green
    Write-Host "[INFO] Check your functions in: https://portal.azure.com" -ForegroundColor Cyan
    exit 0
}
else {
    Write-Host "`n[ERROR] All sync attempts failed" -ForegroundColor Red
    Write-Host "[INFO] Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Check Function App logs for new errors" -ForegroundColor White
    Write-Host "   2. Verify all functions are loaded correctly" -ForegroundColor White
    Write-Host "   3. Consider restarting the Function App" -ForegroundColor White
    exit 1
}
