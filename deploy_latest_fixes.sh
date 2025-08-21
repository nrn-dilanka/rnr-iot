#!/bin/bash

# Deploy Latest Fixes to AWS - RNR IoT Platform
# This script pulls the latest code and rebuilds containers with fixes

echo "🚀 Deploying Latest Fixes to AWS"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📥 Step 1: Pulling latest code from repository...${NC}"
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to pull latest code${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Step 2: Checking current container status...${NC}"
docker-compose ps

echo -e "${BLUE}🛑 Step 3: Stopping current services...${NC}"
docker-compose down

echo -e "${BLUE}🧹 Step 4: Cleaning up old images (optional - keeps data)...${NC}"
echo "Removing old API and worker images to force rebuild..."
docker images | grep rnr-iot | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

echo -e "${BLUE}🔨 Step 5: Rebuilding services with latest code...${NC}"
docker-compose build --no-cache rnr_api_server rnr_worker_service

echo -e "${BLUE}🚀 Step 6: Starting services with health checks...${NC}"
docker-compose up -d

echo -e "${BLUE}⏳ Step 7: Waiting for services to become healthy...${NC}"
echo "Waiting for health checks to pass..."
sleep 30

echo -e "${BLUE}🔍 Step 8: Checking service health...${NC}"
docker-compose ps

echo -e "${BLUE}📊 Step 9: Quick health check...${NC}"
echo "Testing API endpoint..."
curl -s http://localhost:3005/health | jq '.' || echo "API not responding yet"

echo -e "${BLUE}📋 Step 10: Checking logs for errors...${NC}"
echo "Checking for SQLAlchemy text() errors..."
docker logs rnr_iot_api_server 2>&1 | grep -i "text.*should be explicitly declared" | tail -5

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Quick Status Check:${NC}"
echo "• API Health: curl http://localhost:3005/health"
echo "• API Docs: http://your-server-ip:3005/docs"
echo "• View logs: ./check_logs.sh 50"
echo "• Monitor: ./monitor_all_logs.sh"
echo ""
echo -e "${YELLOW}🔧 If issues persist:${NC}"
echo "• Check logs: docker logs rnr_iot_api_server"
echo "• Restart API: docker-compose restart rnr_api_server"
echo "• Full restart: docker-compose down && docker-compose up -d"
