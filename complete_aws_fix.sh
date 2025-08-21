#!/bin/bash

# Complete AWS Server Fix Script
# Fixes all identified issues from endpoint testing

echo "🚀 Complete AWS Server Fix - RNR IoT Platform"
echo "============================================="
echo "🌐 Server: $(hostname)"
echo "📅 Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📥 Step 1: Pulling latest code...${NC}"
git pull origin main

echo -e "${BLUE}📊 Step 2: Current container status...${NC}"
docker-compose ps

echo -e "${BLUE}🛠️ Step 3: Fixing database schema...${NC}"
echo "Adding missing columns to nodes table..."
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
-- Add missing columns
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_active VARCHAR(50) DEFAULT 'true';
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'offline';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_is_active ON nodes(is_active);

-- Update existing nodes to have default values
UPDATE nodes SET is_active = 'true' WHERE is_active IS NULL;
UPDATE nodes SET status = 'offline' WHERE status IS NULL;
"

echo -e "${BLUE}🔄 Step 4: Rebuilding API server with latest code...${NC}"
docker-compose build --no-cache rnr_api_server

echo -e "${BLUE}🚀 Step 5: Restarting services...${NC}"
docker-compose restart rnr_api_server rnr_worker_service

echo -e "${BLUE}⏳ Step 6: Waiting for services to stabilize...${NC}"
sleep 20

echo -e "${BLUE}🧪 Step 7: Running comprehensive tests...${NC}"
echo ""

# Test core endpoints
echo "=== Core Endpoint Tests ==="
echo "1. Health Check:"
curl -s http://localhost:3005/health | head -c 150; echo ""

echo "2. Database Test:"
curl -s http://localhost:3005/api/database/test | head -c 200; echo ""

echo "3. Nodes List:"
curl -s http://localhost:3005/api/nodes; echo ""

echo "4. Node Count:"
curl -s http://localhost:3005/api/nodes/count; echo ""

echo "5. Firmware List:"
curl -s http://localhost:3005/api/firmware | head -c 200; echo ""

echo "6. Sensor Data:"
curl -s http://localhost:3005/api/sensor-data; echo ""

echo ""
echo "=== Node Creation Test ==="
echo "Creating test node..."
response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"node_id":"test_aws_001","name":"AWS Test Node"}' \
  http://localhost:3005/api/nodes)
echo "Response: $response"

echo ""
echo "Checking if node was created..."
curl -s http://localhost:3005/api/nodes; echo ""

echo ""
echo "=== Node Operations Test ==="
echo "Getting specific node..."
curl -s http://localhost:3005/api/nodes/test_aws_001; echo ""

echo ""
echo "Updating node..."
curl -s -X PUT -H "Content-Type: application/json" \
  -d '{"name":"Updated AWS Test Node"}' \
  http://localhost:3005/api/nodes/test_aws_001; echo ""

echo ""
echo "=== Sensor Data Test ==="
echo "Submitting test sensor data..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"node_id":"test_aws_001","data":{"temperature":25.5,"humidity":60.0,"timestamp":"2025-08-21T12:00:00Z"}}' \
  http://localhost:3005/api/sensor-data; echo ""

echo ""
echo -e "${BLUE}📋 Step 8: Checking for errors in logs...${NC}"
echo "Recent API server errors:"
docker logs --tail=20 rnr_iot_api_server 2>&1 | grep -i "error\|exception\|failed" | tail -10

echo ""
echo -e "${BLUE}📊 Step 9: Final status check...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}✅ Complete AWS fix finished!${NC}"
echo ""
echo -e "${YELLOW}📊 Test Results Summary:${NC}"
echo "• Check the responses above for endpoint status"
echo "• Look for any error messages in the logs section"
echo "• Verify that containers are running healthy"
echo ""
echo -e "${YELLOW}🌐 External Testing:${NC}"
echo "Test from your browser or external client:"
echo "• Health: http://13.60.227.209:3005/health"
echo "• API Docs: http://13.60.227.209:3005/docs"
echo "• Nodes: http://13.60.227.209:3005/api/nodes"
echo ""
echo -e "${YELLOW}🔧 If issues remain:${NC}"
echo "• Run endpoint tests: ./test_all_endpoints.sh"
echo "• Check detailed logs: ./check_logs.sh 50"
echo "• Monitor real-time: ./monitor_all_logs.sh"
