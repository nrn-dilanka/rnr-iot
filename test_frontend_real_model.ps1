# Test Frontend Real Model Control Updates
# This script starts the frontend to test the new real model control features

Write-Host "=== Frontend Real Model Control Test ===" -ForegroundColor Green
Write-Host ""

Write-Host "📋 Updated Frontend Features:" -ForegroundColor Yellow
Write-Host "✅ Added Real Model Control (GPIO 27) to Smart Device Control Panel" -ForegroundColor Green
Write-Host "✅ Added Real Model status display to Dashboard" -ForegroundColor Green
Write-Host "✅ Added Relay 5 control for Real Model" -ForegroundColor Green
Write-Host "✅ Updated API service with real model commands" -ForegroundColor Green
Write-Host ""

Write-Host "🎯 Real Model Control Features:" -ForegroundColor Cyan
Write-Host "   - Direct REAL_MODEL_CONTROL command" -ForegroundColor White
Write-Host "   - Relay 5 control (same as GPIO 27)" -ForegroundColor White
Write-Host "   - Real-time status display with 🎯 icon" -ForegroundColor White
Write-Host "   - Integration with smart automation system" -ForegroundColor White
Write-Host ""

Write-Host "🚀 Starting Frontend Development Server..." -ForegroundColor Yellow

# Navigate to frontend directory
Set-Location "c:\Users\RnR Solutions\Desktop\IoT-Platform\frontend"

# Check if node_modules exists
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Start the development server
Write-Host "🌐 Starting React development server on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Test the following new features:" -ForegroundColor Cyan
Write-Host "   1. Dashboard: Check Real Model state indicator" -ForegroundColor White
Write-Host "   2. AI Agent Manager: Test Real Model ON/OFF buttons" -ForegroundColor White
Write-Host "   3. Smart Control: Test Relay 5 (Real Model) control" -ForegroundColor White
Write-Host "   4. Real-time Updates: Watch status change live" -ForegroundColor White
Write-Host ""

npm start
