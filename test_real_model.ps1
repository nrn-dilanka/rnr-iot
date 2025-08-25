# Test Real Model Control on GPIO 27
# This script tests the new real model control functionality

Write-Host "=== ESP32 Real Model Control Test ===" -ForegroundColor Green
Write-Host ""

# Configuration
$baseUrl = "http://localhost:8000"
$deviceId = "441793F9456C"  # Your ESP32 device ID

# Test 1: Turn ON Real Model
Write-Host "Test 1: Turning ON Real Model (GPIO 27)..." -ForegroundColor Yellow
try {
    $response1 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "REAL_MODEL_CONTROL", "state": true}'
    
    Write-Host "✅ Response: $($response1.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Wait 3 seconds
Write-Host "Waiting 3 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Test 2: Turn OFF Real Model
Write-Host "Test 2: Turning OFF Real Model (GPIO 27)..." -ForegroundColor Yellow
try {
    $response2 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "REAL_MODEL_CONTROL", "state": false}'
    
    Write-Host "✅ Response: $($response2.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Control via Relay Number (Relay 5)
Write-Host "Test 3: Control Real Model via Relay 5..." -ForegroundColor Yellow
try {
    $response3 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "RELAY_CONTROL", "relay": 5, "state": true}'
    
    Write-Host "✅ Response: $($response3.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Real Model Control Test Complete ===" -ForegroundColor Green
Write-Host "Check your ESP32 serial monitor for GPIO 27 control messages!" -ForegroundColor Cyan
