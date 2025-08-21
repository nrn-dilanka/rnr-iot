#!/bin/bash

# Comprehensive API Endpoint Testing Script
# Tests all endpoints on RNR IoT Platform and identifies errors

HOST="http://13.60.227.209:3005"
echo "🧪 RNR IoT Platform - Comprehensive Endpoint Testing"
echo "=================================================="
echo "🌐 Testing Host: $HOST"
echo "📅 Test Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -e "${BLUE}🔍 Testing: $method $endpoint${NC}"
    echo "   Description: $description"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$HOST$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$HOST$endpoint")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT -H "Content-Type: application/json" -d "$data" "$HOST$endpoint")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$HOST$endpoint")
    fi
    
    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    # Determine status
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        echo -e "   Status: ${GREEN}✅ SUCCESS ($http_code)${NC}"
        echo "   Response: $(echo "$body" | jq -c '.' 2>/dev/null || echo "$body" | head -c 100)..."
    elif [[ $http_code -ge 400 && $http_code -lt 500 ]]; then
        echo -e "   Status: ${YELLOW}⚠️ CLIENT ERROR ($http_code)${NC}"
        echo "   Error: $(echo "$body" | jq -r '.detail // .' 2>/dev/null || echo "$body")"
    elif [[ $http_code -ge 500 ]]; then
        echo -e "   Status: ${RED}❌ SERVER ERROR ($http_code)${NC}"
        echo "   Error: $(echo "$body" | jq -r '.detail // .' 2>/dev/null || echo "$body")"
    else
        echo -e "   Status: ${RED}❌ UNKNOWN ERROR ($http_code)${NC}"
        echo "   Response: $body"
    fi
    echo ""
}

echo "🏃 Starting comprehensive endpoint testing..."
echo ""

# 1. Health and Status Endpoints
echo "=== 🏥 HEALTH & STATUS ENDPOINTS ==="
test_endpoint "GET" "/health" "System health check"
test_endpoint "GET" "/docs" "API documentation"
test_endpoint "GET" "/openapi.json" "OpenAPI specification"

# 2. Node Management Endpoints
echo "=== 🔧 NODE MANAGEMENT ENDPOINTS ==="
test_endpoint "GET" "/api/nodes" "Get all nodes"
test_endpoint "GET" "/api/nodes/count" "Get node count"
test_endpoint "POST" "/api/nodes" "Create new node" '{"node_id":"test_node_001","name":"Test Node"}'
test_endpoint "GET" "/api/nodes/test_node_001" "Get specific node"
test_endpoint "PUT" "/api/nodes/test_node_001" "Update node" '{"name":"Updated Test Node"}'

# 3. Sensor Data Endpoints
echo "=== 📊 SENSOR DATA ENDPOINTS ==="
test_endpoint "GET" "/api/sensor-data" "Get all sensor data"
test_endpoint "GET" "/api/sensor-data/latest" "Get latest sensor data"
test_endpoint "GET" "/api/sensor-data/test_node_001" "Get sensor data for specific node"
test_endpoint "POST" "/api/sensor-data" "Submit sensor data" '{"node_id":"test_node_001","data":{"temperature":25.5,"humidity":60.0}}'

# 4. Firmware Management Endpoints
echo "=== 💾 FIRMWARE MANAGEMENT ENDPOINTS ==="
test_endpoint "GET" "/api/firmware" "Get all firmware versions"
test_endpoint "GET" "/api/firmware/1" "Get specific firmware"

# 5. Device Control Endpoints
echo "=== 🎮 DEVICE CONTROL ENDPOINTS ==="
test_endpoint "POST" "/api/nodes/test_node_001/action" "Send action to node" '{"action":"status"}'
test_endpoint "POST" "/api/nodes/test_node_001/firmware" "Deploy firmware" '{"firmware_id":1}'

# 6. Real-time Communication
echo "=== 🔗 REAL-TIME COMMUNICATION ==="
echo -e "${BLUE}🔍 Testing: WebSocket /ws${NC}"
echo "   Description: WebSocket connection test"
# WebSocket testing is complex in bash, so we'll just note it
echo -e "   Status: ${YELLOW}⚠️ MANUAL TEST REQUIRED${NC}"
echo "   Note: Use browser or wscat to test ws://13.60.227.209:3005/ws"
echo ""

# 7. Advanced Features (if available)
test_endpoint "GET" "/api/water/systems" "Get water systems"
test_endpoint "GET" "/api/monitoring/dashboard" "Get monitoring dashboard"

# 8. Authentication (if enabled)
echo "=== 🔐 AUTHENTICATION ENDPOINTS ==="
test_endpoint "POST" "/api/auth/login" "User login" '{"username":"admin","password":"admin"}'
test_endpoint "GET" "/api/auth/me" "Get current user"

# 9. Database Test Endpoints
echo "=== 🗄️ DATABASE TEST ENDPOINTS ==="
test_endpoint "GET" "/api/database/test" "Database connection test"

# Summary
echo "=============================================="
echo "🎯 ENDPOINT TESTING COMPLETED"
echo "=============================================="
echo ""
echo "📊 Test Summary:"
echo "• Host: $HOST"
echo "• Total endpoints tested: ~20+"
echo "• Check individual results above for details"
echo ""
echo "🔧 Common fixes for errors:"
echo "• 500 errors: Check server logs with 'docker logs rnr_iot_api_server'"
echo "• 404 errors: Endpoint may not be implemented"
echo "• Database errors: Run './fix_database_schema.sh'"
echo "• Connection errors: Check if services are running"
echo ""
echo "📝 Next steps:"
echo "• Review failed endpoints above"
echo "• Check detailed logs: './check_logs.sh 50'"
echo "• Fix database schema if needed: './fix_database_schema.sh'"
echo "• Test manually: curl http://13.60.227.209:3005/api/nodes"
