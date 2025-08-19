#!/bin/bash

# RNR Solutions IoT Platform - AWS Deployment Script
# Deploy the complete IoT platform with nginx proxy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_section "RNR Solutions IoT Platform Deployment"

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Verify required files exist
print_status "Verifying required files..."
required_files=("docker-compose.yml" "nginx.conf" ".env")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found!"
        exit 1
    fi
done

# Stop any existing containers
print_status "Stopping existing containers..."
docker compose down --remove-orphans || docker-compose down --remove-orphans || true

# Pull latest images
print_status "Pulling latest Docker images..."
docker compose pull || docker-compose pull

# Build custom images
print_status "Building application images..."
docker compose build --no-cache || docker-compose build --no-cache

# Install nginx configuration
print_status "Installing nginx configuration..."
# Remove default nginx site to avoid conflicts
rm -f /etc/nginx/sites-enabled/default
cp nginx.conf /etc/nginx/nginx.conf

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t
if [ $? -ne 0 ]; then
    print_error "Nginx configuration test failed!"
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p /var/log/nginx
mkdir -p ./uploads
chmod 755 ./uploads

# Start the platform
print_status "Starting RNR Solutions IoT Platform..."
docker compose up -d || docker-compose up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Check service health
print_status "Checking service health..."
services=("rnr_iot_postgres" "rnr_iot_rabbitmq" "rnr_iot_api_server" "rnr_iot_worker_service")
for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        print_status "✓ $service is running"
    else
        print_warning "✗ $service is not running"
    fi
done

# Reload nginx
print_status "Reloading nginx..."
systemctl reload nginx

# Display status
print_section "Deployment Status"

echo ""
print_status "Service URLs:"
echo "Frontend:     http://$(curl -s ifconfig.me || echo 'YOUR_IP')"
echo "API:          http://$(curl -s ifconfig.me || echo 'YOUR_IP')/api"
echo "WebSocket:    ws://$(curl -s ifconfig.me || echo 'YOUR_IP')/ws"
echo "RabbitMQ UI:  http://$(curl -s ifconfig.me || echo 'YOUR_IP')/rabbitmq"

echo ""
print_status "Internal Service Ports:"
echo "Frontend:     localhost:3000"
echo "API:          localhost:8000"
echo "PostgreSQL:   localhost:15432"
echo "RabbitMQ:     localhost:5672 (AMQP)"
echo "RabbitMQ UI:  localhost:15672"
echo "MQTT:         localhost:1883"

echo ""
print_status "Logs can be viewed with:"
echo "docker compose logs -f [service_name] OR docker-compose logs -f [service_name]"
echo "Available services: rnr_postgres, rnr_rabbitmq, rnr_api_server, rnr_worker_service"

echo ""
print_status "To stop the platform:"
echo "docker compose down OR docker-compose down"

echo ""
print_status "To update the platform:"
echo "sudo ./deploy_aws_platform.sh"

# Check if SSL is needed
echo ""
print_warning "For production deployment:"
echo "1. Configure a domain name"
echo "2. Set up SSL certificates (Let's Encrypt recommended)"
echo "3. Update nginx.conf with your domain"
echo "4. Update security groups to restrict access as needed"

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor_platform.sh << 'EOF'
#!/bin/bash

# RNR Solutions IoT Platform Monitor

echo "RNR Solutions IoT Platform Status"
echo "=================================="

# Check Docker services
echo ""
echo "Docker Services:"
docker-compose ps

# Check nginx status
echo ""
echo "Nginx Status:"
systemctl status nginx --no-pager -l

# Check disk usage
echo ""
echo "Disk Usage:"
df -h

# Check memory usage
echo ""
echo "Memory Usage:"
free -h

# Check network connections
echo ""
echo "Network Connections:"
netstat -tlnp | grep -E ':(80|443|3000|8000|5672|15672|1883|15432)'

# Check logs for errors
echo ""
echo "Recent Errors in Logs:"
journalctl -u nginx --since="1 hour ago" --no-pager | grep -i error | tail -5

echo ""
echo "For detailed logs: docker-compose logs [service_name]"
EOF

chmod +x monitor_platform.sh

print_section "Deployment Complete!"
print_status "RNR Solutions IoT Platform is now running!"
print_status "Use ./monitor_platform.sh to check system status"
