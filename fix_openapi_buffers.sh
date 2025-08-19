#!/bin/bash
# RNR Solutions - OpenAPI JSON Fix (Buffer Sizes Corrected)
# Fixes parser errors with proper nginx buffer calculations

echo "=========================================="
echo "RNR IoT Platform - OpenAPI JSON Fix"
echo "Fixing parser errors with corrected buffer sizes"
echo "=========================================="

# Create the corrected nginx configuration with proper buffer calculations
echo "1. Creating nginx configuration with corrected buffer sizes..."

sudo tee /etc/nginx/sites-enabled/rnr-iot > /dev/null << 'EOF'
# RNR Solutions IoT Platform - nginx Site Configuration (Buffer Fixed)
server {
    listen 80;
    server_name _;
    
    # Global proxy settings for better JSON handling
    proxy_buffer_size 64k;
    proxy_buffers 8 64k;
    proxy_busy_buffers_size 128k;  # Less than 8*64k = 512k
    
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
        proxy_buffering on;
    }

    # OpenAPI JSON endpoint with enhanced buffering
    location = /api/openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enhanced buffering for large JSON (proper calculations)
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 8 128k;          # 8 * 128k = 1024k total
        proxy_busy_buffers_size 256k;  # Less than 1024k - 128k = 896k
        proxy_temp_file_write_size 128k;
        
        # Ensure JSON content type
        proxy_set_header Accept "application/json";
        
        # Extended timeouts for large JSON
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # API docs endpoint with enhanced buffering
    location = /api/docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enhanced buffering for docs page
        proxy_buffering on;
        proxy_buffer_size 32k;
        proxy_buffers 4 32k;           # 4 * 32k = 128k total
        proxy_busy_buffers_size 64k;   # Less than 128k - 32k = 96k
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
        
        # Standard buffering for API responses
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 4 16k;           # 4 * 16k = 64k total
        proxy_busy_buffers_size 32k;   # Less than 64k - 16k = 48k
        
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

echo "✓ nginx configuration created with corrected buffer sizes"

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

# Test the fixed endpoints with detailed JSON validation
echo ""
echo "5. Testing OpenAPI JSON integrity..."
echo "=========================================="

echo "Fetching OpenAPI JSON and checking integrity..."
OPENAPI_RESPONSE=$(curl -s http://localhost/api/openapi.json)
OPENAPI_SIZE=${#OPENAPI_RESPONSE}
echo "OpenAPI JSON size: $OPENAPI_SIZE characters"

if [ $OPENAPI_SIZE -gt 10000 ]; then
    echo "✓ OpenAPI JSON appears to be complete (>10KB)"
    
    # Check for valid JSON structure
    if echo "$OPENAPI_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
        echo "✓ OpenAPI JSON is valid"
        
        # Check for OpenAPI version field
        if echo "$OPENAPI_RESPONSE" | grep -q '"openapi"'; then
            OPENAPI_VERSION=$(echo "$OPENAPI_RESPONSE" | grep -o '"openapi":"[^"]*"' | head -1)
            echo "✓ OpenAPI version field found: $OPENAPI_VERSION"
        else
            echo "✗ OpenAPI version field missing"
        fi
        
        # Check for complete structure
        if echo "$OPENAPI_RESPONSE" | grep -q '"paths"' && echo "$OPENAPI_RESPONSE" | grep -q '"components"'; then
            echo "✓ OpenAPI structure appears complete (has paths and components)"
        else
            echo "⚠ OpenAPI structure may be incomplete"
        fi
    else
        echo "✗ OpenAPI JSON is invalid"
        echo "First 500 characters:"
        echo "$OPENAPI_RESPONSE" | head -c 500
        echo "..."
        echo "Last 200 characters:"
        echo "$OPENAPI_RESPONSE" | tail -c 200
    fi
else
    echo "✗ OpenAPI JSON appears to be truncated or missing"
    echo "Response received: $OPENAPI_RESPONSE"
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

echo "Testing external OpenAPI..."
curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"

echo "Testing external docs..."
curl -s -o /dev/null -w "External Docs: %{http_code}\n" http://$PUBLIC_IP/api/docs 2>/dev/null || echo "External Docs: Network error"

echo ""
echo "=========================================="
echo "OpenAPI JSON Fix Complete! 🎉"
echo "=========================================="
echo "Buffer Configuration Applied:"
echo "✓ OpenAPI endpoint: 128k buffers for large JSON"
echo "✓ Docs endpoint: 32k buffers for HTML content"
echo "✓ API endpoints: 16k buffers for standard responses"
echo "✓ All buffer calculations are mathematically correct"
echo ""
echo "Access URLs:"
echo "📚 API Documentation: http://$PUBLIC_IP/api/docs"
echo "🔌 OpenAPI Schema: http://$PUBLIC_IP/api/openapi.json"
echo "🔧 Health Check: http://$PUBLIC_IP/api/health"
echo ""
echo "The Swagger UI should now load without parser errors!"
echo ""
echo "If issues persist:"
echo "1. Check JSON: curl -s http://$PUBLIC_IP/api/openapi.json | head -100"
echo "2. Check logs: docker-compose logs rnr_api_server --tail=10"
echo "3. Check nginx: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
