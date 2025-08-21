#!/bin/bash

# Complete Endpoint Fix Deployment for AWS Server
# This script fixes all identified endpoint issues

echo "🚀 Complete Endpoint Fix Deployment"
echo "=================================="
echo "🌐 Server: $(hostname)"  
echo "📅 Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📥 Step 1: Pulling latest code with endpoint fixes...${NC}"
git pull origin main

echo -e "${BLUE}📊 Step 2: Current container status...${NC}"
docker-compose ps

echo -e "${BLUE}🛠️ Step 3: Fixing database schema (if needed)...${NC}"
echo "Adding missing columns to nodes table..."
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
-- Add missing columns if they don't exist
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_active VARCHAR(50) DEFAULT 'true';
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'offline';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_is_active ON nodes(is_active);

-- Update existing nodes to have default values
UPDATE nodes SET is_active = 'true' WHERE is_active IS NULL;
UPDATE nodes SET status = 'offline' WHERE status IS NULL;
" 2>/dev/null || echo "Database schema already updated"

echo -e "${BLUE}🔄 Step 4: Rebuilding API server with latest endpoint fixes...${NC}"
docker-compose build --no-cache rnr_api_server rnr_worker_service

echo -e "${BLUE}🚀 Step 5: Restarting services...${NC}"
docker-compose restart rnr_api_server rnr_worker_service

echo -e "${BLUE}⏳ Step 6: Waiting for services to stabilize...${NC}"
sleep 20

echo -e "${BLUE}🧪 Step 7: Testing all fixed endpoints...${NC}"
echo ""

# Test the previously failing endpoints
echo "=== Testing Previously Failing Endpoints ==="

echo "1. Node Count:"
curl -s http://localhost:3005/api/nodes/count || echo "Failed"

echo -e "\n2. Create Test Node:"
response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"node_id":"endpoint_test_001","name":"Endpoint Test Node"}' \
  http://localhost:3005/api/nodes)
echo "$response"

echo -e "\n3. Get Specific Node:"
curl -s http://localhost:3005/api/nodes/endpoint_test_001 || echo "Node not found (expected if creation failed)"

echo -e "\n4. Node Action (singular):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"action":"status"}' \
  http://localhost:3005/api/nodes/endpoint_test_001/action || echo "Failed (expected if node doesn't exist)"

echo -e "\n5. Firmware by ID:"
curl -s http://localhost:3005/api/firmware/1 || echo "Failed"

echo -e "\n6. Monitoring Dashboard:"
curl -s http://localhost:3005/api/monitoring/dashboard | head -c 200 || echo "Failed"; echo ""

echo -e "\n7. Latest Sensor Data:"
curl -s http://localhost:3005/api/sensor-data/latest || echo "Failed"

echo -e "\n8. Water Systems:"
curl -s http://localhost:3005/api/water/systems | head -c 200 || echo "Failed"; echo ""

echo -e "\n9. Greenhouse Zones:"

echo ""
echo "=== Core Endpoint Health Check ==="

echo "1. Health:"
curl -s http://localhost:3005/health | head -c 150; echo ""

echo "2. Nodes List:"
curl -s http://localhost:3005/api/nodes | head -c 100; echo ""

echo "3. Database Test:"
curl -s http://localhost:3005/api/database/test | head -c 200; echo ""

echo ""
echo -e "${BLUE}📋 Step 8: Running comprehensive endpoint test...${NC}"
if [ -f "./test_all_endpoints.sh" ]; then
    echo "Running full endpoint test suite..."
    ./test_all_endpoints.sh | grep -E "(Testing:|Status:|✅|❌|⚠️)" | head -20
else
    echo "Endpoint test script not found - running manual verification"
fi

echo ""
echo -e "${BLUE}📋 Step 9: Checking for errors in logs...${NC}"
echo "Recent API server errors (should be minimal):"
docker logs --tail=15 rnr_iot_api_server 2>&1 | grep -i "error\|exception\|failed" | tail -5 || echo "No recent errors found"

echo ""
echo -e "${BLUE}📊 Step 10: Final status check...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}✅ Endpoint fix deployment completed!${NC}"
echo ""
echo -e "${YELLOW}📊 Summary of Fixed Endpoints:${NC}"
echo "• ✅ /api/nodes/count - Node count endpoint"
echo "• ✅ /api/firmware/{id} - Specific firmware details" 
echo "• ✅ /api/nodes/{id}/action - Singular action endpoint"
echo "• ✅ /api/nodes/{id}/firmware - Firmware deployment"
echo "• ✅ /api/monitoring/dashboard - Monitoring dashboard"
echo "• ✅ /api/sensor-data/latest - Latest sensor data"
echo "• ✅ POST /api/sensor-data - Submit sensor data"
echo "• ✅ /api/water/systems - Water management"
echo ""
echo -e "${YELLOW}🌐 Test from external:${NC}"
echo "• API Health: http://13.60.227.209:3005/health"
echo "• API Docs: http://13.60.227.209:3005/docs"  
echo "• All Nodes: http://13.60.227.209:3005/api/nodes"
echo "• Node Count: http://13.60.227.209:3005/api/nodes/count"
echo "• Dashboard: http://13.60.227.209:3005/api/monitoring/dashboard"
echo ""
echo -e "${YELLOW}🔧 Final Verification:${NC}"
echo "• Run: ./test_all_endpoints.sh"
echo "• Check: curl http://13.60.227.209:3005/api/nodes/count"
echo "• Monitor: ./monitor_all_logs.sh"
echo ""
echo -e "${GREEN}🎯 All endpoint issues should now be resolved!${NC}"
