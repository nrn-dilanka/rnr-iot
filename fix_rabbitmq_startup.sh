#!/bin/bash

# RNR Solutions - RabbitMQ Troubleshooting Script
# Diagnoses and fixes RabbitMQ startup issues

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

print_section "RabbitMQ Troubleshooting and Fix"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Step 1: Check current container status
print_status "Checking current RabbitMQ container status..."
if docker ps -a | grep -q "rnr_iot_rabbitmq"; then
    print_status "RabbitMQ container exists. Status:"
    docker ps -a --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    print_status "Checking container logs..."
    docker logs --tail 20 rnr_iot_rabbitmq
else
    print_warning "RabbitMQ container does not exist"
fi

# Step 2: Check configuration files
print_status "Checking RabbitMQ configuration files..."

if [ ! -f "./rabbitmq/rabbitmq.conf" ]; then
    print_error "rabbitmq.conf not found! Creating basic configuration..."
    mkdir -p ./rabbitmq
    cat > ./rabbitmq/rabbitmq.conf << 'EOF'
# RNR Solutions - Basic RabbitMQ Configuration
vm_memory_high_watermark.relative = 0.4
disk_free_limit.absolute = 50MB
channel_max = 256
connection_max = 512
heartbeat = 60
log.console.level = warning
mqtt.default_user = rnr_iot_user
mqtt.default_pass = rnr_iot_2025!
mqtt.vhost = rnr_iot_vhost
mqtt.exchange = amq.topic
mqtt.prefetch = 10
mqtt.allow_anonymous = false
EOF
    print_status "✓ Created basic rabbitmq.conf"
fi

if [ ! -f "./rabbitmq/enabled_plugins" ]; then
    print_error "enabled_plugins not found! Creating..."
    mkdir -p ./rabbitmq
    cat > ./rabbitmq/enabled_plugins << 'EOF'
[rabbitmq_mqtt,rabbitmq_management].
EOF
    print_status "✓ Created enabled_plugins file"
fi

# Step 3: Stop and clean up existing container
print_status "Stopping and cleaning up existing RabbitMQ container..."
docker compose stop rnr_rabbitmq 2>/dev/null || docker-compose stop rnr_rabbitmq 2>/dev/null || true
docker rm rnr_iot_rabbitmq 2>/dev/null || true

# Step 4: Check memory availability
AVAILABLE_MEM=$(free -m | awk '/^Mem:/{print $7}')
print_status "Available memory: ${AVAILABLE_MEM}MB"

if [ "$AVAILABLE_MEM" -lt 300 ]; then
    print_warning "Low memory detected. Reducing RabbitMQ memory limit..."
    # Create a temporary docker-compose override
    cat > docker-compose.override.yml << 'EOF'
services:
  rnr_rabbitmq:
    deploy:
      resources:
        limits:
          memory: 200M
        reservations:
          memory: 100M
EOF
    print_status "Created memory override for RabbitMQ"
fi

# Step 5: Try to start RabbitMQ with basic configuration
print_status "Starting RabbitMQ with basic configuration..."
docker compose up -d rnr_rabbitmq || docker-compose up -d rnr_rabbitmq

# Step 6: Wait and check startup
print_status "Waiting for RabbitMQ to start (this may take up to 60 seconds)..."
sleep 10

for i in {1..12}; do
    if docker ps | grep -q "rnr_iot_rabbitmq.*Up"; then
        print_status "✓ RabbitMQ container is running"
        break
    elif [ $i -eq 12 ]; then
        print_error "RabbitMQ container failed to start"
        print_status "Container logs:"
        docker logs --tail 30 rnr_iot_rabbitmq
        exit 1
    else
        print_status "Waiting... (attempt $i/12)"
        sleep 5
    fi
done

# Step 7: Check if RabbitMQ service is ready
print_status "Checking if RabbitMQ service is ready..."
for i in {1..24}; do
    if docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_status "✓ RabbitMQ service is ready and responding"
        break
    elif [ $i -eq 24 ]; then
        print_error "RabbitMQ service failed to become ready"
        print_status "Detailed container logs:"
        docker logs rnr_iot_rabbitmq
        print_status "RabbitMQ status:"
        docker exec rnr_iot_rabbitmq rabbitmq-diagnostics status || true
        exit 1
    else
        print_status "Waiting for RabbitMQ service... (attempt $i/24)"
        sleep 5
    fi
done

# Step 8: Verify MQTT plugin
print_status "Verifying MQTT plugin is loaded..."
if docker exec rnr_iot_rabbitmq rabbitmq-plugins list | grep -q "rabbitmq_mqtt.*E"; then
    print_status "✓ MQTT plugin is enabled"
else
    print_warning "MQTT plugin not enabled. Enabling..."
    docker exec rnr_iot_rabbitmq rabbitmq-plugins enable rabbitmq_mqtt
    sleep 5
fi

# Step 9: Create virtual host and user if needed
print_status "Setting up RabbitMQ user and virtual host..."
docker exec rnr_iot_rabbitmq rabbitmqctl add_vhost rnr_iot_vhost 2>/dev/null || true
docker exec rnr_iot_rabbitmq rabbitmqctl add_user rnr_iot_user rnr_iot_2025! 2>/dev/null || true
docker exec rnr_iot_rabbitmq rabbitmqctl set_user_tags rnr_iot_user administrator 2>/dev/null || true
docker exec rnr_iot_rabbitmq rabbitmqctl set_permissions -p rnr_iot_vhost rnr_iot_user ".*" ".*" ".*" 2>/dev/null || true

# Step 10: Final verification
print_section "RabbitMQ Startup Verification"

echo "Container Status:"
docker ps --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Memory Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" rnr_iot_rabbitmq

echo ""
echo "RabbitMQ Status:"
docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping

echo ""
echo "Enabled Plugins:"
docker exec rnr_iot_rabbitmq rabbitmq-plugins list | grep -E "(mqtt|management)"

print_section "RabbitMQ Successfully Started!"

print_status "Access URLs:"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
echo "Management UI: http://$PUBLIC_IP:15672"
echo "AMQP Port: $PUBLIC_IP:5672"
echo "MQTT Port: $PUBLIC_IP:1883"

echo ""
print_status "Credentials:"
echo "Username: rnr_iot_user"
echo "Password: rnr_iot_2025!"
echo "Virtual Host: rnr_iot_vhost"

echo ""
print_status "Next steps:"
echo "1. Continue with other service deployment"
echo "2. Test MQTT connection on port 1883"
echo "3. Access management UI for monitoring"

# Clean up override file if created
rm -f docker-compose.override.yml
