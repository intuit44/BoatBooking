# PowerShell script to create basic PNG files for Expo mobile app
$assetsPath = ".\mobile-app\assets"

# Base64 encoded minimal PNG (1x1 transparent pixel)
$pngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Convert base64 to bytes
$pngBytes = [System.Convert]::FromBase64String($pngBase64)

# Ensure assets directory exists
if (-not (Test-Path $assetsPath)) {
    New-Item -ItemType Directory -Path $assetsPath -Force
    Write-Host "Created assets directory"
}

# Create PNG files
$files = @("icon.png", "splash.png", "adaptive-icon.png", "favicon.png")

foreach ($file in $files) {
    $filePath = Join-Path $assetsPath $file
    [System.IO.File]::WriteAllBytes($filePath, $pngBytes)
    Write-Host "✅ Created $file"
}

Write-Host "`n🎉 All PNG assets created successfully!"
Write-Host "📁 Location: $assetsPath"
Write-Host "⚠️  These are minimal 1x1 pixel placeholders."
Write-Host "🔄 Replace them with proper images before production."
Write-Host ""
Write-Host "Now you can run: npm run android"