# Auto IP Detection Script for RNR Solutions IoT Platform - PowerShell Version

Write-Host "🔍 Detecting local IP address..." -ForegroundColor Cyan

# Function to detect local IP address
function Get-LocalIP {
    try {
        # Try to get the IP from the active network adapter
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -ne "127.0.0.1"})[0].IPAddress
        
        if (-not $ip) {
            # Try Wi-Fi adapter
            $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*" -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -ne "127.0.0.1"})[0].IPAddress
        }
        
        if (-not $ip) {
            # Try any active network interface
            $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -ne "127.0.0.1" -and $_.InterfaceAlias -notlike "*Loopback*"})[0].IPAddress
        }
        
        return $ip
    }
    catch {
        return $null
    }
}

# Detect IP
$DetectedIP = Get-LocalIP

if (-not $DetectedIP) {
    Write-Host "❌ Could not detect IP address automatically" -ForegroundColor Red
    Write-Host "📝 Please set IP manually in .env files" -ForegroundColor Yellow
    $DetectedIP = "localhost"
}
else {
    Write-Host "✅ Detected IP: $DetectedIP" -ForegroundColor Green
}

# Function to update file content
function Update-FileContent {
    param (
        [string]$FilePath,
        [string]$OldPattern,
        [string]$NewValue
    )
    
    if (Test-Path $FilePath) {
        $content = Get-Content $FilePath -Raw
        $updatedContent = $content -replace $OldPattern, $NewValue
        Set-Content -Path $FilePath -Value $updatedContent -NoNewline
        Write-Host "  ✓ Updated $FilePath" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ File not found: $FilePath" -ForegroundColor Yellow
    }
}

# Update main .env file
Write-Host "📝 Updating main .env file..." -ForegroundColor Cyan
Update-FileContent -FilePath ".env" -OldPattern "REACT_APP_API_URL=http://[^:]+:8000/api" -NewValue "REACT_APP_API_URL=http://$DetectedIP:8000/api"
Update-FileContent -FilePath ".env" -OldPattern "REACT_APP_WS_URL=ws://[^:]+:8000/ws" -NewValue "REACT_APP_WS_URL=ws://$DetectedIP:8000/ws"

# Update frontend .env file
Write-Host "📝 Updating frontend/.env file..." -ForegroundColor Cyan
Update-FileContent -FilePath "frontend\.env" -OldPattern "REACT_APP_API_URL=http://[^:]+:8000/api" -NewValue "REACT_APP_API_URL=http://$DetectedIP:8000/api"
Update-FileContent -FilePath "frontend\.env" -OldPattern "REACT_APP_WS_URL=ws://[^:]+:8000/ws" -NewValue "REACT_APP_WS_URL=ws://$DetectedIP:8000/ws"

# Update docker-compose.yml
Write-Host "📝 Updating docker-compose.yml..." -ForegroundColor Cyan
Update-FileContent -FilePath "docker-compose.yml" -OldPattern "REACT_APP_API_URL: http://[^:]+:8000/api" -NewValue "REACT_APP_API_URL: http://$DetectedIP:8000/api"
Update-FileContent -FilePath "docker-compose.yml" -OldPattern "REACT_APP_WS_URL: ws://[^:]+:8000/ws" -NewValue "REACT_APP_WS_URL: ws://$DetectedIP:8000/ws"

Write-Host "✅ IP configuration updated to: $DetectedIP" -ForegroundColor Green
Write-Host "🚀 You can now run: docker-compose up --build -d" -ForegroundColor Cyan

# Display current configuration
Write-Host "`n📋 Current Configuration:" -ForegroundColor Yellow
Write-Host "  • Frontend URL: http://$DetectedIP`:3000" -ForegroundColor White
Write-Host "  • API URL: http://$DetectedIP`:8000" -ForegroundColor White
Write-Host "  • WebSocket URL: ws://$DetectedIP`:8000/ws" -ForegroundColor White
