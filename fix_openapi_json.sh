#!/bin/bash
# RNR Solutions - Fix OpenAPI JSON Parsing Error
# Fixes truncated JSON responses and parser errors

echo "=========================================="
echo "RNR IoT Platform - OpenAPI JSON Fix"
echo "Fixing parser errors and JSON truncation"
echo "=========================================="

# Create the corrected nginx configuration with proper JSON handling
echo "1. Creating corrected nginx configuration with JSON handling..."

sudo tee /etc/nginx/sites-enabled/rnr-iot > /dev/null << 'EOF'
# RNR Solutions IoT Platform - nginx Site Configuration (JSON Fixed)
server {
    listen 80;
    server_name _;
    
    # Increase buffer sizes for large JSON responses
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Root location - Redirect to API documentation
    location / {
        return 301 /api/docs;
    }

    # API health check endpoint (direct)
    location = /health {
        proxy_pass http://localhost:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Ensure proper buffering for JSON responses
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 16k;
    }

    # OpenAPI JSON endpoint with special handling
    location = /api/openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Special settings for large JSON responses
        proxy_buffering on;
        proxy_buffer_size 256k;
        proxy_buffers 8 256k;
        proxy_busy_buffers_size 256k;
        proxy_temp_file_write_size 256k;
        
        # Ensure JSON content type
        proxy_set_header Accept "application/json";
        
        # Prevent timeout for large JSON
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # API docs endpoint with special handling
    location = /api/docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enhanced buffering for docs page
        proxy_buffering on;
        proxy_buffer_size 64k;
        proxy_buffers 8 64k;
        proxy_busy_buffers_size 64k;
    }

    # Other API routes - Remove /api prefix and forward to backend
    location /api/ {
        # Remove /api prefix: /api/health -> /health
        rewrite ^/api/(.*)$ /$1 break;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Enhanced buffering for API responses
        proxy_buffering on;
        proxy_buffer_size 32k;
        proxy_buffers 8 32k;
        proxy_busy_buffers_size 64k;
        
        # Timeouts for API calls
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket connections for real-time data
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering for WebSockets
        proxy_buffering off;
        
        # WebSocket specific timeouts
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # File upload endpoint with special handling
    location /api/upload {
        # Remove /api prefix: /api/upload -> /upload
        rewrite ^/api/upload$ /upload break;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts for file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        client_max_body_size 100M;
        
        # Disable buffering for uploads
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # RabbitMQ Management UI (optional - for development/monitoring)
    location /rabbitmq/ {
        proxy_pass http://localhost:15672/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "✓ nginx configuration created with enhanced JSON handling"

# Test nginx configuration
echo ""
echo "2. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✓ nginx configuration is valid"
else
    echo "✗ nginx configuration has errors!"
    sudo nginx -t
    exit 1
fi

# Reload nginx
echo ""
echo "3. Reloading nginx..."
if sudo systemctl reload nginx; then
    echo "✓ nginx reloaded successfully"
else
    echo "✗ Failed to reload nginx, trying restart..."
    sudo systemctl restart nginx
    if [ $? -eq 0 ]; then
        echo "✓ nginx restarted successfully"
    else
        echo "✗ Failed to restart nginx"
        exit 1
    fi
fi

# Wait for nginx to apply changes
echo ""
echo "4. Waiting for nginx to apply changes..."
sleep 5

# Test the fixed endpoints with detailed output
echo ""
echo "5. Testing OpenAPI JSON specifically..."
echo "=========================================="

echo "Testing OpenAPI JSON size and validity..."
OPENAPI_RESPONSE=$(curl -s http://localhost/api/openapi.json)
OPENAPI_SIZE=${#OPENAPI_RESPONSE}
echo "OpenAPI JSON size: $OPENAPI_SIZE characters"

if [ $OPENAPI_SIZE -gt 1000 ]; then
    echo "✓ OpenAPI JSON appears to be complete"
    
    # Check for valid JSON structure
    echo "$OPENAPI_RESPONSE" | python3 -m json.tool > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ OpenAPI JSON is valid"
        
        # Check for OpenAPI version field
        if echo "$OPENAPI_RESPONSE" | grep -q '"openapi"'; then
            echo "✓ OpenAPI version field found"
            echo "OpenAPI version: $(echo "$OPENAPI_RESPONSE" | grep -o '"openapi":"[^"]*"')"
        else
            echo "✗ OpenAPI version field missing"
        fi
    else
        echo "✗ OpenAPI JSON is invalid"
        echo "First 200 characters:"
        echo "$OPENAPI_RESPONSE" | head -c 200
    fi
else
    echo "✗ OpenAPI JSON appears to be truncated"
    echo "Response: $OPENAPI_RESPONSE"
fi

echo ""
echo "6. Testing all endpoints..."
echo "=========================================="

echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health Status: %{http_code}\n" http://localhost/api/health

echo "Testing OpenAPI endpoint..."
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost/api/openapi.json

echo "Testing docs endpoint..."
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost/api/docs

echo ""
echo "7. Testing external access..."
echo "=========================================="
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "13.60.255.181")
echo "Testing with IP: $PUBLIC_IP"

echo "Testing external OpenAPI endpoint..."
curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"

echo "Testing external docs endpoint..."
curl -s -o /dev/null -w "External Docs: %{http_code}\n" http://$PUBLIC_IP/api/docs 2>/dev/null || echo "External Docs: Network error"

echo ""
echo "=========================================="
echo "OpenAPI JSON Fix Complete! 🎉"
echo "=========================================="
echo "The OpenAPI specification should now load correctly:"
echo ""
echo "📚 API Documentation: http://$PUBLIC_IP/api/docs"
echo "🔌 OpenAPI Schema: http://$PUBLIC_IP/api/openapi.json"
echo "🔧 Health Check: http://$PUBLIC_IP/api/health"
echo ""
echo "Key improvements:"
echo "✓ Enhanced proxy buffering for large JSON responses"
echo "✓ Specific handling for OpenAPI.json endpoint"
echo "✓ Proper JSON content-type handling"
echo "✓ Increased timeouts for complex responses"
echo ""
echo "If docs still show parser errors:"
echo "1. Check: curl -s http://$PUBLIC_IP/api/openapi.json | head -100"
echo "2. Verify: docker-compose logs rnr_api_server --tail=20"
echo "3. Debug: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
