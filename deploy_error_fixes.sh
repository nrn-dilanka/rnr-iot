#!/bin/bash

echo "🔧 COMPREHENSIVE ERROR FIX DEPLOYMENT"
echo "====================================="

# Stop all services
echo "🛑 Stopping all services..."
docker-compose down

# Clean up old logs and data (optional - be careful!)
echo "🧹 Cleaning up old logs..."
docker system prune -f

# Rebuild with no cache to ensure all fixes are applied
echo "📦 Rebuilding all services with fixes..."
docker-compose build --no-cache

# Start services in order
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 20

# Test all fixes
echo "🧪 Testing fixes..."

echo "1. Database Connection Test:"
curl -s "http://localhost:3005/api/database/test" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    status = data.get('database_status', 'unknown')
    print(f'   Database Status: {status}')
    if status == 'connected':
        print('   ✅ Database connection fixed')
    else:
        print(f'   ❌ Database issue: {data.get(\"error\", \"unknown\")}')
except Exception as e:
    print(f'   ❌ Test failed: {e}')
"

echo -e "\n2. Health Check Test:"
curl -s "http://localhost:3005/health" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    db_status = data.get('database', 'unknown')
    print(f'   Health Status: {data.get(\"status\", \"unknown\")}')
    print(f'   Database: {db_status}')
    if db_status == 'connected':
        print('   ✅ Health check database connection fixed')
except Exception as e:
    print(f'   ❌ Health check failed: {e}')
"

echo -e "\n3. MQTT Connection Status:"
docker logs rnr_iot_api_server --tail=10 | grep -i "mqtt\|ESP32" | tail -3

echo -e "\n4. RabbitMQ Service Status:"
docker logs rnr_iot_rabbitmq --tail=5 | grep -E "started|ready" | tail -2

echo -e "\n5. Container Health Status:"
docker-compose ps

echo -e "\n🎯 Error fix deployment complete!"
echo ""
echo "📋 Summary of fixes applied:"
echo "• Enhanced MQTT connection with retry logic and timeout handling"
echo "• Fixed database SQL text() declarations to remove warnings"
echo "• Improved error handling in ESP32 device manager"
echo "• Added proper MQTT error code explanations"
echo "• Enhanced database connectivity testing"
echo ""
echo "🔍 Monitor logs with: ./check_logs.sh"
echo "🚨 Check for remaining errors: ./analyze_errors.sh"
