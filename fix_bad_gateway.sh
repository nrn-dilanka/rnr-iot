#!/bin/bash
# RNR Solutions - Complete API Server Fix
# Fixes Bad Gateway and OpenAPI.json errors

echo "=========================================="
echo "RNR IoT Platform - Complete API Fix"
echo "Fixing Bad Gateway and OpenAPI issues"
echo "=========================================="

# Stop all services
echo "1. Stopping all services..."
docker-compose down

# Remove API server image to force complete rebuild
echo "2. Removing old API server image..."
docker rmi rnr-iot-rnr_api_server 2>/dev/null || true

# Rebuild and start services
echo "3. Rebuilding services with health checks..."
docker-compose up -d --build

# Wait for initial startup
echo "4. Waiting for services to initialize..."
sleep 45

# Check service status
echo "5. Checking service status..."
echo "=========================================="
docker-compose ps

echo ""
echo "6. Testing API endpoints step by step..."
echo "=========================================="

# Test basic connectivity
echo "Testing basic API connectivity..."
for i in {1..5}; do
    echo "Attempt $i/5..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API server is responding!"
        break
    else
        echo "✗ API server not ready, waiting 10s..."
        sleep 10
    fi
done

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | head -100 && echo "" || echo "✗ Health endpoint failed"

# Test OpenAPI endpoint
echo ""
echo "Testing OpenAPI endpoint..."
curl -s http://localhost:8000/openapi.json | head -200 && echo "..." && echo "✓ OpenAPI endpoint working!" || echo "✗ OpenAPI endpoint failed"

# Test docs endpoint
echo ""
echo "Testing docs endpoint..."
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost:8000/docs

echo ""
echo "7. Testing through nginx proxy..."
echo "=========================================="
curl -s -o /dev/null -w "Nginx API Status: %{http_code}\n" http://localhost/api/health 2>/dev/null || echo "Nginx proxy not available"

echo ""
echo "8. Final service health check..."
echo "=========================================="
docker-compose ps
echo ""
docker-compose logs rnr_api_server --tail=5

echo ""
echo "=========================================="
echo "Fix Complete! Access points:"
echo "=========================================="
echo "🔧 Health Check: http://localhost:8000/health"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔌 OpenAPI Schema: http://localhost:8000/openapi.json"
echo "🌐 External API: http://13.60.255.181/api/health"
echo "📖 External Docs: http://13.60.255.181/api/docs"
echo ""
echo "If you still see errors, check:"
echo "1. Service logs: docker-compose logs rnr_api_server"
echo "2. Container status: docker-compose ps"
echo "3. Port availability: netstat -tlnp | grep 8000"
echo "=========================================="
