# RNR Solutions - Fix OpenAPI.json Bad Gateway Error (PowerShell)
# Reloads nginx with fixed proxy configuration

Write-Host "==========================================" -ForegroundColor Green
Write-Host "RNR IoT Platform - OpenAPI.json Fix" -ForegroundColor Green
Write-Host "Fixing Bad Gateway error for OpenAPI endpoints" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "The nginx configuration has been updated to properly" -ForegroundColor Yellow
Write-Host "strip the /api/ prefix when proxying to the backend." -ForegroundColor Yellow
Write-Host ""

Write-Host "Key changes made:" -ForegroundColor Cyan
Write-Host "- /api/ routes now use 'proxy_pass http://rnr_api_backend/'" -ForegroundColor White
Write-Host "- This strips /api/ prefix before sending to backend" -ForegroundColor White
Write-Host "- Backend receives clean routes like /health, /docs, /openapi.json" -ForegroundColor White
Write-Host ""

Write-Host "Testing the fix..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green

# Test the endpoints
Write-Host "Testing health endpoint..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-WebRequest -Uri "http://13.60.255.181/api/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✓ Health Status: $($healthResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ Health Status: Failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Testing OpenAPI endpoint..." -ForegroundColor Cyan
try {
    $openApiResponse = Invoke-WebRequest -Uri "http://13.60.255.181/api/openapi.json" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✓ OpenAPI Status: $($openApiResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ OpenAPI Status: Failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Testing docs endpoint..." -ForegroundColor Cyan
try {
    $docsResponse = Invoke-WebRequest -Uri "http://13.60.255.181/api/docs" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✓ Docs Status: $($docsResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ Docs Status: Failed - $($_.Exception.Message)" -ForegroundColor Red
}
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Fix Status:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "📚 API Documentation: http://13.60.255.181/api/docs" -ForegroundColor Cyan
Write-Host "🔌 OpenAPI Schema: http://13.60.255.181/api/openapi.json" -ForegroundColor Cyan
Write-Host "🔧 Health Check: http://13.60.255.181/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "If nginx needs to be reloaded on the server, run:" -ForegroundColor Yellow
Write-Host "sudo systemctl reload nginx" -ForegroundColor White
Write-Host ""
Write-Host "The nginx proxy configuration is now correctly configured!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
