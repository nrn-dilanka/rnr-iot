#!/bin/bash
# RNR Solutions - OpenAPI Diagnostic Script (No Sudo Required)
# Diagnoses the Bad Gateway issue for OpenAPI endpoints

echo "=========================================="
echo "RNR IoT Platform - OpenAPI Diagnostic"
echo "Diagnosing Bad Gateway error for OpenAPI"
echo "=========================================="

# Check if services are running
echo "1. Checking Docker services..."
echo "=========================================="
docker-compose ps

echo ""
echo "2. Testing API server directly (bypassing nginx)..."
echo "=========================================="
echo "Testing direct API server health..."
curl -s -o /dev/null -w "Direct API Health: %{http_code}\n" http://localhost:8000/health 2>/dev/null || echo "Direct API Health: Connection failed"

echo "Testing direct API server OpenAPI..."
curl -s -o /dev/null -w "Direct API OpenAPI: %{http_code}\n" http://localhost:8000/openapi.json 2>/dev/null || echo "Direct API OpenAPI: Connection failed"

echo "Testing direct API server docs..."
curl -s -o /dev/null -w "Direct API Docs: %{http_code}\n" http://localhost:8000/docs 2>/dev/null || echo "Direct API Docs: Connection failed"

echo ""
echo "3. Testing through nginx proxy..."
echo "=========================================="
echo "Testing nginx proxied health..."
curl -s -o /dev/null -w "Nginx Health: %{http_code}\n" http://localhost/api/health 2>/dev/null || echo "Nginx Health: Connection failed"

echo "Testing nginx proxied OpenAPI..."
curl -s -o /dev/null -w "Nginx OpenAPI: %{http_code}\n" http://localhost/api/openapi.json 2>/dev/null || echo "Nginx OpenAPI: Connection failed"

echo "Testing nginx proxied docs..."
curl -s -o /dev/null -w "Nginx Docs: %{http_code}\n" http://localhost/api/docs 2>/dev/null || echo "Nginx Docs: Connection failed"

echo ""
echo "4. Checking nginx proxy configuration..."
echo "=========================================="
echo "Checking if nginx is running..."
if pgrep nginx > /dev/null; then
    echo "✓ Nginx is running"
else
    echo "✗ Nginx is not running"
fi

echo ""
echo "5. Checking API server logs..."
echo "=========================================="
echo "Last 10 lines of API server logs:"
docker-compose logs rnr_api_server --tail=10

echo ""
echo "=========================================="
echo "Diagnostic Summary:"
echo "=========================================="
echo "Expected Results:"
echo "- Direct API endpoints should return '200'"
echo "- Nginx proxied endpoints should return '200'"
echo ""
echo "If Direct API works but Nginx doesn't:"
echo "  → Run: sudo ./fix_openapi_nginx_sudo.sh"
echo ""
echo "If Direct API doesn't work:"
echo "  → Run: docker-compose restart rnr_api_server"
echo "  → Check: docker-compose logs rnr_api_server"
echo ""
echo "If both fail:"
echo "  → Run: docker-compose down && docker-compose up -d --build"
echo "=========================================="
