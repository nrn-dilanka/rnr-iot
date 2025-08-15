# RNR Solutions - Fix API Server and Restart Platform (PowerShell)
# This script fixes the uvicorn command issue and restarts the platform

Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform - API Server Fix" -ForegroundColor Green
Write-Host "Fixing uvicorn command and restarting services" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Stop all services
Write-Host "Stopping all services..." -ForegroundColor Yellow
docker-compose down

# Remove the API server image to force rebuild
Write-Host "Removing old API server image..." -ForegroundColor Yellow
docker rmi rnr-iot-rnr_api_server 2>$null

# Build and start services
Write-Host "Building and starting services..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for services to start
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Service Status:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "API Server Logs (last 10 lines):" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
docker-compose logs rnr_api_server --tail=10

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Testing API endpoint..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "API Response: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "API not yet ready" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform Status:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "RabbitMQ Management: http://localhost:15672" -ForegroundColor Cyan
Write-Host "Database: localhost:15432" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all services show 'Up', the platform is ready!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
