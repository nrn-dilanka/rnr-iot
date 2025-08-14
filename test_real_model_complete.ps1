# End-to-End Real Model Control Test
# This script tests the complete real model control system

Write-Host "=== Complete Real Model Control System Test ===" -ForegroundColor Green
Write-Host ""

# Configuration
$baseUrl = "http://localhost:8000"
$deviceId = "441793F9456C"

Write-Host "🎯 Testing Real Model Control System..." -ForegroundColor Yellow
Write-Host "Device ID: $deviceId" -ForegroundColor Cyan
Write-Host "GPIO Pin: 27" -ForegroundColor Cyan
Write-Host ""

# Test 1: Turn ON Real Model via Direct Command
Write-Host "Test 1: REAL_MODEL_CONTROL ON..." -ForegroundColor Yellow
try {
    $response1 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "REAL_MODEL_CONTROL", "state": true}'
    Write-Host "✅ Direct Control ON: $($response1.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Direct Control ON failed: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 2: Turn OFF Real Model via Direct Command
Write-Host "Test 2: REAL_MODEL_CONTROL OFF..." -ForegroundColor Yellow
try {
    $response2 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "REAL_MODEL_CONTROL", "state": false}'
    Write-Host "✅ Direct Control OFF: $($response2.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Direct Control OFF failed: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 3: Turn ON Real Model via Relay 5
Write-Host "Test 3: RELAY_CONTROL Relay 5 ON..." -ForegroundColor Yellow
try {
    $response3 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "RELAY_CONTROL", "relay": 5, "state": true}'
    Write-Host "✅ Relay 5 ON: $($response3.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Relay 5 ON failed: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 4: Turn OFF Real Model via Relay 5
Write-Host "Test 4: RELAY_CONTROL Relay 5 OFF..." -ForegroundColor Yellow
try {
    $response4 = Invoke-WebRequest -Uri "$baseUrl/api/nodes/$deviceId/actions" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"action": "RELAY_CONTROL", "relay": 5, "state": false}'
    Write-Host "✅ Relay 5 OFF: $($response4.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Relay 5 OFF failed: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 5: Check Device Status
Write-Host "Test 5: Checking device status..." -ForegroundColor Yellow
try {
    $statusResponse = Invoke-WebRequest -Uri "$baseUrl/api/nodes" -Method GET
    $nodes = $statusResponse.Content | ConvertFrom-Json
    $targetNode = $nodes | Where-Object { $_.node_id -eq $deviceId }
    
    if ($targetNode) {
        Write-Host "✅ Device found: $($targetNode.name)" -ForegroundColor Green
        Write-Host "📊 Status: $($targetNode.status)" -ForegroundColor Cyan
        Write-Host "🕐 Last seen: $($targetNode.last_seen)" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Device not found in nodes list" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Status check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Real Model Control Test Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Summary of Real Model Features:" -ForegroundColor Cyan
Write-Host "   • GPIO 27 configured for Real Model connection" -ForegroundColor White
Write-Host "   • Direct REAL_MODEL_CONTROL commands supported" -ForegroundColor White
Write-Host "   • Relay 5 control maps to GPIO 27" -ForegroundColor White
Write-Host "   • Frontend includes Real Model control buttons" -ForegroundColor White
Write-Host "   • Dashboard shows Real Model status with 🎯 icon" -ForegroundColor White
Write-Host "   • Integration with smart automation system" -ForegroundColor White
Write-Host ""
Write-Host "📱 Check your ESP32 serial monitor for GPIO 27 control messages!" -ForegroundColor Yellow
