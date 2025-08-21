#!/bin/bash

# Fix Database Schema - Add Missing Columns
# This script fixes the missing is_active column in the nodes table

echo "🔧 Database Schema Fix - Missing Columns"
echo "======================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 Checking current database status...${NC}"
docker-compose ps rnr_postgres

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database container not running${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking current nodes table schema...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "\d nodes"

echo -e "${BLUE}🛠️ Applying database migration...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -f /docker-entrypoint-initdb.d/migrate_database_schema.sql

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Migration file not found in container, applying directly...${NC}"
    docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
    -- Add missing columns if they don't exist
    ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_active VARCHAR(50) DEFAULT 'true';
    ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'offline';
    
    -- Create missing indexes if needed
    CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
    CREATE INDEX IF NOT EXISTS idx_nodes_is_active ON nodes(is_active);
    
    -- Verify the schema
    \d nodes;
    "
fi

echo -e "${BLUE}🔍 Verifying fixed schema...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "\d nodes"

echo -e "${BLUE}📊 Checking data counts...${NC}"
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "
SELECT COUNT(*) as total_nodes FROM nodes;
SELECT COUNT(*) as total_sensor_data FROM sensor_data;
"

echo -e "${BLUE}🔄 Restarting API server to apply changes...${NC}"
docker-compose restart rnr_api_server

echo -e "${BLUE}⏳ Waiting for API server to restart...${NC}"
sleep 10

echo -e "${BLUE}🧪 Testing nodes endpoint...${NC}"
curl -s http://localhost:3005/api/nodes | jq '.' || echo "Testing endpoint..."

echo -e "${BLUE}📋 Checking for database errors...${NC}"
docker logs --tail=10 rnr_iot_api_server 2>&1 | grep -i "column.*does not exist"

if [ $? -ne 0 ]; then
    echo -e "${GREEN}✅ No database column errors found! Schema fix successful.${NC}"
else
    echo -e "${RED}❌ Database errors still present${NC}"
fi

echo -e "${GREEN}🎯 Database schema fix complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "• Test nodes endpoint: curl http://localhost:3005/api/nodes"
echo "• Check API logs: docker logs rnr_iot_api_server"
echo "• Monitor logs: ./check_logs.sh 20"
