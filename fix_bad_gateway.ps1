# RNR Solutions - Complete API Server Fix (PowerShell)
# Fixes Bad Gateway and OpenAPI.json errors

Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform - Complete API Fix" -ForegroundColor Green
Write-Host "Fixing Bad Gateway and OpenAPI issues" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Stop all services
Write-Host "1. Stopping all services..." -ForegroundColor Yellow
docker-compose down

# Remove API server image to force complete rebuild
Write-Host "2. Removing old API server image..." -ForegroundColor Yellow
docker rmi rnr-iot-rnr_api_server 2>$null

# Rebuild and start services
Write-Host "3. Rebuilding services with health checks..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for initial startup
Write-Host "4. Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# Check service status
Write-Host "5. Checking service status..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "6. Testing API endpoints step by step..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green

# Test basic connectivity
Write-Host "Testing basic API connectivity..." -ForegroundColor Cyan
for ($i = 1; $i -le 5; $i++) {
    Write-Host "Attempt $i/5..." -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ API server is responding!" -ForegroundColor Green
        break
    } catch {
        Write-Host "✗ API server not ready, waiting 10s..." -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}

# Test health endpoint
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✓ Health endpoint: $($healthResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ Health endpoint failed" -ForegroundColor Red
}

# Test OpenAPI endpoint
Write-Host ""
Write-Host "Testing OpenAPI endpoint..." -ForegroundColor Cyan
try {
    $openApiResponse = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -TimeoutSec 10
    Write-Host "✓ OpenAPI endpoint: $($openApiResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ OpenAPI endpoint failed" -ForegroundColor Red
}

# Test docs endpoint
Write-Host ""
Write-Host "Testing docs endpoint..." -ForegroundColor Cyan
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 10
    Write-Host "✓ Docs endpoint: $($docsResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ Docs endpoint failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "7. Testing through nginx proxy..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green
try {
    $proxyResponse = Invoke-WebRequest -Uri "http://localhost/api/health" -TimeoutSec 5
    Write-Host "✓ Nginx proxy: $($proxyResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ Nginx proxy not available" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "8. Final service health check..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green
docker-compose ps
Write-Host ""
docker-compose logs rnr_api_server --tail=5

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Fix Complete! Access points:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "🔧 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔌 OpenAPI Schema: http://localhost:8000/openapi.json" -ForegroundColor Cyan
Write-Host "🌐 External API: http://13.60.255.181/api/health" -ForegroundColor Cyan
Write-Host "📖 External Docs: http://13.60.255.181/api/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you still see errors, check:" -ForegroundColor Yellow
Write-Host "1. Service logs: docker-compose logs rnr_api_server" -ForegroundColor White
Write-Host "2. Container status: docker-compose ps" -ForegroundColor White
Write-Host "3. Port availability: netstat -an | findstr :8000" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Green
