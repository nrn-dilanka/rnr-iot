#!/bin/bash
# RNR Solutions - nginx Configuration Fix (Corrected)
# Fixes the limit_req_zone directive placement issue

echo "=========================================="
echo "RNR IoT Platform - nginx Configuration Fix"
echo "Resolving 404 errors and rate limiting config"
echo "=========================================="

# Create the correct nginx site configuration without rate limiting in server block
echo "1. Creating corrected nginx site configuration..."

sudo tee /etc/nginx/sites-enabled/rnr-iot > /dev/null << 'EOF'
# RNR Solutions IoT Platform - nginx Site Configuration
server {
    listen 80;
    server_name _;
    
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
    }

    # API routes - Remove /api prefix and forward to backend
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

echo "✓ nginx site configuration created (without rate limiting zones)"

# Remove default nginx site if it exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "Removing default nginx site..."
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
echo ""
echo "2. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✓ nginx configuration is valid"
else
    echo "✗ nginx configuration has errors!"
    echo "Showing detailed error:"
    sudo nginx -t
    exit 1
fi

# Reload nginx
echo ""
echo "3. Reloading nginx..."
if sudo systemctl reload nginx; then
    echo "✓ nginx reloaded successfully"
else
    echo "✗ Failed to reload nginx"
    echo "Trying restart instead..."
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
sleep 3

# Test the fixed endpoints
echo ""
echo "5. Testing fixed endpoints..."
echo "=========================================="

echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health Status: %{http_code}\n" http://localhost/api/health

echo "Testing OpenAPI endpoint..."
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost/api/openapi.json

echo "Testing docs endpoint..."
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost/api/docs

echo ""
echo "6. Testing external access..."
echo "=========================================="
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "13.60.255.181")
echo "Testing with IP: $PUBLIC_IP"

echo "Testing external health endpoint..."
curl -s -o /dev/null -w "External Health: %{http_code}\n" http://$PUBLIC_IP/api/health 2>/dev/null || echo "External Health: Network error"

echo "Testing external OpenAPI endpoint..."
curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"

echo "Testing external docs endpoint..."
curl -s -o /dev/null -w "External Docs: %{http_code}\n" http://$PUBLIC_IP/api/docs 2>/dev/null || echo "External Docs: Network error"

echo ""
echo "=========================================="
echo "Fix Complete! 🎉"
echo "=========================================="
echo "All endpoints should now return '200':"
echo ""
echo "🔧 Health Check: http://$PUBLIC_IP/api/health"
echo "📚 API Documentation: http://$PUBLIC_IP/api/docs"
echo "🔌 OpenAPI Schema: http://$PUBLIC_IP/api/openapi.json"
echo ""
echo "Local URLs:"
echo "🔧 Health Check: http://localhost/api/health"
echo "📚 API Documentation: http://localhost/api/docs"
echo "🔌 OpenAPI Schema: http://localhost/api/openapi.json"
echo ""
echo "If any endpoint still shows '404':"
echo "1. Check nginx error log: sudo tail -f /var/log/nginx/error.log"
echo "2. Check API server: docker-compose logs rnr_api_server"
echo "3. Verify services: docker-compose ps"
echo "=========================================="
