#!/bin/bash
# RNR Solutions - API Server Troubleshooting Script
# Diagnoses and fixes Bad Gateway and OpenAPI errors

echo "=========================================="
echo "RNR IoT Platform - API Troubleshooting"
echo "Diagnosing Bad Gateway and OpenAPI issues"
echo "=========================================="

# Check if services are running
echo "1. Checking service status..."
docker-compose ps

echo ""
echo "2. Checking API server logs..."
echo "=========================================="
docker-compose logs rnr_api_server --tail=20

echo ""
echo "3. Testing internal connectivity..."
echo "=========================================="

# Check if API server container is responding internally
echo "Testing API server container health..."
docker-compose exec rnr_api_server curl -s http://localhost:8000/health 2>/dev/null && echo "✓ Internal API: OK" || echo "✗ Internal API: Failed"

# Check if API server is accessible from host
echo "Testing API server from host..."
curl -s http://localhost:8000/health 2>/dev/null && echo "✓ Host to API: OK" || echo "✗ Host to API: Failed"

# Check OpenAPI endpoint specifically
echo "Testing OpenAPI endpoint..."
curl -s http://localhost:8000/openapi.json 2>/dev/null | head -c 100 && echo "... ✓ OpenAPI: OK" || echo "✗ OpenAPI: Failed"

echo ""
echo "4. Checking port availability..."
echo "=========================================="
netstat -tlnp | grep :8000 || echo "Port 8000 not listening"

echo ""
echo "5. Checking container networking..."
echo "=========================================="
docker network ls | grep rnr_iot_network
docker network inspect rnr-iot_rnr_iot_network 2>/dev/null | grep -A 10 "Containers" || echo "Network inspect failed"

echo ""
echo "6. Memory and resource check..."
echo "=========================================="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "=========================================="
echo "Diagnosis Summary:"
echo "=========================================="

# Restart API server if it's not healthy
echo "7. Attempting to restart API server..."
docker-compose restart rnr_api_server

echo "Waiting for API server to start..."
sleep 15

# Final test
echo ""
echo "8. Final connectivity test..."
echo "=========================================="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost:8000/openapi.json

echo ""
echo "=========================================="
echo "If issues persist, run: docker-compose down && docker-compose up -d --build"
echo "=========================================="
