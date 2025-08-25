#!/bin/bash
# RNR Solutions - Fix OpenAPI.json Bad Gateway Error
# Reloads nginx with fixed proxy configuration

echo "=========================================="
echo "RNR IoT Platform - OpenAPI.json Fix"
echo "Fixing Bad Gateway error for OpenAPI endpoints"
echo "=========================================="

# Check nginx configuration syntax
echo "1. Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Nginx configuration is valid"
    
    # Reload nginx with new configuration
    echo "2. Reloading nginx..."
    systemctl reload nginx || service nginx reload
    
    echo "3. Waiting for nginx to reload..."
    sleep 5
    
    # Test the fixed endpoints
    echo "4. Testing fixed endpoints..."
    echo "=========================================="
    
    echo "Testing health endpoint..."
    curl -s -o /dev/null -w "Health Status: %{http_code}\n" http://localhost/api/health
    
    echo "Testing OpenAPI endpoint..."
    curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost/api/openapi.json
    
    echo "Testing docs endpoint..."
    curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost/api/docs
    
    echo ""
    echo "=========================================="
    echo "Testing external access..."
    echo "=========================================="
    
    # Test external access if available
    curl -s -o /dev/null -w "External Health: %{http_code}\n" http://13.60.255.181/api/health 2>/dev/null || echo "External Health: Network error"
    curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://13.60.255.181/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"
    
    echo ""
    echo "=========================================="
    echo "Fix Complete!"
    echo "=========================================="
    echo "📚 API Documentation: http://13.60.255.181/api/docs"
    echo "🔌 OpenAPI Schema: http://13.60.255.181/api/openapi.json"
    echo "🔧 Health Check: http://13.60.255.181/api/health"
    echo ""
    echo "The nginx proxy now correctly strips the /api/ prefix"
    echo "when forwarding requests to the backend API server."
    echo "=========================================="
else
    echo "✗ Nginx configuration has errors!"
    echo "Please check the nginx.conf file for syntax issues."
fi
