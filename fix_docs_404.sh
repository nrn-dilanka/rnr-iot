#!/bin/bash

echo "🔧 Fixing API Documentation 404 Error"
echo "====================================="

# Test nginx configuration
echo "📝 Testing nginx configuration..."
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

echo "✅ Nginx configuration is valid"

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Restart API server
echo "🔄 Restarting API server..."
docker-compose restart rnr_api_server

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 8

echo ""
echo "🧪 Testing endpoints..."

# Test the API server directly
echo "Testing API server health..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$API_RESPONSE" = "200" ]; then
    echo "✅ API server is running"
else
    echo "❌ API server not responding (HTTP $API_RESPONSE)"
fi

# Test docs endpoint on API server directly
echo "Testing docs on API server..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo "✅ Docs endpoint works on API server"
else
    echo "❌ Docs endpoint not working on API server (HTTP $DOCS_RESPONSE)"
fi

# Test openapi.json
echo "Testing OpenAPI JSON..."
OPENAPI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json)
if [ "$OPENAPI_RESPONSE" = "200" ]; then
    echo "✅ OpenAPI JSON endpoint works"
else
    echo "❌ OpenAPI JSON not working (HTTP $OPENAPI_RESPONSE)"
fi

echo ""
echo "🌐 External access URLs:"
PUBLIC_IP=$(curl -s ifconfig.me || echo "YOUR_SERVER_IP")
echo "   • Main docs: http://$PUBLIC_IP/docs"
echo "   • API docs:  http://$PUBLIC_IP/api/docs"
echo "   • ReDoc:     http://$PUBLIC_IP/api/redoc"
echo ""
echo "🏁 Fix complete! Try accessing the docs now."
