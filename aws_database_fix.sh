#!/bin/bash

# AWS Server Database Fix Script
# Run this on your AWS server to fix database schema issues

echo "🔧 AWS Database Schema Fix"
echo "=========================="
echo "🌐 Server: $(hostname)"
echo "📅 Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're on AWS server
if [[ ! "$(hostname)" =~ "ip-" ]]; then
    echo -e "${YELLOW}⚠️ This script is designed for AWS servers${NC}"
    echo "Current hostname: $(hostname)"
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${BLUE}📊 Step 1: Checking container status...${NC}"
docker-compose ps

echo -e "${BLUE}🔍 Step 2: Testing current database issue...${NC}"
curl -s http://localhost:3005/api/database/test | head -c 200
echo ""

echo -e "${BLUE}🛠️ Step 3: Applying database schema fix...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
-- Add missing columns if they don't exist
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_active VARCHAR(50) DEFAULT 'true';
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'offline';

-- Create missing indexes if needed
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_is_active ON nodes(is_active);

-- Show current schema
\d nodes;
"

echo -e "${BLUE}📊 Step 4: Verifying schema fix...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'nodes' 
ORDER BY ordinal_position;
"

echo -e "${BLUE}🔄 Step 5: Restarting API server...${NC}"
docker-compose restart rnr_api_server

echo -e "${BLUE}⏳ Step 6: Waiting for restart...${NC}"
sleep 15

echo -e "${BLUE}🧪 Step 7: Testing database connection...${NC}"
curl -s http://localhost:3005/api/database/test | head -c 300
echo ""

echo -e "${BLUE}🧪 Step 8: Testing nodes endpoint...${NC}"
curl -s http://localhost:3005/api/nodes
echo ""

echo -e "${BLUE}🧪 Step 9: Testing node creation...${NC}"
curl -s -X POST -H "Content-Type: application/json" -d '{"node_id":"aws_test_001","name":"AWS Test Node"}' http://localhost:3005/api/nodes
echo ""

echo -e "${BLUE}🧪 Step 10: Checking if test node was created...${NC}"
curl -s http://localhost:3005/api/nodes
echo ""

echo -e "${BLUE}📋 Step 11: Checking logs for errors...${NC}"
docker logs --tail=10 rnr_iot_api_server 2>&1 | grep -i "error\|exception" | tail -5

echo ""
echo -e "${GREEN}✅ Database schema fix completed!${NC}"
echo ""
echo -e "${YELLOW}📊 Verification Results:${NC}"
echo "• Database schema: Check output above"
echo "• Nodes endpoint: Should return array (empty or with test node)"
echo "• API health: curl http://localhost:3005/health"
echo ""
echo -e "${YELLOW}🔧 If issues persist:${NC}"
echo "• Check logs: docker logs rnr_iot_api_server"
echo "• Restart all: docker-compose down && docker-compose up -d"
echo "• Test again: curl http://localhost:3005/api/nodes"
echo ""
echo -e "${BLUE}🌐 Test from external:${NC}"
echo "curl http://13.60.227.209:3005/api/nodes"
