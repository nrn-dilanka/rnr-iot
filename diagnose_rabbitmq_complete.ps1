#!/usr/bin/env pwsh
# RabbitMQ Complete Diagnosis and Fix Script
# This script will diagnose and fix RabbitMQ queue and stream issues

Write-Host "🐰 RabbitMQ Complete Diagnosis and Fix Tool" -ForegroundColor Green
Write-Host "=" * 60

# Check if Docker is running
Write-Host "📋 Step 1: Checking Docker Status..." -ForegroundColor Cyan
try {
    $dockerStatus = docker version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker is not running or not installed" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and run this script again." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Docker is not available" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and start it." -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose file
Write-Host "`n📋 Step 2: Checking Docker Compose Configuration..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "✅ docker-compose.yml found" -ForegroundColor Green
} else {
    Write-Host "❌ docker-compose.yml not found" -ForegroundColor Red
    exit 1
}

# Check current container status
Write-Host "`n📋 Step 3: Checking Container Status..." -ForegroundColor Cyan
$containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "rnr_iot" }
if ($containers) {
    Write-Host "Current RNR IoT containers:" -ForegroundColor Yellow
    $containers | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "⚠️ No RNR IoT containers found" -ForegroundColor Yellow
}

# Function to start services
function Start-Services {
    Write-Host "`n🚀 Starting RabbitMQ and related services..." -ForegroundColor Cyan
    
    # Stop any existing containers first
    Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
    docker-compose down --remove-orphans 2>$null
    
    # Start only RabbitMQ first
    Write-Host "🐰 Starting RabbitMQ container..." -ForegroundColor Yellow
    docker-compose up -d rnr_rabbitmq
    
    # Wait for RabbitMQ to be ready
    Write-Host "⏳ Waiting for RabbitMQ to start (60 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60
    
    # Check RabbitMQ health
    $rabbitHealth = docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ RabbitMQ is healthy and ready" -ForegroundColor Green
    } else {
        Write-Host "❌ RabbitMQ health check failed" -ForegroundColor Red
        Write-Host "Checking RabbitMQ logs..." -ForegroundColor Yellow
        docker logs rnr_iot_rabbitmq --tail 20
    }
    
    # Start database
    Write-Host "🗄️ Starting PostgreSQL..." -ForegroundColor Yellow
    docker-compose up -d rnr_postgres
    Start-Sleep -Seconds 30
    
    # Start API server
    Write-Host "🔌 Starting API Server..." -ForegroundColor Yellow
    docker-compose up -d rnr_api_server
    Start-Sleep -Seconds 20
}

# Function to check RabbitMQ management interface
function Test-RabbitMQManagement {
    Write-Host "`n📊 Testing RabbitMQ Management Interface..." -ForegroundColor Cyan
    
    $managementUrl = "http://localhost:15672"
    $credentials = "rnr_iot_user:rnr_iot_2025!"
    
    try {
        # Convert credentials to base64
        $base64Creds = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($credentials))
        
        # Test management API
        $response = Invoke-WebRequest -Uri "$managementUrl/api/overview" -Headers @{Authorization="Basic $base64Creds"} -UseBasicParsing -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ RabbitMQ Management interface is accessible" -ForegroundColor Green
            Write-Host "🌐 Management UI: $managementUrl" -ForegroundColor Cyan
            Write-Host "👤 Username: rnr_iot_user" -ForegroundColor Cyan
            Write-Host "🔑 Password: rnr_iot_2025!" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "❌ RabbitMQ Management interface not accessible" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to run queue monitoring
function Start-QueueMonitoring {
    Write-Host "`n👀 Starting Queue Monitoring..." -ForegroundColor Cyan
    
    if (Test-Path "rabbitmq_monitor.py") {
        Write-Host "Found rabbitmq_monitor.py, running monitoring..." -ForegroundColor Yellow
        
        # Install required Python packages if needed
        pip install requests paho-mqtt 2>$null
        
        # Run monitoring script
        Write-Host "Starting real-time queue monitoring..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
        python rabbitmq_monitor.py --report
    } else {
        Write-Host "❌ rabbitmq_monitor.py not found" -ForegroundColor Red
    }
}

# Function to generate test data
function Generate-TestData {
    Write-Host "`n📡 Generating Test Data..." -ForegroundColor Cyan
    
    if (Test-Path "generate_realtime_data.py") {
        Write-Host "Found data generator, starting test data generation..." -ForegroundColor Yellow
        
        # Install required packages
        pip install paho-mqtt requests asyncio 2>$null
        
        Write-Host "🔄 Generating test MQTT data for 2 minutes..." -ForegroundColor Green
        Write-Host "This will send sensor data to RabbitMQ queues" -ForegroundColor Yellow
        
        # Run data generator for 2 minutes
        python generate_realtime_data.py
    } else {
        Write-Host "❌ generate_realtime_data.py not found" -ForegroundColor Red
    }
}

# Function to test MQTT connectivity
function Test-MQTTConnectivity {
    Write-Host "`n🔗 Testing MQTT Connectivity..." -ForegroundColor Cyan
    
    if (Test-Path "test_rabbitmq_mqtt.py") {
        Write-Host "Running MQTT connectivity test..." -ForegroundColor Yellow
        
        # Install required packages
        pip install paho-mqtt 2>$null
        
        Write-Host "🧪 Testing MQTT broker connectivity..." -ForegroundColor Green
        python test_rabbitmq_mqtt.py
    } else {
        Write-Host "❌ test_rabbitmq_mqtt.py not found" -ForegroundColor Red
    }
}

# Main execution
Write-Host "`n🎯 Select an action:" -ForegroundColor Green
Write-Host "1. Start all services and diagnose" -ForegroundColor White
Write-Host "2. Check current status only" -ForegroundColor White
Write-Host "3. Generate test data" -ForegroundColor White
Write-Host "4. Monitor queues" -ForegroundColor White
Write-Host "5. Test MQTT connectivity" -ForegroundColor White
Write-Host "6. Full diagnostic and fix (recommended)" -ForegroundColor Yellow

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Start-Services
        Test-RabbitMQManagement
    }
    "2" {
        Test-RabbitMQManagement
        Start-QueueMonitoring
    }
    "3" {
        Generate-TestData
    }
    "4" {
        Start-QueueMonitoring
    }
    "5" {
        Test-MQTTConnectivity
    }
    "6" {
        Write-Host "`n🔧 Running Full Diagnostic and Fix..." -ForegroundColor Green
        Start-Services
        Start-Sleep -Seconds 10
        Test-RabbitMQManagement
        Start-Sleep -Seconds 5
        Test-MQTTConnectivity
        Start-Sleep -Seconds 5
        Generate-TestData
        Start-Sleep -Seconds 5
        Start-QueueMonitoring
    }
    default {
        Write-Host "Invalid choice. Running full diagnostic..." -ForegroundColor Yellow
        Start-Services
        Test-RabbitMQManagement
        Generate-TestData
        Start-QueueMonitoring
    }
}

Write-Host "`n🎉 Diagnostic complete!" -ForegroundColor Green
Write-Host "If you still don't see data in queues, check:" -ForegroundColor Yellow
Write-Host "  1. RabbitMQ Management UI at http://localhost:15672" -ForegroundColor White
Write-Host "  2. Container logs: docker logs rnr_iot_rabbitmq" -ForegroundColor White
Write-Host "  3. API server logs: docker logs rnr_iot_api_server" -ForegroundColor White
