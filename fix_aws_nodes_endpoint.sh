#!/bin/bash

echo "🚀 Deploying Fixed Nodes Endpoint to AWS"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Stop all containers first
echo "� Stopping all containers..."
docker-compose down

# Remove old images to force rebuild
echo "�️ Removing old images..."
docker rmi $(docker images | grep rnr | awk '{print $3}') 2>/dev/null || echo "No old images to remove"

# Rebuild all services with no cache
echo "📦 Rebuilding all services..."
docker-compose build --no-cache

# Start the services
echo "🔄 Starting services..."
docker-compose up -d

# Wait for startup
echo "⏳ Waiting for server startup..."
sleep 15

# Test the endpoints
echo "🧪 Testing fixed endpoints..."

echo "1. Health Check:"
curl -s "http://localhost:3005/health" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Status: {data.get(\"status\", \"N/A\")}')
    print(f'   Database: {data.get(\"database\", \"N/A\")}')
    print(f'   Node Count: {data.get(\"node_count\", \"N/A\")}')
except Exception as e: 
    print(f'   ERROR: {e}')
"

echo -e "\n2. Database Test:"
curl -s "http://localhost:3005/api/database/test" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Database Status: {data.get(\"database_status\", \"N/A\")}')
    print(f'   Table Access: {data.get(\"node_table_accessible\", \"N/A\")}')
    print(f'   Total Nodes: {data.get(\"total_nodes\", \"N/A\")}')
    if data.get('error'):
        print(f'   Error: {data.get(\"error\", \"N/A\")}')
except Exception as e:
    print(f'   ERROR: {e}')
"

echo -e "\n3. Nodes Endpoint:"
curl -s "http://localhost:3005/api/nodes" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'   ✅ SUCCESS: {len(data)} nodes retrieved')
        for i, node in enumerate(data[:2]):
            print(f'      Node {i+1}: {node.get(\"node_id\", \"N/A\")} - {node.get(\"name\", \"N/A\")}')
    else:
        print(f'   Response: {data}')
except Exception as e:
    print(f'   ❌ ERROR: {e}')
"

echo -e "\n📋 Container Status:"
docker-compose ps

echo -e "\n🎯 Deployment Complete!"
echo "Remote endpoint should now work: http://13.60.227.209:3005/api/nodes"
