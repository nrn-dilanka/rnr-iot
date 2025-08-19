#!/bin/bash
# RNR Solutions - Direct OpenAPI Fix
# Simple, focused fix for OpenAPI JSON truncation

echo "=========================================="
echo "RNR IoT Platform - Direct OpenAPI Fix"
echo "Ensuring complete OpenAPI JSON delivery"
echo "=========================================="

# First, let's test the API server directly to ensure it's working
echo "1. Testing API server directly..."
echo "=========================================="

echo "Direct API server OpenAPI test..."
DIRECT_RESPONSE=$(curl -s http://localhost:8000/openapi.json)
DIRECT_SIZE=${#DIRECT_RESPONSE}
echo "Direct API OpenAPI size: $DIRECT_SIZE characters"

if [ $DIRECT_SIZE -gt 10000 ]; then
    echo "✓ Direct API server returns complete OpenAPI JSON"
    
    # Check if it's valid JSON
    if echo "$DIRECT_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
        echo "✓ Direct API OpenAPI JSON is valid"
        
        # Check version field
        if echo "$DIRECT_RESPONSE" | grep -q '"openapi"'; then
            VERSION=$(echo "$DIRECT_RESPONSE" | grep -o '"openapi":"[^"]*"' | head -1)
            echo "✓ Direct API OpenAPI version: $VERSION"
        fi
    else
        echo "✗ Direct API OpenAPI JSON is invalid"
    fi
else
    echo "✗ Direct API server OpenAPI appears incomplete"
    echo "Response: $DIRECT_RESPONSE"
    exit 1
fi

# Create a simplified nginx configuration that prioritizes OpenAPI delivery
echo ""
echo "2. Creating simplified nginx configuration..."
echo "=========================================="

sudo tee /etc/nginx/sites-enabled/rnr-iot > /dev/null << 'EOF'
# RNR Solutions IoT Platform - Simplified nginx Configuration
server {
    listen 80;
    server_name _;
    
    # Disable default buffering limits that might truncate responses
    proxy_buffering off;
    proxy_request_buffering off;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Root location - Redirect to API documentation
    location / {
        return 301 /api/docs;
    }

    # Direct health endpoint
    location = /health {
        proxy_pass http://localhost:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OpenAPI endpoint with maximum simplicity - NO BUFFERING
    location = /api/openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Completely disable all buffering for this endpoint
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_max_temp_file_size 0;
        
        # Set proper content type
        proxy_set_header Accept "application/json";
        add_header Content-Type "application/json" always;
        
        # Extended timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Docs endpoint with no buffering
    location = /api/docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # All other API routes
    location /api/ {
        # Remove /api prefix
        rewrite ^/api/(.*)$ /$1 break;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Minimal buffering
        proxy_buffering off;
        proxy_request_buffering off;
        
        # Standard timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
EOF

echo "✓ Simplified nginx configuration created (no buffering)"

# Test nginx configuration
echo ""
echo "3. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✓ nginx configuration is valid"
else
    echo "✗ nginx configuration has errors!"
    sudo nginx -t
    exit 1
fi

# Reload nginx
echo ""
echo "4. Reloading nginx..."
if sudo systemctl reload nginx; then
    echo "✓ nginx reloaded successfully"
else
    echo "⚠ Reload failed, trying restart..."
    sudo systemctl restart nginx
    if [ $? -eq 0 ]; then
        echo "✓ nginx restarted successfully"
    else
        echo "✗ Failed to restart nginx"
        exit 1
    fi
fi

# Wait for nginx to settle
echo ""
echo "5. Waiting for nginx to settle..."
sleep 5

# Comprehensive testing
echo ""
echo "6. Testing OpenAPI through nginx..."
echo "=========================================="

echo "Testing proxied OpenAPI JSON..."
PROXIED_RESPONSE=$(curl -s http://localhost/api/openapi.json)
PROXIED_SIZE=${#PROXIED_RESPONSE}
echo "Proxied OpenAPI size: $PROXIED_SIZE characters"

# Compare direct vs proxied
echo "Size comparison:"
echo "  Direct API: $DIRECT_SIZE characters"
echo "  Through nginx: $PROXIED_SIZE characters"

if [ $PROXIED_SIZE -eq $DIRECT_SIZE ]; then
    echo "✓ Proxied response matches direct response exactly"
elif [ $PROXIED_SIZE -gt 10000 ]; then
    echo "✓ Proxied response appears complete"
else
    echo "✗ Proxied response appears truncated"
    echo "First 200 characters of proxied response:"
    echo "$PROXIED_RESPONSE" | head -c 200
    echo "..."
fi

# Validate JSON structure
if echo "$PROXIED_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    echo "✓ Proxied OpenAPI JSON is valid"
    
    # Check for OpenAPI version
    if echo "$PROXIED_RESPONSE" | grep -q '"openapi"'; then
        VERSION=$(echo "$PROXIED_RESPONSE" | grep -o '"openapi":"[^"]*"' | head -1)
        echo "✓ Proxied OpenAPI version found: $VERSION"
    else
        echo "✗ No OpenAPI version field in proxied response"
    fi
    
    # Check for required fields
    if echo "$PROXIED_RESPONSE" | grep -q '"info"' && echo "$PROXIED_RESPONSE" | grep -q '"paths"'; then
        echo "✓ Required OpenAPI fields present"
    else
        echo "✗ Missing required OpenAPI fields"
    fi
else
    echo "✗ Proxied OpenAPI JSON is invalid"
    echo "JSON validation error - response may be truncated"
fi

echo ""
echo "7. Testing all endpoints..."
echo "=========================================="

curl -s -o /dev/null -w "Health: %{http_code}\n" http://localhost/api/health
curl -s -o /dev/null -w "OpenAPI: %{http_code}\n" http://localhost/api/openapi.json
curl -s -o /dev/null -w "Docs: %{http_code}\n" http://localhost/api/docs

echo ""
echo "8. Testing external access..."
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "13.60.255.181")
echo "Testing external access via $PUBLIC_IP..."

curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"
curl -s -o /dev/null -w "External Docs: %{http_code}\n" http://$PUBLIC_IP/api/docs 2>/dev/null || echo "External Docs: Network error"

echo ""
echo "=========================================="
echo "Direct OpenAPI Fix Complete! 🎉"
echo "=========================================="
echo ""
echo "Configuration changes:"
echo "✓ Disabled ALL proxy buffering for OpenAPI endpoint"
echo "✓ Extended timeouts for large responses"
echo "✓ Direct pass-through of JSON content"
echo "✓ Proper content-type headers"
echo ""
echo "Test your Swagger UI now:"
echo "📚 http://$PUBLIC_IP/api/docs"
echo ""
echo "If the parser error persists:"
echo "1. Check the raw JSON: curl -s http://$PUBLIC_IP/api/openapi.json | head -50"
echo "2. Compare sizes: Direct=$DIRECT_SIZE vs Proxied=$PROXIED_SIZE"
echo "3. Check nginx errors: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
