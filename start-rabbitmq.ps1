#!/usr/bin/env pwsh
# RNR Solutions - RabbitMQ Startup Script
# Starts only the RabbitMQ container for IoT data transmission

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "     RNR IoT Platform - RabbitMQ Service" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Check if RabbitMQ container already exists and is running
Write-Host "🔍 Checking RabbitMQ container status..." -ForegroundColor Yellow
$rabbitStatus = docker ps -a --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}"

if ($rabbitStatus -match "rnr_iot_rabbitmq.*Up") {
    Write-Host "✅ RabbitMQ container is already running" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "🚀 Starting RabbitMQ container..." -ForegroundColor Yellow
    docker-compose up -d rnr_rabbitmq
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start RabbitMQ container" -ForegroundColor Red
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
    
    Write-Host "✅ RabbitMQ container started successfully" -ForegroundColor Green
    Write-Host ""
}

# Wait for RabbitMQ to be ready
Write-Host "⏳ Waiting for RabbitMQ to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    Start-Sleep -Seconds 2
    $healthCheck = docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping 2>$null
    
    if ($healthCheck -match "Ping succeeded") {
        Write-Host "✅ RabbitMQ is ready!" -ForegroundColor Green
        break
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "⚠️  RabbitMQ took longer than expected to start" -ForegroundColor Yellow
        break
    }
    
    Write-Host "." -NoNewline -ForegroundColor Yellow
} while ($attempt -lt $maxAttempts)

Write-Host ""
Write-Host ""

# Display connection information
Write-Host "📋 RabbitMQ Connection Information:" -ForegroundColor Cyan
Write-Host "   • AMQP Port: 5672" -ForegroundColor White
Write-Host "   • MQTT Port: 1883" -ForegroundColor White
Write-Host "   • Management UI: http://localhost:15672" -ForegroundColor White
Write-Host "   • Username: rnr_iot_user" -ForegroundColor White
Write-Host "   • Password: rnr_iot_2025!" -ForegroundColor White
Write-Host "   • MQTT Virtual Host: rnr_iot_vhost" -ForegroundColor White
Write-Host ""

# Test MQTT connection
Write-Host "🧪 Testing MQTT connection..." -ForegroundColor Yellow
$mqttTest = docker exec rnr_iot_rabbitmq rabbitmq-plugins list | Select-String "rabbitmq_mqtt"
if ($mqttTest) {
    Write-Host "✅ MQTT plugin is enabled" -ForegroundColor Green
} else {
    Write-Host "⚠️  MQTT plugin status unknown" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔗 Your ESP32 devices can now connect to:" -ForegroundColor Green
Write-Host "   MQTT Broker: localhost:1883" -ForegroundColor White
Write-Host "   Username: rnr_iot_user" -ForegroundColor White
Write-Host "   Password: rnr_iot_2025!" -ForegroundColor White
Write-Host ""

# Show container status
Write-Host "📊 Container Status:" -ForegroundColor Cyan
docker ps --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "🎉 RabbitMQ is ready to receive IoT data!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
