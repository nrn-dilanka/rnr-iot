#!/bin/bash
# RNR Solutions - OpenAPI.json Fix for nginx (Updated)
# Fixes Bad Gateway error for OpenAPI endpoints with proper sudo handling

echo "=========================================="
echo "RNR IoT Platform - OpenAPI.json Fix"
echo "Fixing Bad Gateway error for OpenAPI endpoints"
echo "=========================================="

# Check if running as root or with sudo access
if [ "$EUID" -ne 0 ]; then
    echo "This script needs sudo access for nginx operations."
    echo "Please run: sudo ./fix_openapi_nginx_sudo.sh"
    exit 1
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "✗ Nginx is not installed!"
    echo "Please install nginx first: sudo apt update && sudo apt install nginx"
    exit 1
fi

# Check nginx status
echo "1. Checking nginx status..."
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx is running"
else
    echo "⚠ Nginx is not running - starting nginx..."
    systemctl start nginx
    if [ $? -eq 0 ]; then
        echo "✓ Nginx started successfully"
    else
        echo "✗ Failed to start nginx"
        exit 1
    fi
fi

# Test nginx configuration syntax
echo ""
echo "2. Testing nginx configuration syntax..."
if nginx -t; then
    echo "✓ Nginx configuration syntax is valid"
else
    echo "✗ Nginx configuration has syntax errors!"
    echo "Please fix the nginx.conf file first."
    exit 1
fi

# Reload nginx configuration
echo ""
echo "3. Reloading nginx configuration..."
if systemctl reload nginx; then
    echo "✓ Nginx configuration reloaded successfully"
else
    echo "✗ Failed to reload nginx configuration"
    exit 1
fi

# Wait for nginx to apply changes
echo ""
echo "4. Waiting for nginx to apply changes..."
sleep 3

# Test the fixed endpoints
echo ""
echo "5. Testing OpenAPI endpoints..."
echo "=========================================="

# Test health endpoint
echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health Status: %{http_code}\n" http://localhost/api/health

# Test OpenAPI endpoint
echo "Testing OpenAPI endpoint..."
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost/api/openapi.json

# Test docs endpoint
echo "Testing docs endpoint..."
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost/api/docs

echo ""
echo "6. Testing external access..."
echo "=========================================="

# Get public IP for testing
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "13.60.255.181")
echo "Testing with IP: $PUBLIC_IP"

# Test external endpoints
echo "Testing external health endpoint..."
curl -s -o /dev/null -w "External Health: %{http_code}\n" http://$PUBLIC_IP/api/health 2>/dev/null || echo "External Health: Network error"

echo "Testing external OpenAPI endpoint..."
curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"

echo ""
echo "=========================================="
echo "Fix Complete! Access URLs:"
echo "=========================================="
echo "🔧 Health Check: http://$PUBLIC_IP/api/health"
echo "📚 API Documentation: http://$PUBLIC_IP/api/docs"
echo "🔌 OpenAPI Schema: http://$PUBLIC_IP/api/openapi.json"
echo ""
echo "Local testing:"
echo "🔧 Health Check: http://localhost/api/health"
echo "📚 API Documentation: http://localhost/api/docs" 
echo "🔌 OpenAPI Schema: http://localhost/api/openapi.json"
echo ""
echo "If all endpoints show '200', the fix is successful!"
echo "If you still see 'Bad Gateway', check:"
echo "1. docker-compose ps (ensure API server is running)"
echo "2. docker-compose logs rnr_api_server"
echo "3. nginx error logs: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
