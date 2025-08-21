#!/bin/bash

# Quick Fix for SQLAlchemy text() Errors
# This script rebuilds only the API server with the latest fixes

echo "🔧 Quick Fix: SQLAlchemy text() Errors"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📥 Pulling latest code...${NC}"
git pull origin main

echo -e "${BLUE}🛑 Stopping API server...${NC}"
docker-compose stop rnr_api_server

echo -e "${BLUE}🔨 Rebuilding API server with fixes...${NC}"
docker-compose build --no-cache rnr_api_server

echo -e "${BLUE}🚀 Starting API server...${NC}"
docker-compose up -d rnr_api_server

echo -e "${BLUE}⏳ Waiting for startup...${NC}"
sleep 15

echo -e "${BLUE}🔍 Testing for text() errors...${NC}"
echo "Checking recent logs for SQLAlchemy text() warnings..."
docker logs --tail=20 rnr_iot_api_server 2>&1 | grep -i "text.*should be explicitly declared"

if [ $? -ne 0 ]; then
    echo -e "${GREEN}✅ No text() errors found! Fix successful.${NC}"
else
    echo -e "${RED}❌ text() errors still present${NC}"
    echo "Recent API logs:"
    docker logs --tail=10 rnr_iot_api_server
fi

echo -e "${BLUE}📊 Current status:${NC}"
docker-compose ps rnr_api_server

echo -e "${GREEN}🎯 Quick fix complete!${NC}"
