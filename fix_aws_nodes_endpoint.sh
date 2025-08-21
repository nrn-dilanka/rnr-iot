#!/bin/bash

echo "🚀 Deploying Fixed Nodes Endpoint to AWS"
echo "========================================"

# Build and push the updated API server
echo "📦 Building updated API server..."
docker build -t rnr-iot-api:latest ./backend

echo "🔄 Restarting AWS deployment..."
# Stop current containers
docker-compose down rnr_api_server

# Start with updated image
docker-compose up -d rnr_api_server

# Wait for startup
echo "⏳ Waiting for server startup..."
sleep 10

# Test the endpoints
echo "🧪 Testing fixed endpoints..."

echo "1. Health Check:"
curl -s "http://localhost:3005/health" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Status: {data.get(\"status\", \"N/A\")}')
    print(f'   Database: {data.get(\"database\", \"N/A\")}')
except: pass
"

echo -e "\n2. Nodes Endpoint:"
curl -s "http://localhost:3005/api/nodes" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'   ✅ SUCCESS: {len(data)} nodes retrieved')
    else:
        print(f'   Response: {data}')
except Exception as e:
    print(f'   ❌ ERROR: {e}')
"

echo -e "\n🎯 Deployment Complete!"
echo "Remote endpoint should now work: http://13.60.227.209:3005/api/nodes"
