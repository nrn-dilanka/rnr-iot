# RNR Solutions - API-Only Platform Deployment (PowerShell)
# Optimized for 2GB RAM without frontend service

Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform - API-Only Deployment" -ForegroundColor Green
Write-Host "Deploying backend services without frontend" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Stop all services
Write-Host "Stopping all services..." -ForegroundColor Yellow
docker-compose down

# Remove old images to ensure clean build
Write-Host "Cleaning old images..." -ForegroundColor Yellow
docker rmi rnr-iot-rnr_api_server 2>$null

# Start only backend services
Write-Host "Starting backend services..." -ForegroundColor Yellow
docker-compose up -d --build rnr_rabbitmq rnr_postgres rnr_api_server rnr_worker_service

# Wait for services to initialize
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Backend Service Status:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "API Server Health Check:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Start-Sleep -Seconds 5

# Test API endpoints
Write-Host "Testing API server connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✓ API Health: OK" -ForegroundColor Green
} catch {
    Write-Host "✗ API Health: Failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform - API-Only Mode:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "🚀 API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📋 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔧 API Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🐰 RabbitMQ Management: http://localhost:15672" -ForegroundColor Cyan
Write-Host "🗄️  Database: localhost:15432" -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 External Access:" -ForegroundColor Magenta
Write-Host "🌐 API Server: http://13.60.255.181/api" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://13.60.255.181/api/docs" -ForegroundColor Cyan
Write-Host "💓 Health Check: http://13.60.255.181/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Memory Usage (optimized for 2GB):" -ForegroundColor Yellow
Write-Host "- RabbitMQ: 300MB" -ForegroundColor White
Write-Host "- PostgreSQL: 384MB" -ForegroundColor White
Write-Host "- API Server: 512MB" -ForegroundColor White
Write-Host "- Worker Service: 384MB" -ForegroundColor White
Write-Host "- Total: ~1.58GB (leaving 400MB+ for system)" -ForegroundColor White
Write-Host ""
Write-Host "✅ API-only platform is ready!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
