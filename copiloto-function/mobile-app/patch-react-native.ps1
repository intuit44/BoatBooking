# patch-react-native.ps1
# Script para parchear React Native después de npm install

Write-Host "🔧 Aplicando patch a React Native..." -ForegroundColor Yellow

$reactNativeIndex = "node_modules\react-native\index.js"

if (Test-Path $reactNativeIndex) {
    $content = Get-Content $reactNativeIndex -Raw
    
    # Remover líneas problemáticas con Flow syntax
    $fixedContent = $content -replace "import typeof.*?from.*?;", "// Flow import removed"
    $fixedContent = $fixedContent -replace "export type.*?;", "// Flow export removed"
    
    Set-Content -Path $reactNativeIndex -Value $fixedContent -Encoding UTF8
    Write-Host "✅ React Native parcheado" -ForegroundColor Green
} else {
    Write-Host "❌ React Native no encontrado" -ForegroundColor Red
}
