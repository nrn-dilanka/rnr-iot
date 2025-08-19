#!/bin/bash

# RNR Solutions IoT Platform - Low Memory Deployment Script
# Optimized for EC2 instances with 2GB RAM or less

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_section "RNR Solutions IoT Platform - Low Memory Deployment"

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check available memory
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
AVAILABLE_MEM=$(free -m | awk '/^Mem:/{print $7}')

print_status "System Memory Status:"
echo "Total Memory: ${TOTAL_MEM}MB"
echo "Available Memory: ${AVAILABLE_MEM}MB"

if [ "$TOTAL_MEM" -lt 1800 ]; then
    print_error "This system has less than 1.8GB RAM. The platform may not run properly."
    print_warning "Consider upgrading to at least t3.small (2GB RAM) or larger"
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Configure system for low memory usage
print_status "Configuring system for low memory usage..."

# Configure swap if not already present
if [ ! -f /swapfile ]; then
    print_status "Creating 1GB swap file..."
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    print_status "Swap file created and enabled"
fi

# Optimize kernel memory settings for containers
cat > /etc/sysctl.d/99-docker-memory.conf << 'EOF'
# Docker memory optimizations for 2GB systems
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.overcommit_memory=1
net.core.somaxconn=65535
EOF

sysctl -p /etc/sysctl.d/99-docker-memory.conf

# Stop any existing containers
print_status "Stopping existing containers..."
docker compose down --remove-orphans || docker-compose down --remove-orphans || true

# Clean up unused Docker resources
print_status "Cleaning up Docker resources..."
docker system prune -f || true
docker volume prune -f || true

# Pull images one by one to avoid memory spikes
print_status "Pulling base images (one at a time to manage memory)..."
docker pull postgres:15-alpine
sleep 2
docker pull rabbitmq:3-management-alpine
sleep 2

# Build images with memory limits
print_status "Building application images with memory constraints..."
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Build backend with memory limit
docker compose build --memory=512m rnr_api_server || docker-compose build rnr_api_server
sleep 5

# Build worker with memory limit
docker compose build --memory=512m rnr_worker_service || docker-compose build rnr_worker_service
sleep 5

# Build frontend with memory limit
docker compose build --memory=512m rnr_frontend || docker-compose build rnr_frontend
sleep 5

# Install nginx configuration
print_status "Installing nginx configuration..."
cp nginx.conf /etc/nginx/nginx.conf

# Test nginx configuration
nginx -t
if [ $? -ne 0 ]; then
    print_error "Nginx configuration test failed!"
    exit 1
fi

# Start services in order with delays to prevent memory spikes
print_status "Starting services sequentially..."

# Start database first
print_status "Starting PostgreSQL..."
docker compose up -d rnr_postgres || docker-compose up -d rnr_postgres
sleep 10

# Check database is ready
print_status "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec rnr_iot_postgres pg_isready -U rnr_iot_user -d rnr_iot_platform > /dev/null 2>&1; then
        print_status "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start"
        exit 1
    fi
    sleep 2
done

# Start RabbitMQ
print_status "Starting RabbitMQ with optimized configuration..."
docker compose up -d rnr_rabbitmq || docker-compose up -d rnr_rabbitmq
sleep 15

# Check RabbitMQ is ready
print_status "Waiting for RabbitMQ to be ready..."
for i in {1..30}; do
    if docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_status "RabbitMQ is ready"
        
        # Check for deprecation warnings
        WARNINGS=$(docker logs rnr_iot_rabbitmq 2>&1 | grep -i "deprecated" | wc -l || echo "0")
        if [ "$WARNINGS" -eq 0 ]; then
            print_status "✓ RabbitMQ started without deprecation warnings"
        else
            print_warning "RabbitMQ has some warnings (this is normal on first start)"
        fi
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "RabbitMQ failed to start"
        exit 1
    fi
    sleep 2
done

# Start worker service
print_status "Starting Worker Service..."
docker compose up -d rnr_worker_service || docker-compose up -d rnr_worker_service
sleep 10

# Start API server
print_status "Starting API Server..."
docker compose up -d rnr_api_server || docker-compose up -d rnr_api_server
sleep 10

# Start frontend
print_status "Starting Frontend..."
docker compose up -d rnr_frontend || docker-compose up -d rnr_frontend
sleep 10

# Reload nginx
print_status "Reloading nginx..."
systemctl reload nginx

# Check service health
print_status "Checking service health..."
sleep 10

services=("rnr_iot_postgres" "rnr_iot_rabbitmq" "rnr_iot_api_server" "rnr_iot_worker_service" "rnr_iot_frontend")
all_healthy=true

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | grep -q "Up"; then
        print_status "✓ $service is running"
    else
        print_error "✗ $service is not running properly"
        all_healthy=false
    fi
done

# Show memory usage
print_section "Current Memory Usage"
echo "System Memory:"
free -h

echo ""
echo "Docker Container Memory Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Display status
print_section "Low Memory Deployment Status"

if [ "$all_healthy" = true ]; then
    print_status "🎉 All services are running successfully!"
else
    print_warning "Some services may need more time to start. Check logs with:"
    echo "docker compose logs [service_name]"
fi

echo ""
print_status "Service URLs:"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_EC2_IP")
echo "Frontend:     http://$PUBLIC_IP"
echo "API:          http://$PUBLIC_IP/api"
echo "WebSocket:    ws://$PUBLIC_IP/ws"

echo ""
print_warning "Memory Optimization Tips:"
echo "1. Monitor memory usage with: ./monitor_platform.sh"
echo "2. If services crash, restart one by one with delays"
echo "3. Consider upgrading to t3.small or larger for better performance"
echo "4. Use 'docker compose restart [service]' to restart individual services"

echo ""
print_status "To monitor the platform:"
echo "./monitor_platform.sh"

# Create memory monitoring script
cat > monitor_memory.sh << 'EOF'
#!/bin/bash

echo "=== RNR Solutions IoT Platform Memory Monitor ==="
echo "System Memory:"
free -h
echo ""
echo "Swap Usage:"
swapon --show
echo ""
echo "Docker Container Stats:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}"
echo ""
echo "Top Memory Consuming Processes:"
ps aux --sort=-%mem | head -10
EOF

chmod +x monitor_memory.sh

print_section "Low Memory Deployment Complete!"
print_status "Use ./monitor_memory.sh to track memory usage"
