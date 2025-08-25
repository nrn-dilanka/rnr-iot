#!/bin/bash

# Quick fix for OpenAPI docs endpoint
# RNR Solutions IoT Platform

set -e

echo "🔧 Fixing OpenAPI docs endpoint..."

# Test nginx configuration
echo "📝 Testing nginx configuration..."
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Restart API server to pick up FastAPI changes
echo "🔄 Restarting API server..."
docker-compose restart rnr_api_server

# Wait a moment for the service to start
echo "⏳ Waiting for API server to start..."
sleep 5

# Test the endpoints
echo "🧪 Testing endpoints..."
API_HOST="localhost:8000"

echo "Testing health endpoint..."
curl -s "http://${API_HOST}/health" | head -1

echo ""
echo "Testing OpenAPI JSON endpoint..."
curl -s "http://${API_HOST}/openapi.json" | head -1

echo ""
echo "✅ Fix complete!"
echo ""
echo "📖 Access documentation at:"
echo "   • http://$(curl -s ifconfig.me || echo 'YOUR_IP')/docs"
echo "   • http://$(curl -s ifconfig.me || echo 'YOUR_IP')/api/docs"
echo "   • http://$(curl -s ifconfig.me || echo 'YOUR_IP')/redoc"
