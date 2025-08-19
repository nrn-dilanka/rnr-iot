#!/bin/bash

# RNR Solutions - RabbitMQ Configuration Fix Script
# Fixes deprecated environment variable warnings

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

print_section "RabbitMQ Configuration Fix"

print_status "Stopping RabbitMQ container..."
docker compose stop rnr_rabbitmq || docker-compose stop rnr_rabbitmq

print_status "Removing old RabbitMQ container..."
docker rm rnr_iot_rabbitmq || true

print_status "Starting RabbitMQ with new configuration..."
docker compose up -d rnr_rabbitmq || docker-compose up -d rnr_rabbitmq

print_status "Waiting for RabbitMQ to start..."
sleep 15

# Check if RabbitMQ started successfully
if docker ps | grep -q "rnr_iot_rabbitmq"; then
    print_status "✓ RabbitMQ container is running"
else
    print_error "✗ RabbitMQ failed to start"
    exit 1
fi

# Wait for RabbitMQ to be ready
print_status "Waiting for RabbitMQ to be ready..."
for i in {1..30}; do
    if docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_status "✓ RabbitMQ is ready and responding"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "RabbitMQ failed to become ready"
        exit 1
    fi
    sleep 2
done

# Check for deprecation warnings
print_status "Checking for deprecation warnings..."
sleep 5

WARNINGS=$(docker logs rnr_iot_rabbitmq 2>&1 | grep -i "deprecated" | wc -l)

if [ "$WARNINGS" -eq 0 ]; then
    print_status "✓ No deprecation warnings found!"
    print_status "RabbitMQ configuration has been successfully fixed"
else
    print_warning "Still found $WARNINGS deprecation warnings"
    print_status "Showing recent RabbitMQ logs:"
    docker logs --tail 20 rnr_iot_rabbitmq
fi

# Show RabbitMQ status
print_section "RabbitMQ Status"

echo "Container Status:"
docker ps --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Memory Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" rnr_iot_rabbitmq

echo ""
print_status "RabbitMQ Management UI: http://your-server-ip:15672"
print_status "Username: rnr_iot_user"
print_status "Password: rnr_iot_2025!"

echo ""
print_status "To view RabbitMQ logs: docker logs rnr_iot_rabbitmq"
print_status "To restart other services: docker compose restart [service_name]"
