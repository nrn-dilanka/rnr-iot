#!/bin/bash

echo "🔧 Fixing Authentication Router on AWS Server..."

# SSH to AWS server and fix the auth router prefix
ssh -o StrictHostKeyChecking=no ubuntu@13.60.227.209 << 'EOF'
cd ~/rnr-iot
echo "📁 Current directory: $(pwd)"

echo "🔧 Fixing auth.py router prefix..."
sed -i 's/router = APIRouter(prefix="\/auth", tags=\["authentication"\])/router = APIRouter(tags=["authentication"])/' backend/api/auth.py

echo "🔄 Restarting API container..."
docker-compose restart rnr_api_server

echo "⏳ Waiting for container to start..."
sleep 10

echo "✅ Auth router fix applied and container restarted"
EOF

echo "🧪 Testing authentication endpoint..."
sleep 5

# Test the login endpoint
echo "Testing login with admin credentials..."
curl -X POST "http://13.60.227.209:3005/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n✅ Authentication fix deployment completed!"
