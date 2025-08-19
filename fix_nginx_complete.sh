#!/bin/bash
# RNR Solutions - Quick nginx Configuration Fix
# Checks and fixes nginx configuration for API proxy

echo "=========================================="
echo "RNR IoT Platform - nginx Configuration Fix"
echo "Resolving 404 errors for /api/* endpoints"
echo "=========================================="

# Check current nginx configuration location
echo "1. Checking nginx configuration..."
echo "Default nginx config location: /etc/nginx/nginx.conf"
echo "Project nginx config location: $(pwd)/nginx.conf"

# Show current nginx processes and config
echo ""
echo "2. Current nginx process info..."
ps aux | grep nginx | grep -v grep

# Check if our nginx.conf is being used
echo ""
echo "3. Checking nginx configuration file..."
if [ -f "/etc/nginx/nginx.conf" ]; then
    echo "✓ Default nginx config exists"
    echo "Checking if it includes our configuration..."
    
    # Check if there's a sites-enabled or conf.d directory
    if [ -d "/etc/nginx/sites-enabled" ]; then
        echo "✓ sites-enabled directory found"
        NGINX_SITE_CONFIG="/etc/nginx/sites-enabled/rnr-iot"
    elif [ -d "/etc/nginx/conf.d" ]; then
        echo "✓ conf.d directory found"
        NGINX_SITE_CONFIG="/etc/nginx/conf.d/rnr-iot.conf"
    else
        echo "✗ No sites-enabled or conf.d directory found"
        NGINX_SITE_CONFIG="/etc/nginx/nginx.conf"
    fi
else
    echo "✗ Default nginx config not found"
    exit 1
fi

echo "Target config location: $NGINX_SITE_CONFIG"

# Copy our nginx configuration to the correct location
echo ""
echo "4. Installing nginx configuration..."
if [ -f "$(pwd)/nginx.conf" ]; then
    echo "✓ Found project nginx.conf"
    
    # Create nginx site configuration
    echo "Creating nginx site configuration..."
    sudo tee "$NGINX_SITE_CONFIG" > /dev/null << 'EOF'
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

    # Rate limiting for API protection
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

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
        limit_req zone=api burst=20 nodelay;
        
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

    # File upload endpoint with special limits
    location /api/upload {
        limit_req zone=upload burst=5 nodelay;
        
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

    echo "✓ nginx site configuration created"
    
    # Remove default nginx site if it exists
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        echo "Removing default nginx site..."
        sudo rm -f /etc/nginx/sites-enabled/default
    fi
    
else
    echo "✗ Project nginx.conf not found!"
    exit 1
fi

# Test nginx configuration
echo ""
echo "5. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✓ nginx configuration is valid"
else
    echo "✗ nginx configuration has errors!"
    exit 1
fi

# Reload nginx
echo ""
echo "6. Reloading nginx..."
if sudo systemctl reload nginx; then
    echo "✓ nginx reloaded successfully"
else
    echo "✗ Failed to reload nginx"
    exit 1
fi

# Wait for nginx to apply changes
echo ""
echo "7. Waiting for nginx to apply changes..."
sleep 3

# Test the fixed endpoints
echo ""
echo "8. Testing fixed endpoints..."
echo "=========================================="

echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health Status: %{http_code}\n" http://localhost/api/health

echo "Testing OpenAPI endpoint..."
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" http://localhost/api/openapi.json

echo "Testing docs endpoint..."
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" http://localhost/api/docs

echo ""
echo "9. Testing external access..."
echo "=========================================="
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "13.60.255.181")
echo "Testing with IP: $PUBLIC_IP"

curl -s -o /dev/null -w "External Health: %{http_code}\n" http://$PUBLIC_IP/api/health 2>/dev/null || echo "External Health: Network error"
curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" http://$PUBLIC_IP/api/openapi.json 2>/dev/null || echo "External OpenAPI: Network error"

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
echo "If any endpoint still shows '404' or 'Network error':"
echo "1. Check nginx error log: sudo tail -f /var/log/nginx/error.log"
echo "2. Restart nginx: sudo systemctl restart nginx"
echo "3. Check firewall: sudo ufw status"
echo "=========================================="
